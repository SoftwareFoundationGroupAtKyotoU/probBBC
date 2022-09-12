import re
import collections
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

aalpy.paths.path_to_prism = "/Users/bo40/workspace/PRISM/prism/prism/bin/prism"
aalpy.paths.path_to_properties = "/Users/bo40/workspace/python/AALpy/Benchmarking/prism_eval_props/"

example = 'shared_coin'
prop_name = 'shared_coin1'

prism_prob_output_regex = re.compile("Result: (\d+\.\d+)")
def evaluate_properties(prism_file_name, properties_file_name, prism_adv_path):
    print('PRISM call')
    import subprocess
    import io
    from os import path

    prism_file = aalpy.paths.path_to_prism.split('/')[-1]
    path_to_prism_file = aalpy.paths.path_to_prism[:-len(prism_file)]

    exportadvmdp = '-exportadvmdp'
    file_abs_path = path.abspath(prism_file_name)
    adversary_path = path.abspath(prism_adv_path)
    properties_als_path = path.abspath(properties_file_name)
    results = {}
    # PRISMの呼び出し adversaryを出力するようにパラメタ指定
    proc = subprocess.Popen(
        [aalpy.paths.path_to_prism, exportadvmdp, adversary_path, file_abs_path, properties_als_path],
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
    counter = collections.Counter(sample)
    return counter.most_common()

def compare_frequency(trace, smc_freq, mdp):
    
    return False

# multivesta_output_regex = re.compile("(\d\.\d+) \[var: (\d\.\d+), ci/2: (\d\.\d+)\]")

def initialize_smc(sul, prism_model_path, prism_adv_path, spec_path, sut_value, observation_table):

    sb = StrategyBridge(prism_adv_path, prism_model_path)

    return StatisticalModelChecker(sul, sb, spec_path, sut_value, observation_table, num_exec=2000)

# PRISM + SMC による反例探索オラクル
class ProbBBReachOracle(RandomWalkEqOracle) :
  def __init__(self, alphabet: list, sul: SUL, num_steps=5000, reset_after_cex=True, reset_prob=0.09):
    self.previous_strategy = None
    self.current_strategy = None
    self.observation_table = None
    super().__init__(alphabet, sul=sul, num_steps=num_steps, reset_after_cex=reset_after_cex, reset_prob=reset_prob)

  def find_cex(self, hypothesis):
    if isinstance(hypothesis, StochasticMealyMachine):
        mdp = smm_to_mdp_conversion(hypothesis)
    else:
        mdp = hypothesis

    prism_model_path = f'/Users/bo40/workspace/python/mc_exp.prism'
    prism_adv_path = f'/Users/bo40/workspace/python/adv.tra'
    prop_path = f'/Users/bo40/workspace/python/sandbox/{prop_name}.props'
    mdp_2_prism_format(mdp, name='mc_exp', output_path=prism_model_path)
    prism_ret = evaluate_properties(prism_model_path, prop_path, prism_adv_path)

    if len(prism_ret) == 0:
        # 仕様を計算できていない (APが存在しない場合など)
        # adv.traの出力がないので、SMCはできない → Equivalence test
        return super().find_cex(hypothesis)

    sut_value = prism_ret['prop1']

    # SMCを実行する
    ltl_prop_path = f'/Users/bo40/workspace/python/sandbox/{prop_name}.ltl'
    smc : StatisticalModelChecker = initialize_smc(self.sul, prism_model_path, prism_adv_path, ltl_prop_path, sut_value, self.observation_table)
    cex = smc.run()

    print(f'CEX from SMC: {cex}')

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
    # SMC実行中の実行列のサンプルとObservationTableから反例を見つける
    cex_candidates = sort_by_frequency(smc.exec_sample)
    for (exec_trace, freq) in cex_candidates:
        if compare_frequency(exec_trace, freq, mdp):
            # 違う分布であれば反例
            return exec_trace

    # if hyp_test_ret satisfies the error bound
    # SMCで反例が見つからなかったので equivalence testing
    cex = super().find_cex(hypothesis) # equivalence testing
    print(f'CEX from EQ testing : {cex}')

    return cex

def learn_mdp_and_strategy(example, automaton_type='smm', n_c=20, n_resample=1000, min_rounds=10, max_rounds=500,
                                 strategy='normal', cex_processing='longest_prefix', stopping_based_on_prop=None,
                                 samples_cex_strategy=None):
    mdp = load_automaton_from_file(f'/Users/bo40/workspace/python/AALpy/DotModels/MDPs/{example}.dot', automaton_type='mdp')
    # visualize_automaton(mdp)
    input_alphabet = mdp.get_input_alphabet()

    sul = MdpSUL(mdp)

    eq_oracle = ProbBBReachOracle(input_alphabet, sul=sul, num_steps=2000, reset_prob=0.25, reset_after_cex=True)
    # EQOracleChain
    learned_mdp = run_stochastic_Lstar(input_alphabet=input_alphabet, eq_oracle=eq_oracle, sul=sul, n_c=n_c,
                                       n_resample=n_resample, min_rounds=min_rounds, max_rounds=max_rounds,
                                       automaton_type=automaton_type, strategy=strategy, cex_processing=cex_processing,
                                       samples_cex_strategy=samples_cex_strategy, target_unambiguity=0.99,
                                       property_based_stopping=stopping_based_on_prop, custom_oracle=True)

    learned_strategy = eq_oracle.learned_strategy

    return learned_mdp, learned_strategy

_, strategy = learn_mdp_and_strategy(example)

execute_smc(example, strategy)
