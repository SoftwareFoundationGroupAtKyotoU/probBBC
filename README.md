ProbBBC
=======
[![License: BSD-2](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](./LICENSE)

ProbBBC is a prototype implementation of the Probabilistic Black-Box Checking (ProbBBC) method for Markov decision processes (MDPs) using an L*-style learning. The package includes a patch file to modify AALpy to support reading the observation table from ProbBBC.

The package provides a command-line interface, which takes as input an MDP model in the DOT format, a property to be checked, and the path to the PRISM model checker. ProbBBC estimates the maximum satisfaction probability of the given specification.

Usage
-----
To use ProbBBC, run the main.py script with the required arguments, as shown below.

```
python3 main.py \
    --model-file [MODEL_FILE] \
    --prop-file [PROP_FILE] \
    --prism-path [PRISM_PATH] \
    [OPTIONS]
```
### Required arguments
- `[MODEL_FILE]`: the path to the MDP model file in the DOT format
    - Example: `benchmarks/first_grid/first_grid.dot`
- `[PROP_FILE]`: the path to the property file
    - Example: `benchmarks/first_grid/first_grid10.props`
- `[PRISM_PATH]`: the path to the PRISM model checker

### Optional arguments:
- `-h, --help`
    show help messages and exit
- `--output-dir [OUTPUT_DIR]`
                      the name of the output directory (default value: 'results')
- `--save-files-for-each-round`
                      save files(model, hypothesis, strategy) for each rounds
- `--min-rounds [MIN_ROUNDS]`
                      the minimum number of learning rounds of L*mdp (default value: 20)
- `--max-rounds [MAX_ROUNDS]`
                      if learning_rounds >= max_rounds, L*mdp learning will stop (default value: 240)
- `--l-star-mdp-strategy [STRATEGY]`
                       either one of ['classic', 'normal', 'chi2'] or an object implementing DifferenceChecker class. The default value is 'normal'. Classic strategy is the one presented in the seed paper, 'normal' is the updated version, and chi2 is based on chi squared.
- `--n-cutoff [N_C]`      
                      Cutoff for a cell to be considered complete (default value is 20), only used with 'classic' strategy.
- `--n-resample [N_RESAMPLE]`
                      Resampling size (default value is 100), only used with 'classic' L*mdp strategy.
- `--target-unambiguity [TARGET_UNAMBIGUITY]`
                       Target unambiguity value of L*mdp (default value is 0.99).
- `--eq-num-steps [EQ_NUM_STEPS]`
                      Number of steps to be performed by equivalence oracle.
- `--smc-max-exec [SMC_MAX_EXEC]`
                      Maximum number of executions by SMC (default value is 5000).
- `--only-classical-equivalence-testing`
                      Skip the strategy guided equivalence testing using SMC.
- `--smc-statistical-test-bound [TEST_BOUND]`
                      Statistical test bound of difference check between SMC and model-checking (default value is 0.025).
- `-v, --verbose, --debug`
                      Output debug messages.

Set up
-------

The following shows the installation with [venv](https://docs.python.org/3/library/venv.html). In what follows, we assume the environment is installed under `~/probBBC/.venv`. We also assume that [PRISM](https://www.prismmodelchecker.org/) is already installed.

### Set up venv

First, we configure and activate venv. One can also use an existing environment. 

```shell
## Make an environment
python3 -m venv .venv
## Activate it. If you use a shell other than bash, you need to use another script, such as .venv/bin/activate.fish
. .venv/bin/activate
```

### Build and install Spot

ProbBBC depends on [Spot](https://spot.lre.epita.fr/) for handling LTL formulas. The installation of Spot is as follows.

```shell
## Download the source code of spot
wget http://www.lrde.epita.fr/dload/spot/spot-2.11.5.tar.gz
tar xvf spot-2.11.5.tar.gz
cd spot-2.11.5
# Specify appropriate CPU/OS for your environment
./configure --prefix "$OLDPWD/.venv/" --build=x86_64-unknown-linux-gnu --host=x86_64-unknown-linux-gnu
# Build and install Spot
make -j8 && make install
```

### Install (modified version of) AALpy

In order to interact with the observation table in, what we call, the validation phase, we need a modified version of AALpy. The following shows how to install it.

1. Clone the [github repository](https://github.com/DES-Lab/AALpy) of AALpy
2. Modify the [src file](https://github.com/DES-Lab/AALpy/blob/master/aalpy/learning_algs/stochastic/StochasticLStar.py) of L-star MDP learning as follows
```
108:    # This way all steps from eq. oracle will be added to the tree
109:    eq_oracle.sul = stochastic_teacher.sul
110:
111:    observation_table = SamplingBasedObservationTable(input_alphabet, automaton_type,
112:                                                      stochastic_teacher, compatibility_checker=compatibility_checker,
113:                                                      strategy=strategy,
114:                                                      cex_processing=cex_processing)
115:    # ===== BEGIN OF MODIFICATION ===
116:    eq_oracle.observation_table = observation_table
117:    # ===== END OF MODIFICATION =====
118:
119:    start_time = time.time()
120:    eq_query_time = 0
```

You can automatically apply this modification by executing the following at the root directory of AALpy.

```
patch -p1 < /path/to/probBBC/aalpy.patch
```

3. For manual installation, install `pydot`
```
python3 -m pip install pydot
```
4. Install AALpy (modified version). Run the following command at root directory of AALpy repository. (Maybe you need to add `sudo`)
```
python3 setup.py install
```



### Install other packages

Other packages can be automatically installed as follows.

```shell
pip install -r requirements.txt
```
## Benchmarks

For each benchmark, assign appropriate values for required arguments (`--model-file`, `--prop-file`, `--prism-path`).
If you want to run ProbBBC without strategy-guided equivalence testing (for example, for evaluation), please also add `--only-classical-equivalence-testing`.

### Optional arguments for each benchmark
| Benchmark                           | `--min-rounds` | `--max-rounds` | `--target-unambiguity` | Other options                 |
| ----------------------------------- | -------------- | -------------- | ---------------------- | ----------------------------- |
| TCP                                 | 100            | 120            | 0.99                   | `--save-files-for-each-round` |
| MQTT                                | 100            | 120            | 0.99                   | `--save-files-for-each-round` |
| Slot machine                        | 110            | 120            | 0.99                   | `--save-files-for-each-round` |
| Slot machine with supressed outputs | 110            | 120            | 0.99                   | `--save-files-for-each-round` |
| Shared coin consensus               | 100            | 120            | 0.99                   | `--save-files-for-each-round` |
| First gridworld                     | 100            | 120            | 0.99                   | `--save-files-for-each-round` |
| Second gridworld                    | 120            | 130            | 0.99                   | `--save-files-for-each-round` |


### Example
```
python3 src/main.py --model-file benchmarks/mqtt/mqtt.dot --prop-file benchmarks/mqtt/mqtt.props --prism-path /usr/bin/prism --output-dir results --min-rounds 100 --max-rounds 120 --save-files-for-each-round --target-unambiguity 0.99
```

### Formatter
Please run `ruff check && ruff format` and apply the changes before making commit.

### License
This software is released under the BSD-2 License. See LICENSE file for details.
