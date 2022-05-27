from aalpy.utils import load_automaton_from_file, save_automaton_to_file, visualize_automaton, generate_random_dfa
from aalpy.SULs import DfaSUL
from aalpy.oracles import RandomWalkEqOracle
from aalpy.learning_algs import run_Lstar

# randomly generate a dfa
random_dfa = generate_random_dfa(alphabet=[1,2,3,4,5],num_states=20, num_accepting_states=8)
big_random_dfa = generate_random_dfa(alphabet=[1,2,3,4,5],num_states=2000, num_accepting_states=500)

# get input alphabet of the automaton
alphabet = random_dfa.get_input_alphabet()

# loaded or randomly generated automata are considered as BLACK-BOX that is queried
# learning algorithm has no knowledge about its structure
# create a SUL instance for the automaton/system under learning
sul = DfaSUL(random_dfa)

# define the equivalence oracle
eq_oracle = RandomWalkEqOracle(alphabet, sul, num_steps=5000, reset_prob=0.09)

# start learning
learned_dfa = run_Lstar(alphabet, sul, eq_oracle, automaton_type='dfa')

# save automaton to file and visualize it
save_automaton_to_file(learned_dfa, path='Learned_Automaton', file_type='dot')

# visualize automaton
visualize_automaton(learned_dfa)
# or just print its DOT representation
print(learned_dfa)
