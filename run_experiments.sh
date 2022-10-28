#!/bin/bash -u

for i in `seq 1 5`
do
  mkdir results
  touch results/results.log
  python3 main.py &> results/results.log
  mv "results" "results-$i"
done
