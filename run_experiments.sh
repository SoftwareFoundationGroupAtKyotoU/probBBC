#!/bin/bash -u

for i in `seq 1 10`
do
  mkdir results
  touch results/results.log
  python3 main.py --model-name first_grid --prop-name first_grid --output-dir results --min-rounds 10 --max-rounds 40 --save-files-for-each-round --target-unambiguity 0.9 --debug &> results/results.log
  mv "results" "results-grid10-$i"
done
