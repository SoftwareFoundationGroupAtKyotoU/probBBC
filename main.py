import os
import sys
import argparse
import aalpy.paths
from ProbBlackBoxChecking import learn_mdp_and_strategy

def initialize_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", dest="model_name", help="name of input model", required=True)
    parser.add_argument("--prop-name", dest="prop_name", help="name of property file", required=True)
    parser.add_argument("--min-rounds", dest="min_rounds", type=int, help="minimum number of learning rounds of L*mdp (Default value = 20)", default=20)
    parser.add_argument("--max-rounds", dest="max_rounds", type=int, help="if learning_rounds >= max_rounds, L*mdp learning will stop (Default value = 240)", default=240)
    parser.add_argument("--l-star-mdp-strategy", dest="l_star_mdp_strategy", help="either one of ['classic', 'normal', 'chi2'] or a object implementing DifferenceChecker class,\ndefault value is 'normal'. Classic strategy is the one presented\nin the seed paper, 'normal' is the updated version and chi2 is based on chi squared.", default="normal")
    parser.add_argument("--n-cutoff", dest="n_c", type=int, help="cutoff for a cell to be considered complete (Default value = 20), only used with 'classic' strategy", default=20)
    parser.add_argument("--n-resample", dest="n_resample", type=int, help="resampling size (Default value = 100), only used with 'classic' L*mdp strategy", default=100)
    parser.add_argument("--target-unambiguity", dest="target_unambiguity", type=float, help="target unambiguity value of L*mdp (default 0.99)", default=0.99)
    parser.add_argument("--eq-num-steps", dest="eq_num_steps", type=int, help="number of steps to be preformed by equivalence oracle", default=2000)
    parser.add_argument("--smc-max-exec", dest="smc_max_exec", type=int, help="max number of executions by SMC (default=5000)", default=5000)
    parser.add_argument("--smc-statistical-test-bound", dest="smc_statistical_test_bound", type=float, help="statistical test bound of difference check between SMC and model-checking (default 0.025)", default=0.025)
    parser.add_argument("-v", "--verbose", "--debug", dest="debug", action="store_true", help="output debug messages")

    return parser


def main_debug():
    parser = initialize_argparse()
    args = parser.parse_args()

    aalpy.paths.path_to_prism = "/Users/bo40/workspace/PRISM/prism/prism/bin/prism"
    aalpy.paths.path_to_properties = "/Users/bo40/workspace/python/AALpy/Benchmarking/prism_eval_props/"

    mdp_name = args.model_name
    prop_name = args.prop_name
    # example = 'shared_coin'
    # prop_name = 'shared_coin'
    # example = 'slot_machine'
    # prop_name = 'slot'
    # example = 'mqtt'
    # prop_name = 'mqtt'
    # example = 'tcp'
    # prop_name = 'tcp'
    # example = 'first_grid'
    # prop_name = 'first_grid'

    file_dir = os.path.dirname(__file__) + "/results"
    os.makedirs(file_dir, exist_ok=True)
    prop_dir = os.path.dirname(__file__)

    mdp_model_path = f'/Users/bo40/workspace/python/AALpy/DotModels/MDPs/{mdp_name}.dot'
    prism_model_path = f'{file_dir}/mc_exp.prism'
    prism_adv_path = f'{file_dir}/adv.tra'
    prism_prop_path = f'{prop_dir}/{prop_name}.props'
    ltl_prop_path = f'{prop_dir}/{prop_name}.ltl'

    learned_mdp, strategy = learn_mdp_and_strategy(mdp_model_path, prism_model_path, prism_adv_path, prism_prop_path, ltl_prop_path,
        min_rounds=args.min_rounds, max_rounds=args.max_rounds, strategy=args.l_star_mdp_strategy, n_c=args.n_c, n_resample=args.n_resample,
        target_unambiguity=args.target_unambiguity, eq_num_steps=args.eq_num_steps, smc_max_exec=args.smc_max_exec,
        smc_statistical_test_bound=args.smc_statistical_test_bound, debug=args.debug)

    print("Finish prob bbc")

def main():
    parser = initialize_argparse()
    args = parser.parse_args()

    aalpy.paths.path_to_prism = "/home/lab8/shijubo/prism-4.7-linux64/bin/prism"
    aalpy.paths.path_to_properties = "/home/lab8/shijubo/ProbBBC/AALpy/Benchmarking/prism_eval_props/"

    mdp_name = args.model_name
    prop_name = args.prop_name
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

    learned_mdp, strategy = learn_mdp_and_strategy(mdp_model_path, prism_model_path, prism_adv_path, prism_prop_path, ltl_prop_path,
        min_rounds=args.min_rounds, max_rounds=args.max_rounds, strategy=args.l_star_mdp_strategy, n_c=args.n_c, n_resample=args.n_resample,
        target_unambiguity=args.target_unambiguity, eq_num_steps=args.eq_num_steps, smc_max_exec=args.smc_max_exec,
        smc_statistical_test_bound=args.smc_statistical_test_bound, debug=args.debug)

    print("Finish prob bbc")

if __name__ == "__main__":
    main()

