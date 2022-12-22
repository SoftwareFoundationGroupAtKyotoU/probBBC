#!/bin/bash -u

for i in `seq 1 10`
do
  mkdir results
  touch results/results.log
  python3 main.py --model-name slot_machine_reduce_v2 --prop-name slot --output-dir results --min-rounds 100 --max-rounds 120 --save-files-for-each-round --target-unambiguity 0.99 --debug &> results/results.log
  mv "results" "results-slot_reduce_v2-14-$i"
done
