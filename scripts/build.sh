#!/bin/bash
set -e

cd $(dirname $0)/..

push=""
if [[ -n "${PUSH}" ]]; then
    push="--push"
fi

repo="ghcr.io/obot-platform/mcp-images"
if [[ -n "${BASE_REPO}" ]]; then
    repo=${BASE_REPO}
fi


for f in $(ls Dockerfile.*); do
    echo Building $f
    docker build -t $repo/${f#Dockerfile.}:latest $push -f $f .
done
