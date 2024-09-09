from aalpy.SULs import MdpSUL
from aalpy.oracles import RandomWalkEqOracle
from aalpy.learning_algs import run_stochastic_Lstar
from aalpy.utils import visualize_automaton, generate_random_mdp


def random_mdp_lean(
    num_states, input_len, n_c=20, n_resample=1000, min_rounds=10, max_rounds=1000
):
    mdp, input_alphabet = generate_random_mdp(num_states, input_len)
    visualize_automaton(mdp, path="sul")
    sul = MdpSUL(mdp)
    eq_oracle = RandomWalkEqOracle(
        input_alphabet, sul=sul, num_steps=5000, reset_prob=0.11, reset_after_cex=True
    )

    learned_mdp = run_stochastic_Lstar(
        input_alphabet,
        sul,
        eq_oracle,
        n_c=n_c,
        n_resample=n_resample,
        min_rounds=min_rounds,
        max_rounds=max_rounds,
    )

    return learned_mdp


learned = random_mdp_lean(10, 5)
visualize_automaton(learned)
