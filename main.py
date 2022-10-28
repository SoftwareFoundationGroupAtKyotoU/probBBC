import os
import sys
import aalpy.paths
from ProbBlackBoxChecking import learn_mdp_and_strategy


def main_debug():
    aalpy.paths.path_to_prism = "/Users/bo40/workspace/PRISM/prism/prism/bin/prism"
    aalpy.paths.path_to_properties = "/Users/bo40/workspace/python/AALpy/Benchmarking/prism_eval_props/"

    # example = 'shared_coin'
    # prop_name = 'shared_coin2'
    # example = 'slot_machine'
    # prop_name = 'slot'
    example = 'mqtt'
    prop_name = 'mqtt'
    # example = sys.argv[1]
    # prop_name = sys.argv[2]

    file_dir = os.path.dirname(__file__) + "/results"
    os.makedirs(file_dir, exist_ok=True)
    prop_dir = os.path.dirname(__file__)

    mdp_model_path = f'/Users/bo40/workspace/python/AALpy/DotModels/MDPs/{example}.dot'
    prism_model_path = f'{file_dir}/mc_exp.prism'
    prism_adv_path = f'{file_dir}/adv.tra'
    prism_prop_path = f'{prop_dir}/{prop_name}.props'
    ltl_prop_path = f'{prop_dir}/{prop_name}.ltl'

    learned_mdp, strategy = learn_mdp_and_strategy(mdp_model_path, prism_model_path, prism_adv_path, prism_prop_path, ltl_prop_path)

    print("Finish prob bbc")

def main():
    aalpy.paths.path_to_prism = "/home/lab8/shijubo/prism-4.7-linux64/bin/prism"
    aalpy.paths.path_to_properties = "/home/lab8/shijubo/ProbBBC/AALpy/Benchmarking/prism_eval_props/"

    mdp_name = sys.argv[1]
    prop_name = sys.argv[2]
    # example = 'shared_coin'
    # prop_name = 'shared_coin2'
    # example = 'slot_machine'
    # prop_name = 'slot'
    # example = 'mqtt'
    # prop_name = 'mqtt'

    file_dir = os.path.dirname(__file__) + "/results"
    os.makedirs(file_dir, exist_ok=True)
    prop_dir = os.path.dirname(__file__)

    mdp_model_path = f'/home/lab8/shijubo/ProbBBC/AALpy/DotModels/MDPs/{mdp_name}.dot'
    prism_model_path = f'{file_dir}/mc_exp.prism'
    prism_adv_path = f'{file_dir}/adv.tra'
    prism_prop_path = f'{prop_dir}/{prop_name}.props'
    ltl_prop_path = f'{prop_dir}/{prop_name}.ltl'

    learned_mdp, strategy = learn_mdp_and_strategy(mdp_model_path, prism_model_path, prism_adv_path, prism_prop_path, ltl_prop_path)

    print("Finish prob bbc")

if __name__ == "__main__":
    main()

