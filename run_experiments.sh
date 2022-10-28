#!/bin/bash -u

for i in `seq 1 5`
do
  python3 main.py slot_machine slot &> results/results.log
  mv "results" "results-$i"
done