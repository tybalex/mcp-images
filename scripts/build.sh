#!/bin/bash
set -e

cd $(dirname $0)/..

for f in $(ls Dockerfile.*); do
    echo Building $f
    docker build -t ghcr.io/obot-platform/${f#Dockerfile.}-mcp:latest -f $f .
done
