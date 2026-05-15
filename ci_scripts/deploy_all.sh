#!/bin/bash

apply_with_retry() {
    local file=$1
    local max_attempts=10
    local attempt=1
    until kubectl apply -f "$file" || [ $attempt -eq $max_attempts ]; do
        echo "Esperando webhook... ($attempt)"
        sleep 3
        ((attempt++))
    done
}

set -x
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 1. LIMPIEZA DE PROCESOS (NO de datos)
echo "Reiniciando entorno conservando datos..."
minikube delete
pkill -f "minikube mount" || true

# 2. PREPARACIÓN DE CARPETA (SIN BORRAR EL CONTENIDO)
if [ ! -d "$PROJECT_ROOT/auth/data/postgres-db" ]; then
    echo "Carpeta no encontrada, creando nueva..."
    mkdir -p "$PROJECT_ROOT/auth/data/postgres-db"
fi

# Aseguramos permisos siempre, por si acaso, pero SIN borrar archivos
sudo chown -R 999:999 "$PROJECT_ROOT/auth/data/postgres-db"
sudo chmod -R 777 "$PROJECT_ROOT/auth/data/postgres-db"

# 3. ARRANQUE NATIVO
minikube start --driver=docker --mount --mount-string="$PROJECT_ROOT/auth/data/postgres-db:/minikube-data"

# 4. FIX PERMISOS INTERNOS (Para que Minikube deje entrar a Postgres)
# Esto soluciona el 'Permission Denied' que vimos en el ssh
minikube ssh "sudo chown -R 999:999 /minikube-data && sudo chmod -R 777 /minikube-data"

eval $(minikube docker-env)
minikube addons enable ingress

# 5. BUILDS (Optimizados)
micros=("search" "frontend" "auth")
for micro in "${micros[@]}"; do
    micro_file=$(grep -rl "image: kubeflix-${micro}" "$PROJECT_ROOT" | head -n 1)
    [ -z "$micro_file" ] && continue
    version=$(grep -oP "image: kubeflix-${micro}:\Kv[0-9]+" "$micro_file" | head -n 1)
    if ! docker image inspect "kubeflix-${micro}:${version}" > /dev/null 2>&1; then
        docker build -t "kubeflix-${micro}:${version}" "$PROJECT_ROOT/$micro"
    fi
done

# 6. ESPERA NGINX
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s

# 7. DESPLIEGUE ORDENADO
# Primero el PV para que cuando llegue el PVC, se casen al instante
kubectl apply -f "$PROJECT_ROOT/auth/k8s/postgres.yaml"
sleep 5 # Pausa para que el PV pase a estado 'Available'

kubectl apply -f "$PROJECT_ROOT/auth/k8s/auth.yaml"
apply_with_retry "$PROJECT_ROOT/auth/k8s/auth-ingress.yaml"

# Resto de la app
kubectl apply -f "$PROJECT_ROOT/search/k8s/"
kubectl apply -f "$PROJECT_ROOT/frontend/k8s/"

kubectl create secret generic search-api-secret --from-literal=admin-pass="Admin007" --dry-run=client -o yaml | kubectl apply -f -

echo "--- INFRAESTRUCTURA DESPLEGADA ---"