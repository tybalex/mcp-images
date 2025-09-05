#!/bin/bash
set -e

cd $(dirname $0)/..

push=""
if [[ -n "${PUSH}" ]]; then
    push="--push"
fi

if [[ -n "${BASE_REPO}" ]]; then
    repo=${BASE_REPO}/
fi


for f in $(ls Dockerfile.*); do
    echo Building $f
    docker build -t ${repo}mcp-images-${f#Dockerfile.}:main $push -f $f .
done
