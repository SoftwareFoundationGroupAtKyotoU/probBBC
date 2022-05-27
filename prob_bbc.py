import asyncio
import selectors
import pickle
import re
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

# aalpy.utils.ModelCheckingの関数
prism_prob_output_regex = re.compile("Result: (\d+\.\d+)")
def evaluate_all_properties(prism_file_name, properties_file_name, prism_adv_path):
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


# MultiVeStAの実行
multivesta_output_regrex = re.compile("Result:")
async def execute_smc(prism_model_path, prism_adv_path):
    import os
    import socket
    import pickle
    # MV_python_integratorとの通信socket
    if os.path.exists(socket_path):
        os.remove(socket_path)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(socket_path)
    s.listen()

    multivesta_path = f'/Users/bo40/workspace/python/multivesta/multivesta.jar'
    python_model_path = f'/Users/bo40/workspace/python/sandbox/MV_python_integrator.py'
    quatex_spec = f'/Users/bo40/workspace/python/sandbox/spec.multiquatex'

    multivesta_cmd = f"java -jar {multivesta_path} -c -m {python_model_path} -sm true -f {quatex_spec} -l 1 -sots 1 -sd vesta.python.simpy.SimPyState -vp true -bs 300 -ds [10] -a 0.05 -otherParams python3"
    process = await asyncio.create_subprocess_shell(
        multivesta_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    connection, address = s.accept()
    connection.setblocking(False)

    while True:
        # MultiVeStAの終了時にwhileループを抜ける
        if process.stdout.at_eof():
            break

        # MultiVeStAの標準出力を読みこむ
        data = await process.stdout.readline()
        line = data.decode('utf-8').rstrip()
        print(f'child {line}')

        # print("before recv")
        # # MV_python_integratorとの通信
        # try:
        #     data = connection.recv(4096)
        #     if len(data) > 0:
        #         print("get data from MV_python_integrator")
        #         print(pickle.loads(data))
        # except BlockingIOError:
        #     pass

        # print("after recv")

    await process.wait()
    s.close()
    return 0



def execute_smc_sel(prism_model_path, prism_adv_path):
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
        data = conn.recv(16384)
        if len(data) > 0:
            try:
                cex = pickle.loads(data)
                print(f'MV_py: {cex}')
                if "cex" in cex:
                    ret.append(cex["cex"])
            except pickle.UnpicklingError:
                pass # TODO : dataを保存しておくか、バッファーを大きくする

    # MultiVeStAの標準出力を読み込む
    def read_multivesta(file, mask, ret):
        output = file.read1().decode('utf-8').rstrip()
        print(f'child: {output}')
        # MultiVeStAが終了しているか確認
        if proc.poll() != None:
            sel.modify(file, selectors.EVENT_READ, None)

    sel.register(connection, selectors.EVENT_READ, read_mv_python_integrator)
    sel.register(proc.stdout, selectors.EVENT_READ, read_multivesta)

    quit = False
    ret = []
    while True:
        for key, mask in sel.select():
            if key.data == None:
                quit = True
            else:
                callback = key.data
                # retを返り値で変更するのも良い
                callback(key.fileobj, mask, ret)
        if quit:
            break

    try:
        # MultiVeStAが終了してから一度だけsocketを読む
        data = connection.recv(4096)
        if len(data) > 0:
            print(f'MV_py: {pickle.loads(data)}')
    except BlockingIOError:
        pass

    sel.unregister(connection.fileno())
    sel.unregister(proc.stdout.fileno())
    connection.close()
    s.close()
    sel.close()

    if len(ret) > 0:
        return ret[-1]
    return 0


class ProbBBCOracle(RandomWalkEqOracle) :
  def __init__(self, alphabet: list, sul: SUL, num_steps=5000, reset_after_cex=True, reset_prob=0.09):
    super().__init__(alphabet, sul=sul, num_steps=num_steps, reset_after_cex=reset_after_cex, reset_prob=reset_prob)

  def find_cex(self, hypothesis):
    print('PRISM call')
    if isinstance(hypothesis, StochasticMealyMachine):
        mdp = smm_to_mdp_conversion(hypothesis)
    else:
        mdp = hypothesis

    mdp_2_prism_format(mdp, name='mc_exp', output_path=f'mc_exp.prism')
    prism_model_path = f'mc_exp.prism'
    prism_adv_path = f'adv.tra'
    # get_properties_file(example) -> aalpy/Benchmarking/prism/eval/props/**example**.props
    prism_ret = evaluate_all_properties(prism_model_path, get_properties_file(example), prism_adv_path)

    if len(prism_ret) == 0:
        # 仕様を計算できていない (APが存在しない場合など)
        # adv.traの出力がないので、SMCはできない → Equivalence test
        return super().find_cex(hypothesis)

    # SMCを実行して、観測した動作をobservation tableと比較する

    # asyncio.run(execute_smc(prism_model_path, prism_adv_path))
    cex = execute_smc_sel(prism_model_path, prism_adv_path)

    print(f'CEX from SMC: {cex}')
    cex = super().find_cex(hypothesis) # equivalence testing
    print(f'CEX from EQ testing : {cex}')

    return cex


def learn_benchmark_mdp(example, automaton_type='smm', n_c=20, n_resample=1000, min_rounds=10, max_rounds=500,
                                 strategy='normal', cex_processing='longest_prefix', stopping_based_on_prop=None,
                                 samples_cex_strategy=None):
    # Specify the path to the dot file containing a MDP
    mdp = load_automaton_from_file(f'/Users/bo40/workspace/python/AALpy/DotModels/MDPs/{example}.dot', automaton_type='mdp')
    # visualize_automaton(mdp)
    input_alphabet = mdp.get_input_alphabet()

    sul = MdpSUL(mdp)
    # eq_oracle = RandomWordEqOracle(input_alphabet, sul, num_walks=100, min_walk_len=5, max_walk_len=15,
    #                                reset_after_cex=True)
    # eq_oracle = RandomWalkEqOracle(input_alphabet, sul=sul, num_steps=2000, reset_prob=0.25,
    #                                reset_after_cex=True)
    eq_oracle = ProbBBCOracle(input_alphabet, sul=sul, num_steps=2000, reset_prob=0.25, reset_after_cex=True)
    # EQOracleChain
    learned_mdp = run_stochastic_Lstar(input_alphabet=input_alphabet, eq_oracle=eq_oracle, sul=sul, n_c=n_c,
                                       n_resample=n_resample, min_rounds=min_rounds, max_rounds=max_rounds,
                                       automaton_type=automaton_type, strategy=strategy, cex_processing=cex_processing,
                                       samples_cex_strategy=samples_cex_strategy, target_unambiguity=0.99,
                                       property_based_stopping=stopping_based_on_prop, custom_oracle=True)

    return learned_mdp



learned_model = learn_benchmark_mdp(example)

if isinstance(learned_model, StochasticMealyMachine):
    mdp = smm_to_mdp_conversion(learned_model)
else:
    mdp = learned_model

values, diff = model_check_experiment(get_properties_file(example), get_correct_prop_values(example), mdp)

print('Value for each property:', [round(d * 100, 2) for d in values.values()])
print('Error for each property:', [round(d * 100, 2) for d in diff.values()])


    # proc = subprocess.Popen(
    #     ['java', '-jar', multivesta_path, '-c', '-m', python_model_path, '-sm',  'true', '-f', quatex_spec, '-l', '2', '-sots', '1', '-sd', 'vesta.python.simpy.SimPyState', '-vp', 'true', '-bs', '300', '-ds', '[10]', '-a', '0.05', '-otherParams', 'python3'],
    #     stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    # )
    # # TODO: 非同期にして、integratorと通信
    # for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
    #     print(line) # for debug
    #     if not line:
    #         break
    #     else:
    #         match = multivesta_output_regrex.match(line)