import os
import argparse
from aalpy.SULs import MdpSUL
from aalpy.utils import load_automaton_from_file

from Smc import StatisticalModelChecker
from StrategyBridge import StrategyBridge


def initialize_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds-log-dir", dest="rounds_log_dir", help="path to log directory.", required=True)
    parser.add_argument("--model-path", dest="model_path", help="path to input model", required=True)
    parser.add_argument("--prop-path", dest="prop_path", help="path to property file", required=True)
    return parser

def main():
    parser = initialize_argparse()
    args = parser.parse_args()

    adv_file_name = "adv.tra"
    exportstates_file_name = "mc_exp.prism.sta"
    exporttrans_file_name = "mc_exp.prism.tra"
    exportlabels_file_name = "mc_exp.prism.lab"

    mdp = load_automaton_from_file(args.model_path, automaton_type='mdp')
    # visualize_automaton(mdp)
    sul = MdpSUL(mdp)

    for file in os.listdir(args.rounds_log_dir):
        d = os.path.join(args.rounds_log_dir, file)
        if os.path.isdir(d):
            # 各ラウンドのログディレクトリ
            adv_path = os.path.join(d, adv_file_name)
            exportstates_path = os.path.join(d, exportstates_file_name)
            exporttrans_path = os.path.join(d, exporttrans_file_name)
            exportlabels_path = os.path.join(d, exportlabels_file_name)
            if os.path.exists(adv_path) and os.path.exists(exportstates_path) and os.path.exists(exporttrans_path) and os.path.exists(exportlabels_path):
                sb = StrategyBridge(adv_path, exportstates_path, exporttrans_path, exportlabels_path)
                smc : StatisticalModelChecker = StatisticalModelChecker(sul, sb, args.prop_path, 0, None, num_exec=5000, returnCEX=False)
                smc.run()
                print(f'SUT value by SMC at {d}: {smc.exec_count_satisfication / smc.num_exec} (satisfication: {smc.exec_count_satisfication}, total: {smc.num_exec})')
                smc_log_path = os.path.join(d, "smc.log")
                with open(smc_log_path, 'w+') as f:
                    f.write(f'{smc.exec_count_satisfication / smc.num_exec}\n{smc.exec_count_satisfication}\n{smc.num_exec}')
    print("Finish evaluation of each round")

if __name__ == "__main__":
    main()