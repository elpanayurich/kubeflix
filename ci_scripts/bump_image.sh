#!/bin/bash

# Updated list to include Payments (Option 4)
if [ $# -ne 1 ];then
    echo -e "List of possible images to bump:\n  1 - search\n  2 - frontend\n  3 - auth\n  4 - payments"
    echo "Usage ./bump_image.sh [MICRO_TO_BUMP_NUMBER_FROM_LIST]"
    exit 1
fi

set -x

declare -A micros
micros["1"]="search"
micros["2"]="frontend"
micros["3"]="auth"
micros["4"]="payments"

declare -A src_paths
src_paths["1"]="../search"
src_paths["2"]="../frontend"
src_paths["3"]="../auth"
src_paths["4"]="../payments"

if [[ "$1" -gt ${#micros[@]} || "$1" -lt 1 ]]; then
    echo "Input not valid"
    exit 1
fi

micro_name=${micros[$1]}
build_context=${src_paths[$1]}

# Find the manifest file containing the image (YAML)
micro_file=$(grep -lr "image: kubeflix-$micro_name" ../ | head -n 1)

if [ -z "$micro_file" ]; then
    echo "Error: Could not find a manifest file containing image: kubeflix-$micro_name"
    exit 1
fi

# Extract current version (e.g., v1)
version=$(grep -oP "image: kubeflix-$micro_name:\Kv[0-9]+" "$micro_file" | head -n 1)
# Calculate next version (v1 -> v2)
new_version="v$(( ${version#v} + 1 ))"

echo "Bumping $micro_name from $version to $new_version in $micro_file"

# Apply change to YAML file
sed -i "s|image: kubeflix-$micro_name:${version}|image: kubeflix-$micro_name:${new_version}|g" "$micro_file"

# Connect to Minikube's Docker daemon
eval $(minikube docker-env)

echo "Building image inside minikube: $build_context"
cd "$build_context"
docker build -t "kubeflix-$micro_name:$new_version" .
cd -

echo "Updating the cluster"
kubectl apply -f "$micro_file"