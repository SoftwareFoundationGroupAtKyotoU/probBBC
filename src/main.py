import logging
import os
import sys
from os.path import abspath
import argparse
import aalpy.paths
from ProbBlackBoxChecking import learn_mdp_and_strategy


def initialize_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-file", dest="model_file", help="path to input dot model", required=True
    )
    parser.add_argument(
        "--prop-file", dest="prop_file", help="path to property file", required=True
    )
    parser.add_argument(
        "--prism-path", dest="prism_path", help="path to PRISM", required=True
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        help="name of output directory (Default value = 'results')",
        default="results",
    )
    parser.add_argument(
        "--save-files-for-each-round",
        dest="save_files_for_each_round",
        action="store_true",
        help="save files(model, hypothesis, strategy) for each rounds",
    )
    parser.add_argument(
        "--min-rounds",
        dest="min_rounds",
        type=int,
        help="minimum number of learning rounds of L*mdp (Default value = 20)",
        default=20,
    )
    parser.add_argument(
        "--max-rounds",
        dest="max_rounds",
        type=int,
        help="if learning_rounds >= max_rounds, L*mdp learning will stop (Default value = 240)",
        default=240,
    )
    parser.add_argument(
        "--l-star-mdp-strategy",
        dest="l_star_mdp_strategy",
        help="either one of ['classic', 'normal', 'chi2'] or a object implementing DifferenceChecker class,\ndefault value is 'normal'. Classic strategy is the one presented\nin the seed paper, 'normal' is the updated version and chi2 is based on chi squared.",
        default="normal",
    )
    parser.add_argument(
        "--n-cutoff",
        dest="n_c",
        type=int,
        help="cutoff for a cell to be considered complete (Default value = 20), only used with 'classic' strategy",
        default=20,
    )
    parser.add_argument(
        "--n-resample",
        dest="n_resample",
        type=int,
        help="resampling size (Default value = 100), only used with 'classic' L*mdp strategy",
        default=100,
    )
    parser.add_argument(
        "--target-unambiguity",
        dest="target_unambiguity",
        type=float,
        help="target unambiguity value of L*mdp (default 0.99)",
        default=0.99,
    )
    parser.add_argument(
        "--eq-num-steps",
        dest="eq_num_steps",
        type=int,
        help="number of steps to be preformed by equivalence oracle",
        default=2000,
    )
    parser.add_argument(
        "--smc-max-exec",
        dest="smc_max_exec",
        type=int,
        help="max number of executions by SMC (default=5000)",
        default=5000,
    )
    parser.add_argument(
        "--only-classical-equivalence-testing",
        dest="only_classical_equivalence_testing",
        help="Skip the strategy guided equivalence testing using SMC",
        action="store_true",
    )
    parser.add_argument(
        "--smc-statistical-test-bound",
        dest="smc_statistical_test_bound",
        type=float,
        help="statistical test bound of difference check between SMC and model-checking (default 0.025)",
        default=0.025,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        "--debug",
        dest="debug",
        action="store_true",
        help="output debug messages",
    )

    return parser


def main():
    parser = initialize_argparse()
    args = parser.parse_args()
    logging.basicConfig(
        format="%(asctime)s %(module)s[%(lineno)d] [%(levelname)s]: %(message)s",
        stream=sys.stdout,
        level=logging.INFO if not args.debug else logging.DEBUG,
    )
    aalpy.paths.path_to_prism = args.prism_path

    output_dir = abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    mdp_model_path = args.model_file
    prism_model_path = f"{output_dir}/mc_exp.prism"
    prism_adv_path = f"{output_dir}/adv.tra"
    prop_file = args.prop_file
    prism_prop_path = prop_file
    prop_file_name, _ = os.path.splitext(prop_file)
    ltl_prop_path = f"{prop_file_name}.ltl"

    learned_mdp, strategy = learn_mdp_and_strategy(
        mdp_model_path,
        prism_model_path,
        prism_adv_path,
        prism_prop_path,
        ltl_prop_path,
        output_dir=output_dir,
        save_files_for_each_round=args.save_files_for_each_round,
        min_rounds=args.min_rounds,
        max_rounds=args.max_rounds,
        strategy=args.l_star_mdp_strategy,
        n_c=args.n_c,
        n_resample=args.n_resample,
        target_unambiguity=args.target_unambiguity,
        eq_num_steps=args.eq_num_steps,
        smc_max_exec=args.smc_max_exec,
        only_classical_equivalence_testing=args.only_classical_equivalence_testing,
        smc_statistical_test_bound=args.smc_statistical_test_bound,
        debug=args.debug,
    )

    print("Finish prob bbc")


if __name__ == "__main__":
    main()
