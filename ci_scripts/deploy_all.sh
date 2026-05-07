#!/bin/bash

set -x

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

minikube start --driver=docker
eval $(minikube docker-env)

minikube addons enable ingress

kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s

kubectl wait --namespace ingress-nginx \
  --for=jsonpath='{.subsets[0].addresses[0].ip}' \
  endpoints ingress-nginx-controller-admission \
  --timeout=60s

kubectl apply -f "$PROJECT_ROOT/search/k8s/postgres.yaml"
kubectl apply -f "$PROJECT_ROOT/search/k8s/search.yaml"
kubectl apply -f "$PROJECT_ROOT/frontend/k8s/"

kubectl create secret generic search-api-secret \
  --from-literal=admin-pass="Admin007" \
  --dry-run=client -o yaml | kubectl apply -f -

micros=("search" "frontend")

for micro in "${micros[@]}"; do
    micro_file=$(grep -rl "image: kubeflix-${micro}" "$PROJECT_ROOT" | head -n 1)

    if [ -z "$micro_file" ]; then
        continue
    fi

    version=$(grep -oP "image: kubeflix-${micro}:\Kv[0-9]+" "$micro_file" | head -n 1)

    if [ -z "$version" ]; then
        continue
    fi

    if ! docker image inspect "kubeflix-${micro}:${version}" > /dev/null 2>&1; then
        docker build -t "kubeflix-${micro}:${version}" "$PROJECT_ROOT/$micro"
    fi
done