# Customer Success FTE - Kubernetes Deployment

## Prerequisites

- Kubernetes cluster 1.25+ (GKE, EKS, AKS, or local with minikube/kind)
- kubectl configured
- Docker for building images
- NGINX Ingress Controller (for ingress)
- cert-manager (for SSL certificates)
- Prometheus Operator (for monitoring)

## Quick Start

### 1. Build and Deploy

```bash
# Set image tag
export IMAGE_TAG=v1.0.0

# Run deployment script
./production/k8s/deploy.sh

# Or deploy manually
docker build -f production/Dockerfile -t customer-success-fte:$IMAGE_TAG .
docker push customer-success-fte:$IMAGE_TAG  # Push to your registry

# Apply manifests
kubectl apply -f production/k8s/namespace.yaml
kubectl apply -f production/k8s/configmap.yaml
kubectl apply -f production/k8s/secrets.yaml
kubectl apply -f production/k8s/serviceaccount.yaml
kubectl apply -f production/k8s/api-deployment.yaml
kubectl apply -f production/k8s/worker-deployment.yaml
kubectl apply -f production/k8s/ingress.yaml
kubectl apply -f production/k8s/monitoring.yaml
```

### 2. Configure Secrets

Before deploying, update the secrets:

```bash
# Edit secrets file
vim production/k8s/secrets.yaml

# Or create with kubectl
kubectl create secret generic customer-success-secrets \
  --from-literal=DB_PASSWORD='your-password' \
  --from-literal=OPENAI_API_KEY='sk-...' \
  --namespace=customer-success
```

### 3. Verify Deployment

```bash
# Check pods
kubectl get pods -n customer-success

# Check services
kubectl get services -n customer-success

# Check ingress
kubectl get ingress -n customer-success

# View logs
kubectl logs -f deployment/customer-success-api -n customer-success
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              customer-success namespace               │   │
│  │                                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐            │   │
│  │  │   API           │  │   Worker        │            │   │
│  │  │  Deployment     │  │  Deployment     │            │   │
│  │  │  (3 replicas)   │  │  (2 replicas)   │            │   │
│  │  └────────┬────────┘  └────────┬────────┘            │   │
│  │           │                    │                      │   │
│  │  ┌────────▼────────────────────▼────────┐            │   │
│  │  │         ClusterIP Service            │            │   │
│  │  │         (port 80 → 8000)             │            │   │
│  │  └────────┬─────────────────────────────┘            │   │
│  │           │                                          │   │
│  │  ┌────────▼─────────────────────────────┐            │   │
│  │  │           Ingress                    │            │   │
│  │  │     (SSL termination, routing)       │            │   │
│  │  └──────────────────────────────────────┘            │   │
│  │                                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐            │   │
│  │  │   ConfigMap     │  │    Secrets      │            │   │
│  │  │  (env config)   │  │  (credentials)  │            │   │
│  │  └─────────────────┘  └─────────────────┘            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Manifests Overview

| File | Resource | Purpose |
|------|----------|---------|
| `namespace.yaml` | Namespace | Isolated environment |
| `configmap.yaml` | ConfigMap | Non-sensitive config |
| `secrets.yaml` | Secret | Sensitive credentials |
| `serviceaccount.yaml` | SA/Role/RB | Pod identity & permissions |
| `api-deployment.yaml` | Deployment/Service/HPA | API server with autoscaling |
| `worker-deployment.yaml` | Deployment/HPA | Background worker |
| `ingress.yaml` | Ingress | External access |
| `monitoring.yaml` | ServiceMonitor/PrometheusRule | Metrics & alerts |

## Configuration

### Environment Variables (ConfigMap)

| Variable | Default | Description |
|----------|---------|-------------|
| ENVIRONMENT | production | Environment name |
| LOG_LEVEL | INFO | Logging level |
| DB_HOST | postgres-service | PostgreSQL host |
| DB_PORT | 5432 | PostgreSQL port |
| KAFKA_BOOTSTRAP_SERVERS | kafka-service:9092 | Kafka brokers |
| GMAIL_ENABLED | true | Enable Gmail channel |
| WHATSAPP_ENABLED | true | Enable WhatsApp channel |

### Secrets

| Variable | Description |
|----------|-------------|
| DB_PASSWORD | Database password |
| OPENAI_API_KEY | OpenAI API key |
| GMAIL_CLIENT_ID | Gmail OAuth client ID |
| GMAIL_CLIENT_SECRET | Gmail OAuth secret |
| TWILIO_ACCOUNT_SID | Twilio account SID |
| TWILIO_AUTH_TOKEN | Twilio auth token |

## Scaling

### Manual Scaling

```bash
# Scale API
kubectl scale deployment/customer-success-api --replicas=5 -n customer-success

# Scale Worker
kubectl scale deployment/customer-success-worker --replicas=4 -n customer-success
```

### Autoscaling

HPA is configured for automatic scaling:

| Metric | Target | Min | Max |
|--------|--------|-----|-----|
| CPU | 70% | 3 | 10 |
| Memory | 80% | 3 | 10 |

## Monitoring

### Access Metrics

```bash
# Port forward Prometheus
kubectl port-forward svc/prometheus-k8s 9090:9090 -n monitoring

# View API metrics
curl http://localhost:8000/metrics
```

### Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighErrorRate | Error rate > 5% | Critical |
| HighLatency | P95 latency > 2s | Warning |
| PodNotReady | Pod not ready 5m | Warning |
| KafkaLag | Consumer lag > 1000 | Warning |
| DBPoolExhausted | Connections < 2 | Critical |

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n customer-success
kubectl describe pod <pod-name> -n customer-success
```

### View Logs

```bash
# API logs
kubectl logs -f deployment/customer-success-api -n customer-success

# Worker logs
kubectl logs -f deployment/customer-success-worker -n customer-success
```

### Debug Pod

```bash
# Exec into pod
kubectl exec -it <pod-name> -n customer-success -- /bin/bash

# Run command in pod
kubectl exec <pod-name> -n customer-success -- python -c "from production.db import health_check; print('OK')"
```

### Common Issues

**ImagePullBackOff**
```bash
# Check image name and registry
kubectl describe pod <pod-name> -n customer-success
```

**CrashLoopBackOff**
```bash
# Check logs and events
kubectl logs <pod-name> -n customer-success --previous
kubectl get events -n customer-success --sort-by='.lastTimestamp'
```

## Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/customer-success-api -n customer-success

# Rollback to specific revision
kubectl rollout undo deployment/customer-success-api --to-revision=2 -n customer-success
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace customer-success

# Or delete individual resources
kubectl delete -f production/k8s/
```
