import re
import itertools
import aalpy.paths
from aalpy.base import Oracle, SUL
from aalpy.automata import StochasticMealyMachine
from aalpy.SULs import MdpSUL
from aalpy.oracles import RandomWalkEqOracle, RandomWordEqOracle
from aalpy.learning_algs import run_stochastic_Lstar
from aalpy.utils import visualize_automaton, load_automaton_from_file, smm_to_mdp_conversion, mdp_2_prism_format, model_check_properties, model_check_experiment, get_properties_file, get_correct_prop_values
from Smc import StatisticalModelChecker
from StrategyBridge import StrategyBridge

aalpy.paths.path_to_prism = "/Users/bo40/workspace/PRISM/prism/prism/bin/prism"
aalpy.paths.path_to_properties = "/Users/bo40/workspace/python/AALpy/Benchmarking/prism_eval_props/"

socket_path = '/tmp/multivesta.sock'
example = 'shared_coin'

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

multivesta_output_regex = re.compile("(\d\.\d+) \[var: (\d\.\d+), ci/2: (\d\.\d+)\]")
def initialize_smc(sul, prism_model_path, prism_adv_path, spec_path):

    sb = StrategyBridge(prism_adv_path, prism_model_path)

    return StatisticalModelChecker(sul, sb, spec_path, num_exec=2000)

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
    prop_path = f'/Users/bo40/workspace/python/sandbox/shared_coin.props'
    mdp_2_prism_format(mdp, name='mc_exp', output_path=prism_model_path)
    prism_ret = evaluate_properties(prism_model_path, prop_path, prism_adv_path)

    if len(prism_ret) == 0:
        # 仕様を計算できていない (APが存在しない場合など)
        # adv.traの出力がないので、SMCはできない → Equivalence test
        return super().find_cex(hypothesis)

    sut_value = prism_ret['prop1']

    # SMCを実行する
    smc : StatisticalModelChecker = initialize_smc(self.sul, prism_model_path, prism_adv_path, get_properties_file(example), sut_value)
    cex = smc.run()

    # SMCの結果 と sut_value に有意差があるか検定を行う
    print(f'SUT value : {sut_value}\nHypothesis value : {smc.exec_count_satisfication / smc.num_exec}')
    smc.hypothesis_testing(sut_value, 'two-sided')

    # self.sul.teacher # StochasticTeacherを呼び出すことができる
    # SMC実行時の実行トレースを使ってObservation tableの更新
    refine_ot_by_sample(smc.exec_sample, self.sul.teacher)

    print(f'CEX from SMC: {cex}')
    if cex != None:
        return cex

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