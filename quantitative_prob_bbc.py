import asyncio
import selectors
import re
import itertools
import aalpy.paths
from aalpy.base import Oracle, SUL
from aalpy.automata import StochasticMealyMachine
from aalpy.SULs import MdpSUL
from aalpy.oracles import RandomWalkEqOracle, RandomWordEqOracle
from aalpy.learning_algs import run_stochastic_Lstar
from aalpy.utils import visualize_automaton, load_automaton_from_file, smm_to_mdp_conversion, mdp_2_prism_format, model_check_properties, model_check_experiment, get_properties_file, get_correct_prop_values

aalpy.paths.path_to_prism = "/Users/bo40/workspace/PRISM/prism/prism/bin/prism"
aalpy.paths.path_to_properties = "/Users/bo40/workspace/python/AALpy/Benchmarking/prism_eval_props/"

socket_path = '/tmp/multivesta.sock'
example = 'shared_coin'

prism_prob_output_regex = re.compile("Result: (\d+\.\d+)")
def evaluate_properties(prism_file_name, properties_file_name, prism_adv_path):
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

def find_cex(sample, ot):
    pass

multivesta_output_regex = re.compile("(\d\.\d+) \[var: (\d\.\d+), ci/2: (\d\.\d+)\]")
def execute_smc(prism_model_path, prism_adv_path):
    import os
    import socket
    import pickle
    import subprocess
    # MV_python_integratorとの通信socket
    if os.path.exists(socket_path):
        os.remove(socket_path)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(socket_path)
    s.listen()

    multivesta_path = f'/Users/bo40/workspace/python/multivesta/multivesta.jar'
    python_model_path = f'/Users/bo40/workspace/python/sandbox/MV_python_integrator.py'
    quatex_spec = f'/Users/bo40/workspace/python/sandbox/spec.multiquatex'

    # -vp : display interactive plot window
    multivesta_cmd = ["java", "-jar", multivesta_path, "-c", "-m", python_model_path, "-sm", "true", "-f", quatex_spec, "-l", "1", "-sots", "1", "-sd", "vesta.python.simpy.SimPyState", "-vp", "false", "-bs", "300", "-ds", "[10]", "-a", "0.05", "-otherParams", "python3"]
    proc = subprocess.Popen(multivesta_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    connection, _ = s.accept()
    connection.setblocking(False)

    sel = selectors.DefaultSelector()

    # MultiVeStAから呼び出されるモデルとの通信sokcetを読み出す
    def read_mv_python_integrator(conn, mask, ret):
        data = conn.recv(32768)
        if len(data) > 0:
            try:
                params = pickle.loads(data)
                # print(f'MV_py: {cex}')
                if "print" in params:
                    print(f'MV_integrator: {params["print"]}')
                if "trace" in params:
                    ret['sample'].append(params["trace"])
                if "cex" in params:
                    ret['cex'].append(params["cex"])
            except pickle.UnpicklingError:
                pass # TODO : dataを保存しておくか、バッファーを大きくする
        return ret

    # MultiVeStAの標準出力を読み込む
    def read_multivesta(file, mask, ret):
        output = file.read1().decode('utf-8').rstrip()
        for line in output.splitlines():
            match = multivesta_output_regex.search(line)
            if match:
                ret['result'].append((match.group(1), match.group(2), match.group(3)))
        print(f'child: {output}')
        # MultiVeStAが終了しているか確認
        if proc.poll() != None:
            sel.modify(file, selectors.EVENT_READ, None)
        return ret

    sel.register(connection, selectors.EVENT_READ, read_mv_python_integrator)
    sel.register(proc.stdout, selectors.EVENT_READ, read_multivesta)

    quit = False
    multivesta_ret = {'sample': [], 'cex': [], 'result': []}
    while True:
        for key, mask in sel.select():
            if key.data == None:
                quit = True
            else:
                callback = key.data
                multivesta_ret = callback(key.fileobj, mask, multivesta_ret)
        if quit:
            break

    try:
        # MultiVeStAが終了してから一度だけsocketを読む
        data = connection.recv(16384)
        if len(data) > 0:
            print(f'MV_py: {pickle.loads(data)}')
    except BlockingIOError:
        pass

    sel.unregister(connection.fileno())
    sel.unregister(proc.stdout.fileno())
    connection.close()
    s.close()
    sel.close()

    if len(multivesta_ret['result']) == 0:
        multivesta_ret['result'] = [(None,None,None)]

    if len(multivesta_ret['cex']) > 0:
        return multivesta_ret['sample'], multivesta_ret['cex'][-1], multivesta_ret['result'][0]

    return multivesta_ret['sample'], None, multivesta_ret['result'][0]

class ProbBBReachOracle(RandomWalkEqOracle) :
  def __init__(self, alphabet: list, sul: SUL, num_steps=5000, reset_after_cex=True, reset_prob=0.09):
    self.previous_strategy = None
    self.current_strategy = None
    super().__init__(alphabet, sul=sul, num_steps=num_steps, reset_after_cex=reset_after_cex, reset_prob=reset_prob)

  def find_cex(self, hypothesis):
    print('PRISM call')
    if isinstance(hypothesis, StochasticMealyMachine):
        mdp = smm_to_mdp_conversion(hypothesis)
    else:
        mdp = hypothesis

    prism_model_path = f'/Users/bo40/workspace/python/mc_exp.prism'
    prism_adv_path = f'/Users/bo40/workspace/python/adv.tra'
    mdp_2_prism_format(mdp, name='mc_exp', output_path=prism_model_path)
    # get_properties_file(example) -> aalpy/Benchmarking/prism/eval/props/**example**.props
    prism_ret = evaluate_properties(prism_model_path, get_properties_file(example), prism_adv_path)

    if len(prism_ret) == 0:
        # 仕様を計算できていない (APが存在しない場合など)
        # adv.traの出力がないので、SMCはできない → Equivalence test
        return super().find_cex(hypothesis)

    # SMCを実行して、モデルとSUTそれぞれの仕様の値を比較する

    # asyncio.run(execute_smc(prism_model_path, prism_adv_path))
    sample, cex, hypothesis_value = execute_smc(prism_model_path, prism_adv_path)

    sut_value = prism_ret['prop1']

    # self.sul.teacher # StochasticTeacherを呼び出すことができる

    print(f'SUT value : {sut_value}\nHypothesis value : {hypothesis_value[0]}')

    # hypothesis_value と sut_value を比較して違っていれば、cexを見つける

    print(f'CEX from SMC: {cex}')
    if cex != None:
        return cex

    find_cex(sample, None)

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