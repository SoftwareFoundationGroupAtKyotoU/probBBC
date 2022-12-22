#!/bin/bash -u

for i in `seq 1 10`
do
  python3 eval_each_round.py --rounds-log-dir "results-second13-$i/rounds" --model-path ../AALpy/DotModels/MDPs/second_grid.dot --prop-path second_grid.ltl > results-second13-$i/rounds/eval.txt
done
