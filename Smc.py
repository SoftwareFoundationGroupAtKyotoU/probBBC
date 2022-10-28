import numpy as np
from scipy import stats
from aalpy.learning_algs.stochastic.SamplingBasedObservationTable import SamplingBasedObservationTable

from aalpy.base import SUL
import spot
import buddy

from StrategyBridge import StrategyBridge


class StatisticalModelChecker:
    def __init__(self, mdp_sut : SUL, strategy_bridge : StrategyBridge, spec_path, sut_value, observation_table, num_exec=1000, max_exec_len=40, returnCEX=False):
        self.sut = mdp_sut
        self.strategy_bridge = strategy_bridge
        self.sut_value = sut_value
        self.observation_table : SamplingBasedObservationTable = observation_table
        with open(spec_path) as f:
            spec = f.readline()
        self.spec_monitor = spot.translate(spec, 'monitor', 'det')
        self.bdict = self.spec_monitor.get_dict()
        self.num_exec = num_exec
        self.max_exec_len = max_exec_len
        self.returnCEX = returnCEX
        self.exec_sample = []
        self.satisfied_exec_sample = []
        self.exec_count_satisfication = 0
        self.exec_count_violation = 0

    def run(self):
        for k in range(0, self.num_exec):
            self.reset_sut()
            for i in range(0, self.max_exec_len):
                ret = self.one_step()
                # Hypothesisで遷移できないような入出力列が見つかれば、SMCを終了
                if not ret and self.returnCEX:
                    return self.exec_trace
                monitor_ret = self.step_monitor(self.current_output)
                if not monitor_ret:
                    self.exec_count_violation += 1
                    break
            self.post_sut()
            if monitor_ret:
                self.exec_count_satisfication += 1
                self.satisfied_exec_sample.append(self.exec_trace)
            self.exec_sample.append(self.exec_trace)

            if (k + 1) % 500 == 0 and self.observation_table:
                # Observation tableの更新
                self.observation_table.update_obs_table_with_freq_obs()
                # Closedness, Consistencyの判定
                row_to_close = self.observation_table.get_row_to_close()
                consistency_violation = self.observation_table.get_consistency_violation()
                # Observation tableがclosedかつconsistentでなくなったときはSMCを早期終了
                if row_to_close or consistency_violation:
                    return -1

            if (k + 1) % 1000 == 0:
                print(f'SUT executed {k} times')

        return None

    def hypothesis_testing(self, mean, alternative):
        sample = np.concatenate((np.zeros(self.exec_count_violation), np.ones(self.exec_count_satisfication)))
        return stats.ttest_1samp(sample, mean, alternative=alternative)

    def reset_sut(self):
        self.number_of_steps = 0
        self.current_output = self.sut.pre()
        self.strategy_bridge.reset()
        self.exec_trace = []
        self.monitor_current_state = self.spec_monitor.get_init_state_number()

    def one_step(self):
        self.number_of_steps += 1

        # strategyから次のアクションを決め、SULを実行する
        action = self.strategy_bridge.next_action()
        self.current_output = self.sut.step(action)
        # 実行列を保存
        self.exec_trace.append(action)
        self.exec_trace.append(self.current_output)

        # Hypothesis側で入出力に対応する遷移を行う
        ret = self.strategy_bridge.update_state(action, self.current_output)
        if not ret:
            # Hypothesisで遷移できない出力を観測した
            pass
        return ret

    def post_sut(self):
        self.sut.post()

    # 出力outputにより、モニターの状態遷移を行う。
    # 返り値はモニターの状態遷移が行われたか否か。モニターの状態遷移が行えないことは、仕様の違反を意味する。
    def step_monitor(self, output : str) -> bool:
        # モニターの遷移ラベルのガードと、システムの出力を比較する
        edges = self.spec_monitor.out(self.monitor_current_state)
        accept = False
        for e in edges:
            next_state = self.guardCheck(output, e)
            if not next_state:
                continue
            else:
                accept = True
                self.monitor_current_state = next_state
                break
        return accept

    # 出力outputと、モニターのedgeを受け取り、edgeの条件をoutputが満たしているか判定する
    # 条件を満たしていてedgeで遷移できるならば遷移先の状態を返し、遷移できないならばNoneを返す
    def guardCheck(self, output : str, edge):
        cond = edge.cond
        label = spot.bdd_format_formula(self.bdict, cond)
        # print(f'output: {output}')
        # print(f'label : {label}')
        if (label == '1'):
            # 条件が常に成立
            return edge.dst
        aps_bdd = buddy.bdd_support(cond)
        aps = spot.bdd_format_formula(self.bdict, aps_bdd).split(' & ')
        obsv_aps = output.split('__')
        for ap in aps:
            if (ap in obsv_aps):
                f = spot.formula_ap(ap)
                var = self.bdict.varnum(f)
                cond = buddy.bdd_restrict(cond, buddy.bdd_ithvar(var))
            else:
                f = spot.formula_ap(ap)
                var = self.bdict.varnum(f)
                cond = buddy.bdd_restrict(cond, buddy.bdd_nithvar(var))
        # restricted_label = spot.bdd_format_formula(self.bdict, cond)
        # print(f'cond  : {restricted_label}')
        ret = buddy.bdd_satcount(cond)
        if (ret > 0):
            return edge.dst
        else:
            return None
