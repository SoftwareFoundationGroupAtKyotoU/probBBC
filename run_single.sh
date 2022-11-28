#!/bin/bash -u

mkdir results
touch results/results.log

python3 main.py --model-name slot_machine_r5 --prop-name slot --output-dir results-test --min-rounds 10 --max-rounds 25 --save-files-for-each-round --target-unambiguity 0.9 --debug 
mv "results" "results-mqtt"

curl -X POST -H 'Content-type: application/json' --data '{"text":"Procyon: run single finished."}' https://hooks.slack.com/services/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
