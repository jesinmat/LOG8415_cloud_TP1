#!/bin/bash

function run() {
    if [[ -z "$AWS_URL" ]]; then
        echo "Set AWS_URL first!"
        return 1
    fi

    OutDir="$PWD/output/"

    docker run --rm -e AWS_URL -v ~/.aws/:/root/.aws/ -v "$OutDir":/output/ aws-loadtester
}

run
