#!/bin/bash
# Customer Success FTE - Kubernetes Deployment Script
# Usage: ./deploy.sh [namespace]

set -e

NAMESPACE="${1:-customer-success}"
IMAGE_NAME="customer-success-fte"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "============================================="
echo "  Customer Success FTE - Kubernetes Deploy"
echo "============================================="
echo ""
echo "Namespace: $NAMESPACE"
echo "Image: $IMAGE_NAME:$IMAGE_TAG"
echo ""

# Step 1: Build Docker image
echo "Step 1: Building Docker image..."
docker build -f production/Dockerfile -t $IMAGE_NAME:$IMAGE_TAG .
echo "✓ Docker image built"
echo ""

# Step 2: Create namespace
echo "Step 2: Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
echo "✓ Namespace created/verified"
echo ""

# Step 3: Apply ConfigMap and Secrets
echo "Step 3: Applying ConfigMap and Secrets..."
kubectl apply -f production/k8s/configmap.yaml -n $NAMESPACE
kubectl apply -f production/k8s/secrets.yaml -n $NAMESPACE
echo "✓ ConfigMap and Secrets applied"
echo ""

# Step 4: Apply RBAC
echo "Step 4: Applying RBAC..."
kubectl apply -f production/k8s/serviceaccount.yaml -n $NAMESPACE
echo "✓ ServiceAccount and RoleBinding applied"
echo ""

# Step 5: Apply Deployments
echo "Step 5: Applying Deployments..."
kubectl apply -f production/k8s/api-deployment.yaml -n $NAMESPACE
kubectl apply -f production/k8s/worker-deployment.yaml -n $NAMESPACE
echo "✓ Deployments applied"
echo ""

# Step 6: Apply Ingress
echo "Step 6: Applying Ingress..."
kubectl apply -f production/k8s/ingress.yaml -n $NAMESPACE
echo "✓ Ingress applied"
echo ""

# Step 7: Apply Monitoring
echo "Step 7: Applying Monitoring..."
kubectl apply -f production/k8s/monitoring.yaml -n $NAMESPACE
echo "✓ ServiceMonitor and Alerts applied"
echo ""

# Step 8: Wait for rollout
echo "Step 8: Waiting for rollout..."
kubectl rollout status deployment/customer-success-api -n $NAMESPACE --timeout=300s
kubectl rollout status deployment/customer-success-worker -n $NAMESPACE --timeout=300s
echo "✓ Rollout complete"
echo ""

# Step 9: Show status
echo "Step 9: Deployment Status"
echo "-------------------------------------------"
kubectl get deployments -n $NAMESPACE
echo ""
kubectl get pods -n $NAMESPACE
echo ""
kubectl get services -n $NAMESPACE
echo ""

# Step 10: Show ingress
echo "Ingress Configuration:"
kubectl get ingress -n $NAMESPACE
echo ""

echo "============================================="
echo "  Deployment Complete!"
echo "============================================="
echo ""
echo "Next steps:"
echo "1. Check logs: kubectl logs -f deployment/customer-success-api -n $NAMESPACE"
echo "2. Test health: kubectl port-forward svc/customer-success-api-service 8000:80 -n $NAMESPACE"
echo "3. View dashboard: kubectl get all -n $NAMESPACE"
echo ""
