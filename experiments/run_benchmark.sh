#!/bin/bash -u

# =================
# run_benchmark.sh
# =================
#
# Description:
#  Script to execute a benchmark experiment using probabilistic black box checking
#
# Usage:
# ./run_benchmark.sh [benchmark_name] [spec]
# ./run_benchmark.sh [benchmark_name] [spec] [min_rounds] [max_rounds]
#

if (($# < 2)); then
    echo 'Usage: ./run_benchmark.sh [benchmark_name] [spec]'
    echo 'Usage: ./run_benchmark.sh [benchmark_name] [spec] [min_rounds] [max_rounds] [target_unambiguity]'
else
    BENCHMARK_PATH="../benchmarks/$1/$1.dot"
    SPEC_PATH="../benchmarks/$1/$2.props"
fi

readonly MIN_ROUNDS=${3:-70}
readonly MAX_ROUNDS=${4:-100}
readonly TARGET_UNAMBIGUITY=${5:-0.99}

rm -rf results

mkdir results
touch results/results.log

python3 ../src/main.py \
  --model-file $BENCHMARK_PATH \
  --prop-file $SPEC_PATH \
  --output-dir results \
  --min-rounds $MIN_ROUNDS \
  --max-rounds $MAX_ROUNDS \
  --save-files-for-each-round \
  --target-unambiguity $TARGET_UNAMBIGUITY \
  --debug > results/results.log

