#!/bin/bash

if [ $# -ne 1 ];then
    echo -e "List of possible images to bump:\n  1 - search\n  2 - frontend"
    echo "Usage ./bump_image.sh [MICRO_TO_BUMP_NUMBER_FROM_LIST]"
    exit 1
fi

set -x

declare -A micros
micros["1"]="search"
micros["2"]="frontend"

declare -A src_paths
src_paths["1"]="../search"
src_paths["2"]="../frontend"

if [[ "$1" -gt ${#micros[@]} || "$1" -lt 1 ]]; then
    echo "Input not valid"
    exit 1
fi

micro_name=${micros[$1]}
build_context=${src_paths[$1]}

micro_file=$(grep -lr "image: kubeflix-$micro_name" ../)

if [ -z "$micro_file" ]; then
    echo "Error: Could not find a manifest file containing image: kubeflix-$micro_name"
    exit 1
fi

version=$(grep -oP "image: kubeflix-$micro_name:\Kv[0-9]+" "$micro_file")
new_version="v$(( ${version#v} + 1 ))"

echo "Bumping $micro_name from $version to $new_version in $micro_file"

sed -i "s|image: kubeflix-$micro_name:${version}|image: kubeflix-$micro_name:${new_version}|g" "$micro_file"

eval $(minikube docker-env)

echo "Building image inside minikube: $build_context"
docker build -t "kubeflix-$micro_name:$new_version" -f "$build_context/Dockerfile" ..

echo "Updating the cluster"
kubectl apply -f "$micro_file"