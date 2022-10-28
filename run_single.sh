#!/bin/bash -u

mkdir results
touch results/results.log

python3 main.py mqtt mqtt &> results/results.log
mv "results" "results-mqtt"

curl -X POST -H 'Content-type: application/json' --data '{"text":"Procyon: run single finished."}' https://hooks.slack.com/services/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
