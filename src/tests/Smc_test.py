import unittest
import spot

from ..StrategyBridge import StrategyBridge
from ..Smc import StatisticalModelChecker
from aalpy.SULs import MdpSUL
from aalpy.utils import load_automaton_from_file


def custom_print(aut):
    bdict = aut.get_dict()
    print("Acceptance:", aut.get_acceptance())
    print("Number of sets:", aut.num_sets())
    print("Number of states: ", aut.num_states())
    print("Initial states: ", aut.get_init_state_number())
    print("Atomic propositions:", end="")
    for ap in aut.ap():
        print(" ", ap, " (=", bdict.varnum(ap), ")", sep="", end="")
    print()
    # Templated methods are not available in Python, so we cannot
    # retrieve/attach arbitrary objects from/to the automaton.  However the
    # Python bindings have get_name() and set_name() to access the
    # "automaton-name" property.
    name = aut.get_name()
    if name:
        print("Name: ", name)
    print("Deterministic:", aut.prop_universal() and aut.is_existential())
    print("Unambiguous:", aut.prop_unambiguous())
    print("State-Based Acc:", aut.prop_state_acc())
    print("Terminal:", aut.prop_terminal())
    print("Weak:", aut.prop_weak())
    print("Inherently Weak:", aut.prop_inherently_weak())
    print("Stutter Invariant:", aut.prop_stutter_invariant())

    for s in range(0, aut.num_states()):
        print("State {}:".format(s))
        for t in aut.out(s):
            print("  edge({} -> {})".format(t.src, t.dst))
            # bdd_print_formula() is designed to print on a std::ostream, and
            # is inconvenient to use in Python.  Instead we use
            # bdd_format_formula() as this simply returns a string.
            print("    label =", spot.bdd_format_formula(bdict, t.cond))
            print("    acc sets =", t.acc)


class SMCTestCase(unittest.TestCase):
    def test_initialize(self):
        example = "shared_coin"
        mdp = load_automaton_from_file(
            f"/Users/bo40/workspace/python/AALpy/DotModels/MDPs/{example}.dot",
            automaton_type="mdp",
        )
        sul = MdpSUL(mdp)
        sample_prism_model = "/Users/bo40/workspace/python/mc_exp_sample.prism"
        sample_prism_adv = "/Users/bo40/workspace/python/adv_sample.tra"
        sb = StrategyBridge(sample_prism_adv, sample_prism_model)

        spec_path = "/Users/bo40/workspace/python/sandbox/shared_coin.ltl"
        smc = StatisticalModelChecker(sul, sb, spec_path)

        custom_print(smc.spec_monitor)

        smc.reset_sut()
        # XXX: unused
        # ret = smc.one_step()
        smc.step_monitor(smc.current_output)
        # XXX: unused
        # ret = smc.one_step()
        smc.step_monitor(smc.current_output)
        # XXX: unused
        # ret = smc.one_step()
        smc.step_monitor(smc.current_output)

        0

    def test_smc_run(self):
        example = "shared_coin"
        mdp = load_automaton_from_file(
            f"/Users/bo40/workspace/python/AALpy/DotModels/MDPs/{example}.dot",
            automaton_type="mdp",
        )
        sul = MdpSUL(mdp)
        sample_prism_model = "/Users/bo40/workspace/python/mc_exp_sample.prism"
        sample_prism_adv = "/Users/bo40/workspace/python/adv_sample.tra"
        sb = StrategyBridge(sample_prism_adv, sample_prism_model)

        spec_path = "/Users/bo40/workspace/python/sandbox/shared_coin.ltl"
        smc = StatisticalModelChecker(sul, sb, spec_path, num_exec=5000)

        smc.run()
        print(f"sat : {smc.exec_count_satisfication}")
        print(f"vio : {smc.exec_count_violation}")
        ret = smc.hypothesis_testing(0.29, "two-sided")
        print(f"pvalue : {ret.pvalue}")
        0


if __name__ == "__main__":
    unittest.main()
