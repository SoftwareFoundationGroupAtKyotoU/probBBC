import numpy as np
from scipy import stats
import random
import argparse
import re
from typing import Tuple, List

from aalpy.base import SUL
from aalpy.SULs import MdpSUL
from aalpy.utils import load_automaton_from_file
import spot
import buddy

class StatisticalModelChecker:
    def __init__(self, mdp_sut : SUL, actions, spec_path, num_exec=1000, max_exec_len=40):
        self.sut = mdp_sut
        self.actions = actions
        self.exec_trace = []
        with open(spec_path) as f:
            spec = f.readline()
        self.spec_monitor = spot.translate(spec, 'monitor', 'det')
        self.bdict = self.spec_monitor.get_dict()
        self.spec_monitor_out = []
        for s in range(0, self.spec_monitor.num_states()):
            self.spec_monitor_out.append(self.spec_monitor.out(s))
        self.ap_varnum = dict()
        for ap in self.spec_monitor.ap():
            var = self.bdict.varnum(ap)
            self.ap_varnum[ap.to_str()] = (buddy.bdd_ithvar(var), buddy.bdd_nithvar(var))
        self.num_exec = num_exec
        self.max_exec_len = max_exec_len
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
                if not ret:
                    return self.exec_trace
                (monitor_ret, satisfied) = self.step_monitor(self.current_output_aps)
                if not monitor_ret:
                    self.exec_count_violation += 1
                    break
                if satisfied:
                    break
            self.post_sut()
            if monitor_ret:
                self.exec_count_satisfication += 1
                self.satisfied_exec_sample.append(self.exec_trace)
            self.exec_sample.append(self.exec_trace)

            if k > 0 and k % 500 == 0:
                # output satisfaction and violation counts
                print(f'values:{k},{self.exec_count_satisfication / (self.exec_count_satisfication + self.exec_count_violation)},{self.exec_count_satisfication},{self.exec_count_violation}')
        return None

    def hypothesis_testing(self, mean, alternative):
        sample = np.concatenate((np.zeros(self.exec_count_violation), np.ones(self.exec_count_satisfication)))
        return stats.ttest_1samp(sample, mean, alternative=alternative)

    def reset_sut(self):
        self.number_of_steps = 0
        self.current_output = self.sut.pre()
        self.current_output_aps = self.current_output.split('__')
        self.exec_trace = []
        self.monitor_current_state = self.spec_monitor.get_init_state_number()

    def one_step(self):
        self.number_of_steps += 1
        # strategyから次のアクションを決め、SULを実行する
        action = random.choice(self.actions)
        self.current_output = self.sut.step(action)
        self.current_output_aps = self.current_output.split('__')
        # 実行列を保存
        self.exec_trace.append(action)
        self.exec_trace.append(self.current_output)
        return self.current_output

    def post_sut(self):
        self.sut.post()

    # 出力outputにより、モニターの状態遷移を行う。
    # 返り値はモニターの状態遷移が行われたか否かと条件が常に成立する状態に到達したか否か。モニターの状態遷移が行えないことは、仕様の違反を意味する。
    def step_monitor(self, output_aps : List[str]) -> Tuple[bool, bool]:
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
    def guardCheck(self, output_aps : List[str], edge):
        cond = edge.cond
        # label = spot.bdd_format_formula(self.bdict, cond)
        # # print(f'output: {output}')
        # # print(f'label : {label}')
        neg_cond = buddy.bdd_not(cond)
        if buddy.bdd_satcount(neg_cond) == 0 and edge.src == edge.dst:
            # 条件が常に成立
            return (edge.dst, True)
        aps_bdd = buddy.bdd_support(cond)
        aps = spot.bdd_format_formula(self.bdict, aps_bdd).split(' & ')
        for ap in aps:
            if (ap in output_aps):
                bdd_var = self.ap_varnum[ap][0]
                cond = buddy.bdd_restrict(cond, bdd_var)
            else:
                bdd_var = self.ap_varnum[ap][1]
                cond = buddy.bdd_restrict(cond, bdd_var)
        # restricted_label = spot.bdd_format_formula(self.bdict, cond)
        # print(f'cond  : {restricted_label}')
        ret = buddy.bdd_satcount(cond)
        if (ret > 0):
            return (edge.dst, False)
        else:
            return (None, False)

def initialize_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", dest="model_path", help="path to input model", required=True)
    parser.add_argument("--prop-path", dest="prop_path", help="path to property file", required=True)
    return parser

finally_regex = re.compile(r"F[ ]*\[[0-9 ]+,([0-9 ]+)\].*")
def prop_max_step(prop_path):
    ret = 0
    with open(prop_path) as f:
        for line in f:
            m = finally_regex.match(line)
            if m:
                max_step = int(m[1].strip())
                if max_step > ret:
                    ret = max_step
    if ret == 0:
        return 30
    return ret + 2

def main():
    parser = initialize_argparse()
    args = parser.parse_args()

    mdp = load_automaton_from_file(args.model_path, automaton_type='mdp')
    # visualize_automaton(mdp)
    sul = MdpSUL(mdp)

    with open(args.prop_path, 'r') as f:
      prop_str = f.read().strip()
    print(f'Property: {prop_str}')
    max_exec_len = prop_max_step(args.prop_path)
    print(f'Property max exec length : {max_exec_len}')

    # coins
    actions = ["go1", "go2"]
    # grid world
    # actions = ["North", "South", "West", "East"]
    # mqtt
    # actions = ["ConnectC2", "ConnectC1WithWill", "PublishQoS0C2", "PublishQoS1C1", "SubscribeC1", "UnSubScribeC1", "SubscribeC2", "UnSubScribeC2", "DisconnectTCPC1"]
    # slot machine
    # actions = ["spin1", "spin2", "spin3", "stop"]
    # tcp
    # actions = ["CLOSECONNECTION", "ACK_plus_PSH_paren_V_c_V_c_1_paren_", "SYN_plus_ACK_paren_V_c_V_c_0_paren_", "RST_paren_V_c_V_c_0_paren_", "ACCEPT", "FIN_plus_ACK_paren_V_c_V_c_0_paren_", "LISTEN", "SYN_paren_V_c_V_c_0_paren_", "RCV", "ACK_plus_RST_paren_V_c_V_c_0_paren_", "CLOSE", "ACK_paren_V_c_V_c_0_paren_"]

    smc : StatisticalModelChecker = StatisticalModelChecker(sul, actions, args.prop_path, num_exec=26492, max_exec_len=max_exec_len)
    smc.run()
    print(f'SUT value by SMC: {smc.exec_count_satisfication / smc.num_exec} (satisfication: {smc.exec_count_satisfication}, total: {smc.num_exec})')
    smc_log_path = args.prop_path + '.smclog'
    with open(smc_log_path, 'a+') as f:
        f.write(f'{prop_str}\n{smc.exec_count_satisfication / smc.num_exec}\n{smc.exec_count_satisfication}\n{smc.num_exec}')
    print("Finish evaluation of each round")


if __name__ == "__main__":
    main()