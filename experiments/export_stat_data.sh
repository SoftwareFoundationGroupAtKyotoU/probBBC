#!/bin/bash -u

ROUNDS_STAT_FILENAME=`basename $1`
ROUNDS_STAT="${ROUNDS_STAT_FILENAME%.*}"
PBR_ROUNDS_FILENAME=`basename $2`
PBR_ROUNDS="${PBR_ROUNDS_FILENAME%.*}"
OUTPUT_FILE=$ROUNDS_STAT-$PBR_ROUNDS

rm -f $OUTPUT_FILE
touch $OUTPUT_FILE

echo -e "Rounds\tProbability by our method\tRounds'\tNum queries\tNum steps\tProbability by previous method" > $OUTPUT_FILE
cat $1 >> $OUTPUT_FILE
grep -E '(Probability for property, totalNrSteps :) (.*)' $2 | sed -E 's/(Probability for property, totalNrSteps :) ([0-9.E+-]+),([0-9.]+)/\t\t\t\t\3\t\2/g' >> $OUTPUT_FILE


