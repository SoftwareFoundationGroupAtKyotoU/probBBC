#!/bin/bash -u

BENCH=grid10
DATE=20221207

EVAL_ROUNDS_FILE=eval.txt

DATAFOLDER=results-$DATE-$BENCH/results-$BENCH
ROUNDS_EVAL_OUTPUT=stat_${BENCH}_${DATE}_eval.txt
ROUNDS_STEP_OUTPUT=stat_${BENCH}_${DATE}_step.txt
ROUNDS_STAT_OUTPUT=stat_${BENCH}_${DATE}.txt

touch $ROUNDS_EVAL_OUTPUT
touch $ROUNDS_STEP_OUTPUT
touch $ROUNDS_STAT_OUTPUT

for i in `seq 1 50`
do
  grep -E 'SUT value by SMC at .*\/r([0-9]+): ([0-9.]+) .*' $DATAFOLDER-$i/rounds/$EVAL_ROUNDS_FILE | sed -E "s/SUT value by SMC at .*\/r([0-9]+): ([0-9.]+) .*/$i-\1\t\2/g" >> $ROUNDS_EVAL_OUTPUT
  round_num=`grep -E 'SUT value by SMC at .*\/r([0-9]+): ([0-9.]+) .*' $DATAFOLDER-$i/rounds/$EVAL_ROUNDS_FILE | sed -E 's/SUT value by SMC at .*\/r([0-9]+): ([0-9.]+) .*/\1\t\2/g' | wc -l`
  grep -E 'Round information : {.*}' $DATAFOLDER-$i/results.log | sed -E "s/Round information : \{'learning_rounds': ([0-9]+).*'sul\.num_queries': ([0-9]+).*'sul\.num_steps': ([0-9]+).*\}/$i-\1\t\2\t\3/g" | tail -n $round_num >> $ROUNDS_STEP_OUTPUT
  paste $ROUNDS_EVAL_OUTPUT $ROUNDS_STEP_OUTPUT > $ROUNDS_STAT_OUTPUT
done

# for i in `seq 1 50`
# do
#   grep -E 'Round information : {.*}' $DATAFOLDER-$i/results.log | sed -E "s/Round information : \{'learning_rounds': ([0-9]+).*'sul\.num_queries': ([0-9]+).*'sul\.num_steps': ([0-9]+).*\}/\1\t\2\t\3/g"
# done
