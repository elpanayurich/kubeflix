#!/bin/bash

# Actualizamos la lista para incluir el Auth (Opción 3)
if [ $# -ne 1 ];then
    echo -e "List of possible images to bump:\n  1 - search\n  2 - frontend\n  3 - auth"
    echo "Usage ./bump_image.sh [MICRO_TO_BUMP_NUMBER_FROM_LIST]"
    exit 1
fi

set -x

declare -A micros
micros["1"]="search"
micros["2"]="frontend"
micros["3"]="auth" # <-- Añadido

declare -A src_paths
src_paths["1"]="../search"
src_paths["2"]="../frontend"
src_paths["3"]="../auth" # <-- Añadido

if [[ "$1" -gt ${#micros[@]} || "$1" -lt 1 ]]; then
    echo "Input not valid"
    exit 1
fi

micro_name=${micros[$1]}
build_context=${src_paths[$1]}

# Buscamos el archivo que contiene la imagen (YAML)
micro_file=$(grep -lr "image: kubeflix-$micro_name" ../ | head -n 1)

if [ -z "$micro_file" ]; then
    echo "Error: Could not find a manifest file containing image: kubeflix-$micro_name"
    exit 1
fi

# Extraemos la versión actual (ej: v1)
version=$(grep -oP "image: kubeflix-$micro_name:\Kv[0-9]+" "$micro_file" | head -n 1)
# Calculamos la siguiente (v1 -> v2)
new_version="v$(( ${version#v} + 1 ))"

echo "Bumping $micro_name from $version to $new_version in $micro_file"

# Aplicamos el cambio en el archivo YAML
sed -i "s|image: kubeflix-$micro_name:${version}|image: kubeflix-$micro_name:${new_version}|g" "$micro_file"

# Conectamos con el demonio de Docker de Minikube
eval $(minikube docker-env)

echo "Building image inside minikube: $build_context"
cd "$build_context"
# Corregido: Usamos la variable $micro_name para que el tag sea correcto
docker build -t "kubeflix-$micro_name:$new_version" .
cd -

echo "Updating the cluster"
kubectl apply -f "$micro_file"