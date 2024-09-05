"""
Learning faulty coffee machine that can be found in Chapter 5 and Chapter 7 of Martin's Tappler PhD thesis.
:return learned MDP
"""

from aalpy.SULs import MdpSUL
from aalpy.oracles import RandomWalkEqOracle
from aalpy.learning_algs import run_stochastic_Lstar
from aalpy.utils import visualize_automaton, get_weird_coffee_machine_MDP

mdp = get_weird_coffee_machine_MDP()
visualize_automaton(mdp, path="sul")

input_alphabet = mdp.get_input_alphabet()
sul = MdpSUL(mdp)

eq_oracle = RandomWalkEqOracle(
    input_alphabet, sul=sul, num_steps=4000, reset_prob=0.11, reset_after_cex=True
)

learned_mdp = run_stochastic_Lstar(
    input_alphabet,
    sul,
    eq_oracle,
    n_c=20,
    n_resample=1000,
    min_rounds=10,
    max_rounds=500,
    strategy="normal",
    cex_processing="rs",
    samples_cex_strategy="bfs",
    automaton_type="smm",
)

visualize_automaton(learned_mdp)
