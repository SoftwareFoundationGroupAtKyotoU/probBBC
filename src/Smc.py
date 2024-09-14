import logging

import numpy as np
from scipy import stats
from typing import Tuple, List
from aalpy.learning_algs.stochastic.SamplingBasedObservationTable import (
    SamplingBasedObservationTable,
)

from aalpy.base import SUL
import spot
import buddy

from StrategyBridge import StrategyBridge


class StatisticalModelChecker:
    def __init__(
        self,
        mdp_sut: SUL,
        strategy_bridge: StrategyBridge,
        spec_path,
        sut_value,
        observation_table,
        num_exec=1000,
        max_exec_len=40,
        returnCEX=False,
    ):
        self.log = logging.getLogger("StatisticalModelChecker")
        self.sut = mdp_sut
        self.strategy_bridge = strategy_bridge
        self.sut_value = sut_value
        self.observation_table: SamplingBasedObservationTable = observation_table
        with open(spec_path) as f:
            spec = f.readline()
        self.spec_monitor = spot.translate(spec, "monitor", "det")
        self.bdict = self.spec_monitor.get_dict()
        self.spec_monitor_out = []
        for s in range(0, self.spec_monitor.num_states()):
            self.spec_monitor_out.append(self.spec_monitor.out(s))
        self.ap_varnum = dict()
        for ap in self.spec_monitor.ap():
            var = self.bdict.varnum(ap)
            self.ap_varnum[ap.to_str()] = (
                buddy.bdd_ithvar(var),
                buddy.bdd_nithvar(var),
            )
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
                (monitor_ret, satisfied) = self.step_monitor(self.current_output_aps)
                if not monitor_ret:
                    self.exec_count_violation += 1
                    break
                if satisfied and not self.returnCEX:
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
                consistency_violation = (
                    self.observation_table.get_consistency_violation()
                )
                # Observation tableがclosedかつconsistentでなくなったときはSMCを早期終了
                if row_to_close or consistency_violation:
                    return -1

            if (k + 1) % 1000 == 0:
                self.log.info(f"SUT executed {k} times")

        return None

    def hypothesis_testing(self, mean, alternative):
        sample = np.concatenate(
            (
                np.zeros(self.exec_count_violation),
                np.ones(self.exec_count_satisfication),
            )
        )
        return stats.ttest_1samp(sample, mean, alternative=alternative)

    def reset_sut(self):
        self.number_of_steps = 0
        # XXX: Temporary fix for integration test. Need to be checked.
        self.sut.pre()
        self.current_output = self.sut.step(None)
        self.current_output_aps = self.current_output.split("__")
        self.strategy_bridge.reset()
        self.exec_trace = []
        self.monitor_current_state = self.spec_monitor.get_init_state_number()

    def one_step(self):
        self.number_of_steps += 1

        # strategyから次のアクションを決め、SULを実行する
        action = self.strategy_bridge.next_action()
        self.current_output = self.sut.step(action)
        self.current_output_aps = self.current_output.split("__")
        # 実行列を保存
        self.exec_trace.append(action)
        self.exec_trace.append(self.current_output)

        # Hypothesis側で入出力に対応する遷移を行う
        ret = self.strategy_bridge.update_state(action, self.current_output_aps)
        if not ret:
            # Hypothesisで遷移できない出力を観測した
            pass
        return ret

    def post_sut(self):
        self.sut.post()

    # 出力outputにより、モニターの状態遷移を行う。
    # 返り値はモニターの状態遷移が行われたか否かと条件が常に成立する状態に到達したか否か。モニターの状態遷移が行えないことは、仕様の違反を意味する。
    def step_monitor(self, output_aps: List[str]) -> Tuple[bool, bool]:
        # モニターの遷移ラベルのガードと、システムの出力を比較する
        edges = self.spec_monitor_out[self.monitor_current_state]
        accept = False
        satisfied_ret = False
        for e in edges:
            (next_state, satisfied) = self.guardCheck(output_aps, e)
            if not next_state:
                continue
            else:
                accept = True
                self.monitor_current_state = next_state
                satisfied_ret = satisfied
                break
        return (accept, satisfied_ret)

    # 出力outputと、モニターのedgeを受け取り、edgeの条件をoutputが満たしているか判定する
    # 返り値はペアで、一つ目は条件を満たしていてedgeで遷移できるならば遷移先の状態を返し、遷移できないならばNoneを返す
    # 二つ目はセルフループしか存在しない状態に到達したか否か（以降は条件が常に成立するか否か）
    def guardCheck(self, output_aps: List[str], edge):
        cond = edge.cond
        # label = spot.bdd_format_formula(self.bdict, cond)
        # # print(f'output: {output}')
        # # print(f'label : {label}')
        neg_cond = buddy.bdd_not(cond)
        if buddy.bdd_satcount(neg_cond) == 0 and edge.src == edge.dst:
            # 条件が常に成立
            return (edge.dst, True)
        aps_bdd = buddy.bdd_support(cond)
        aps = spot.bdd_format_formula(self.bdict, aps_bdd).split(" & ")
        for ap in aps:
            if ap in output_aps:
                bdd_var = self.ap_varnum[ap][0]
                cond = buddy.bdd_restrict(cond, bdd_var)
            else:
                bdd_var = self.ap_varnum[ap][1]
                cond = buddy.bdd_restrict(cond, bdd_var)
        # restricted_label = spot.bdd_format_formula(self.bdict, cond)
        # print(f'cond  : {restricted_label}')
        ret = buddy.bdd_satcount(cond)
        if ret > 0:
            return (edge.dst, False)
        else:
            return (None, False)
