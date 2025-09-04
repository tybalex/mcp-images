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

# Clone tableau-mcp repository if building tableau dockerfile
if [[ -f "Dockerfile.tableau" ]]; then
    echo "Cloning tableau-mcp repository for tableau build..."
    rm -rf tableau-mcp
    git clone https://github.com/tableau/tableau-mcp.git
fi

for f in $(ls Dockerfile.*); do
    echo Building $f
    
    if [[ "$f" == "Dockerfile.tableau" ]]; then
        # Special handling for tableau: use tableau-mcp as context
        docker build -t ${repo}mcp-images-${f#Dockerfile.}:main $push -f $f ./tableau-mcp
    else
        # Normal handling: use current directory as context
        docker build -t ${repo}mcp-images-${f#Dockerfile.}:main $push -f $f .
    fi
done

# Clean up tableau-mcp directory if it was created
if [[ -d "tableau-mcp" ]]; then
    echo "Cleaning up tableau-mcp directory..."
    rm -rf tableau-mcp
fi
