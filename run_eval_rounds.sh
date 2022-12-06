#!/bin/bash -u

for i in `seq 1 10`
do
  python3 eval_each_round.py --rounds-log-dir "results-grid10-$i/rounds" --model-path ../AALpy/DotModels/MDPs/first_grid.dot --prop-path first_grid.ltl > results-grid10-$i/rounds/eval.txt
done
