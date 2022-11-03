import re
import collections
import os
from sys import prefix
from typing import List
import aalpy.paths
from aalpy.base import Oracle, SUL
from aalpy.automata import StochasticMealyMachine
from aalpy.SULs import MdpSUL
from aalpy.oracles import RandomWalkEqOracle, RandomWordEqOracle
from aalpy.learning_algs import run_stochastic_Lstar
from aalpy.utils import load_automaton_from_file, mdp_2_prism_format, get_properties_file, get_correct_prop_values
from aalpy.automata.StochasticMealyMachine import smm_to_mdp_conversion

from Smc import StatisticalModelChecker
from StrategyBridge import StrategyBridge
from PrismModelConverter import add_step_counter_to_prism_model


prism_prob_output_regex = re.compile("Result: (\d+\.\d+)")
def evaluate_properties(prism_file_name, properties_file_name, prism_adv_path, exportstates_path, exporttrans_path, exportlabels_path):
    print('PRISM call', flush=True)
    import subprocess
    import io
    from os import path

    prism_file = aalpy.paths.path_to_prism.split('/')[-1]
    path_to_prism_file = aalpy.paths.path_to_prism[:-len(prism_file)]

    exportadvmdp = '-exportadvmdp'
    adversary_path = path.abspath(prism_adv_path)
    exportstates = '-exportstates'
    exporttrans = '-exporttrans'
    exportlabels = '-exportlabels'
    file_abs_path = path.abspath(prism_file_name)
    properties_als_path = path.abspath(properties_file_name)
    results = {}
    # PRISMの呼び出し adversaryを出力するようにパラメタ指定
    proc = subprocess.Popen(
        [aalpy.paths.path_to_prism, exportadvmdp, adversary_path, exportstates, exportstates_path, exporttrans, exporttrans_path, exportlabels, exportlabels_path, file_abs_path, properties_als_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=path_to_prism_file)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        print(line) # デバッグ用出力
        if not line:
            break
        else:
            match = prism_prob_output_regex.match(line)
            if match:
                results[f'prop{len(results) + 1}'] = float(match.group(1))
    proc.kill()
    return results

def refine_ot_by_sample(sample, teacher):
    pass

def sort_by_frequency(sample):
    # 以下デバッグ用
    # for t in sample:
    #     eq = True
    #     for a, b in zip(t, sample[0]):
    #         if a != b:
    #             eq = False
    #             break
    #     if eq:
    #         print(t)
    prefix_closed_sample = []
    for trace in sample:
        for i in range(2, len(trace) + 1, 2):
            prefix_closed_sample.append(tuple(trace[0:i]))
    counter = collections.Counter(prefix_closed_sample)
    return counter.most_common()

def compare_frequency(satisfied_sample, total_sample, mdp, diff_bound=0.05):
    def probability_on_mdp(trace, mdp):
        ret = 1.0
        mdp_state = mdp.initial_state
        for input, output in zip(trace[0::2], trace[1::2]):
            for next_state, prob in mdp_state.transitions[input]:
                if next_state.output == output:
                    ret = ret * prob
                    mdp_state = next_state
                    break
        return ret

    cex_candidates = sort_by_frequency(satisfied_sample)
    for (exec_trace, freq) in cex_candidates:
        exec_trace = list(exec_trace)
        # MDPでのtraceの出現確率を計算
        mdp_prob = probability_on_mdp(exec_trace, mdp)

        # total_sampleからtraceと同じ入力の実行列を抽出する
        population_size = 0
        for trace in total_sample:
            equality_flag = True
            for action1, action2 in zip(exec_trace[0::2], trace[0::2]):
                if action1 != action2:
                    equality_flag = False
                    break
            if equality_flag:
                population_size += 1

        sut_prob = freq / population_size

        # 違う分布であれば反例として返す
        # TODO: chernoff boundを使って評価する
        if abs(mdp_prob - sut_prob) > diff_bound:
            return exec_trace

    # 反例が見つからなかった
    return None

def initialize_strategy_bridge_and_smc(sul, prism_model_path, prism_adv_path, spec_path, sut_value, observation_table, returnCEX):

    sb = StrategyBridge(prism_adv_path, prism_model_path)

    return StatisticalModelChecker(sul, sb, spec_path, sut_value, observation_table, num_exec=5000, returnCEX=returnCEX)

# PRISM + SMC による反例探索オラクル
class ProbBBReachOracle(RandomWalkEqOracle) :
  def __init__(self, prism_model_path, prism_adv_path, prism_prop_path, ltl_prop_path, alphabet: list, sul: SUL, num_steps=5000, reset_after_cex=True, reset_prob=0.09, statistical_test_bound=0.025):
    self.prism_model_path = prism_model_path
    self.prism_adv_path = prism_adv_path
    self.prism_prop_path = prism_prop_path
    self.ltl_prop_path = ltl_prop_path
    self.previous_strategy = None
    self.current_strategy = None
    self.observation_table = None
    self.statistical_test_bound = statistical_test_bound
    super().__init__(alphabet, sul=sul, num_steps=num_steps, reset_after_cex=reset_after_cex, reset_prob=reset_prob)

  def find_cex(self, hypothesis):
    if isinstance(hypothesis, StochasticMealyMachine):
        mdp = smm_to_mdp_conversion(hypothesis)
    else:
        mdp = hypothesis

    # PRISMへの入出力ファイルを準備
    if os.path.isfile(self.prism_model_path):
        os.remove(self.prism_model_path)
    if os.path.isfile(self.prism_adv_path):
        os.remove(self.prism_adv_path)
    converted_model_path = f'{self.prism_model_path}.convert'
    if os.path.isfile(converted_model_path):
        os.remove(converted_model_path)
    self.exportstates_path = f'{self.prism_model_path}.sta'
    if os.path.isfile(self.exportstates_path):
        os.remove(self.exportstates_path)
    self.exporttrans_path = f'{self.prism_model_path}.tra'
    if os.path.isfile(self.exporttrans_path):
        os.remove(self.exporttrans_path)
    self.exportlabels_path = f'{self.prism_model_path}.lab'
    if os.path.isfile(self.exportlabels_path):
        os.remove(self.exportlabels_path)

    mdp_2_prism_format(mdp, name='mc_exp', output_path=self.prism_model_path)
    # PRISMのモデルにカウンタ変数を埋め込む
    add_step_counter_to_prism_model(self.prism_model_path, converted_model_path)

    # PRISMでモデル検査を実行
    prism_ret = evaluate_properties(converted_model_path, self.prism_prop_path, self.prism_adv_path, self.exportstates_path, self.exporttrans_path, self.exportlabels_path)

    if len(prism_ret) == 0:
        # 仕様を計算できていない (APが存在しない場合など)
        # adv.traの出力がないので、SMCはできない → Equivalence test
        return super().find_cex(hypothesis)

    if not os.path.isfile(self.prism_adv_path):
        # strategyが生成できていない場合 (エラー)
        return super().find_cex(hypothesis)

    self.learned_strategy = self.prism_adv_path
    sut_value = prism_ret['prop1']

    # SMCを実行する
    sb = StrategyBridge(self.prism_adv_path, self.exportstates_path, self.exporttrans_path, self.exportlabels_path)
    smc : StatisticalModelChecker = StatisticalModelChecker(self.sul, sb, self.ltl_prop_path, sut_value, self.observation_table, num_exec=5000, returnCEX=True)
    cex = smc.run()

    print(f'CEX from SMC: {cex}', flush=True)

    if cex != -1 and cex != None:
        # 具体的な反例が得られればそれを返す
        return cex

    if cex == -1:
        # Observation tableがclosedかつconsistentでなくなったとき
        return None

    # SMCの結果 と sut_value に有意差があるか検定を行う
    print(f'SUT value : {sut_value}\nHypothesis value : {smc.exec_count_satisfication / smc.num_exec}')
    hyp_test_ret = smc.hypothesis_testing(sut_value, 'two-sided')
    print(f'Hypothesis testing result : {hyp_test_ret}')

    # if hyp_test_ret violates the error bound
    if hyp_test_ret.pvalue < self.statistical_test_bound:
        # SMC実行中の実行列のサンプルとObservationTableから反例を見つける
        # TODO: 複数回のSMCのサンプルの和集合をtotal_sampleとして渡すこともできるようにする
        cex = compare_frequency(smc.satisfied_exec_sample, smc.exec_sample, mdp, self.statistical_test_bound)
        if cex != None:
            return cex

    # if hyp_test_ret satisfies the error bound
    # SMCで反例が見つからなかったので equivalence testing
    cex = super().find_cex(hypothesis) # equivalence testing
    print(f'CEX from EQ testing : {cex}')

    return cex

def learn_mdp_and_strategy(mdp_model_path, prism_model_path, prism_adv_path, prism_prop_path, ltl_prop_path, automaton_type='smm', n_c=20, n_resample=1000, min_rounds=20, max_rounds=240,
                                 strategy='normal', cex_processing='longest_prefix', stopping_based_on_prop=None,
                                 samples_cex_strategy=None):
    mdp = load_automaton_from_file(mdp_model_path, automaton_type='mdp')
    # visualize_automaton(mdp)
    input_alphabet = mdp.get_input_alphabet()

    sul = MdpSUL(mdp)

    eq_oracle = ProbBBReachOracle(prism_model_path, prism_adv_path, prism_prop_path, ltl_prop_path, input_alphabet, sul=sul, num_steps=2000, reset_prob=0.25, reset_after_cex=True)
    # EQOracleChain
    learned_mdp = run_stochastic_Lstar(input_alphabet=input_alphabet, eq_oracle=eq_oracle, sul=sul, n_c=n_c,
                                       n_resample=n_resample, min_rounds=min_rounds, max_rounds=max_rounds,
                                       automaton_type=automaton_type, strategy=strategy, cex_processing=cex_processing,
                                       samples_cex_strategy=samples_cex_strategy, target_unambiguity=0.99,
                                       property_based_stopping=stopping_based_on_prop, custom_oracle=True)

    learned_strategy = eq_oracle.learned_strategy

    sb = StrategyBridge(prism_adv_path, eq_oracle.exportstates_path, eq_oracle.exporttrans_path, eq_oracle.exportlabels_path)
    smc : StatisticalModelChecker = StatisticalModelChecker(sul, sb, ltl_prop_path, 0, None, num_exec=5000, returnCEX=False)
    smc.run()
    print(f'Hypothesis value : {smc.exec_count_satisfication / smc.num_exec}')

    return learned_mdp, learned_strategy

# example = 'shared_coin'
# prop_name = 'shared_coin2'
# example = 'slot_machine'
# prop_name = 'slot'
# example = 'mqtt'
# prop_name = 'mqtt'

# mdp_model_path = f'/Users/bo40/workspace/python/AALpy/DotModels/MDPs/{example}.dot'
# prism_model_path = f'/Users/bo40/workspace/python/mc_exp.prism'
# prism_adv_path = f'/Users/bo40/workspace/python/adv.tra'
# prism_prop_path = f'/Users/bo40/workspace/python/sandbox/{prop_name}.props'
# ltl_prop_path = f'/Users/bo40/workspace/python/sandbox/{prop_name}.ltl'

# learned_mdp, strategy = learn_mdp_and_strategy(mdp_model_path, prism_model_path, prism_adv_path, prism_prop_path, ltl_prop_path)

# print("Finish prob bbc")


