# Customer Success FTE - Complete Deployment Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Production Checklist](#production-checklist)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 16+ with pgvector extension
- Apache Kafka 2.8+
- OpenAI API key

### 1. Clone and Setup

```bash
cd customer-success-fte

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Required: OPENAI_API_KEY
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL and Kafka
docker-compose up -d postgres kafka

# Wait for services to be healthy
docker-compose ps
```

### 3. Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock httpx

# Run all tests
pytest production/tests/ -v

# Run with coverage
pytest production/tests/ -v --cov=production --cov-report=html
```

### 4. Start Application

```bash
# Full stack (API + Worker)
docker-compose --profile full up -d

# Or run locally
uvicorn production.api.main:app --reload

# Test health endpoint
curl http://localhost:8000/health
```

---

## Local Development

### Database Setup

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d customer_success

# Verify pgvector extension
\dx | grep vector

# View tables
\dt

# View knowledge base entries
SELECT category, COUNT(*) FROM knowledge_base GROUP BY category;
```

### Kafka Topics

```bash
# List topics (using kafka-cli or kafka-ui)
docker exec -it customer-success-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Expected topics:
# - customer_success.emails.inbound
# - customer_success.whatsapp.inbound
# - customer_success.web_form.submissions
# - customer_success.tickets.created
# - customer_success.tickets.updated
# - customer_success.escalations
# - customer_success.metrics
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/webhooks/gmail` | POST | Gmail webhook |
| `/webhooks/whatsapp` | POST | WhatsApp webhook |
| `/webhooks/web-form` | POST | Web form submission |
| `/tickets/{id}/status` | GET | Ticket status lookup |
| `/chat/instant` | POST | Instant chat support |

### Test Webhooks

```bash
# Test Gmail webhook
curl -X POST http://localhost:8000/webhooks/gmail \
  -H "Content-Type: application/json" \
  -d '{
    "messageId": "test-123",
    "threadId": "thread-456",
    "from": "customer@example.com",
    "subject": "Product inquiry",
    "body": "Hi, I need help with your product"
  }'

# Test WhatsApp webhook
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "From": "whatsapp:+1234567890",
    "Body": "Hello, I have a question"
  }'
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster 1.25+ (GKE, EKS, AKS, or local with minikube/kind)
- kubectl configured
- NGINX Ingress Controller
- cert-manager (for SSL)
- Prometheus Operator (for monitoring)

### 1. Build and Push Image

```bash
# Set your registry
export REGISTRY=gcr.io/your-project
export IMAGE_TAG=v1.0.0

# Build image
docker build -f production/Dockerfile -t $REGISTRY/customer-success-fte:$IMAGE_TAG .

# Push to registry
docker push $REGISTRY/customer-success-fte:$IMAGE_TAG
```

### 2. Configure Secrets

```bash
# Create namespace
kubectl create namespace customer-success

# Create secrets (use external secrets manager in production)
kubectl create secret generic customer-success-secrets \
  --from-literal=DB_PASSWORD='your-secure-password' \
  --from-literal=OPENAI_API_KEY='sk-...' \
  --from-literal=TWILIO_ACCOUNT_SID='AC...' \
  --from-literal=TWILIO_AUTH_TOKEN='...' \
  --namespace=customer-success
```

### 3. Update Configuration

Edit `production/k8s/configmap.yaml` and `production/k8s/secrets.yaml`:

```yaml
# configmap.yaml
data:
  DB_HOST: "your-postgres-service"
  KAFKA_BOOTSTRAP_SERVERS: "your-kafka-service:9092"

# secrets.yaml
stringData:
  OPENAI_API_KEY: "sk-your-actual-key"
```

### 4. Deploy

```bash
# Using deploy script
./production/k8s/deploy.sh customer-success

# Or manually
kubectl apply -f production/k8s/namespace.yaml
kubectl apply -f production/k8s/configmap.yaml
kubectl apply -f production/k8s/secrets.yaml
kubectl apply -f production/k8s/serviceaccount.yaml
kubectl apply -f production/k8s/api-deployment.yaml
kubectl apply -f production/k8s/worker-deployment.yaml
kubectl apply -f production/k8s/ingress.yaml
kubectl apply -f production/k8s/monitoring.yaml
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n customer-success

# Check services
kubectl get services -n customer-success

# Check ingress
kubectl get ingress -n customer-success

# View logs
kubectl logs -f deployment/customer-success-api -n customer-success
kubectl logs -f deployment/customer-success-worker -n customer-success
```

### 6. Configure Ingress

Update `production/k8s/ingress.yaml` with your domain:

```yaml
spec:
  tls:
    - hosts:
        - api.yourdomain.com
        - webhooks.yourdomain.com
      secretName: customer-success-tls
  rules:
    - host: api.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: customer-success-api-service
                port:
                  number: 80
```

### 7. Setup SSL

```bash
# Create ClusterIssuer (if not exists)
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
EOF
```

---

## Production Checklist

### Security

- [ ] Use external secrets manager (Vault, AWS Secrets Manager, GCP Secret Manager)
- [ ] Enable network policies
- [ ] Configure pod security policies
- [ ] Use private container registry
- [ ] Enable audit logging
- [ ] Configure RBAC with least privilege
- [ ] Enable SSL/TLS everywhere
- [ ] Configure CORS properly for web form

### Database

- [ ] Use managed PostgreSQL (RDS, Cloud SQL, Azure Database)
- [ ] Enable point-in-time recovery
- [ ] Configure connection pooling (PgBouncer)
- [ ] Setup read replicas for scaling
- [ ] Enable pgvector extension
- [ ] Configure backup retention

### Kafka

- [ ] Use managed Kafka (Confluent Cloud, MSK, Event Hubs)
- [ ] Configure replication factor >= 3
- [ ] Enable ACLs for topic access
- [ ] Setup dead letter queue
- [ ] Configure retention policies
- [ ] Monitor consumer lag

### Monitoring

- [ ] Configure Prometheus alerts
- [ ] Setup Grafana dashboards
- [ ] Enable distributed tracing (Jaeger, Zipkin)
- [ ] Configure log aggregation (ELK, Loki)
- [ ] Setup PagerDuty/OpsGenie integration
- [ ] Create runbooks for alerts

### Scaling

- [ ] Tune HPA thresholds
- [ ] Configure pod disruption budgets
- [ ] Setup cluster autoscaler
- [ ] Load test with expected traffic
- [ ] Configure resource quotas
- [ ] Plan for multi-region deployment

### CI/CD

- [ ] Setup automated testing
- [ ] Configure image scanning
- [ ] Enable canary deployments
- [ ] Configure rollback procedures
- [ ] Setup staging environment
- [ ] Document deployment process

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n customer-success

# View logs
kubectl logs <pod-name> -n customer-success

# Check events
kubectl get events -n customer-success --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it <pod-name> -n customer-success -- \
  python -c "from production.db.database import health_check; import asyncio; print(asyncio.run(health_check()))"

# Check database service
kubectl get endpoints postgres-service -n customer-success
```

### Kafka Connection Issues

```bash
# Test Kafka connectivity
kubectl exec -it <pod-name> -n customer-success -- \
  python -c "from production.kafka.client import KafkaClient; import asyncio; c = KafkaClient(); print(asyncio.run(c.health_check()))"

# Check Kafka service
kubectl get endpoints kafka-service -n customer-success
```

### High Error Rate

```bash
# Check error logs
kubectl logs deployment/customer-success-api -n customer-success | grep ERROR

# View metrics
kubectl port-forward svc/prometheus-k8s 9090:9090 -n monitoring
# Open http://localhost:9090

# Query error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

### Pod Crashing (CrashLoopBackOff)

```bash
# Check previous logs
kubectl logs <pod-name> -n customer-success --previous

# Check resource usage
kubectl top pods -n customer-success

# Verify secrets and configmaps
kubectl get secrets customer-success-secrets -n customer-success -o yaml
kubectl get configmap customer-success-config -n customer-success -o yaml
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress customer-success-ingress -n customer-success

# Verify ingress controller
kubectl get pods -n ingress-nginx

# Test service directly
kubectl port-forward svc/customer-success-api-service 8000:80 -n customer-success
curl http://localhost:8000/health
```

### Memory Issues

```bash
# Check memory usage
kubectl top pods -n customer-success

# Adjust limits in api-deployment.yaml
resources:
  limits:
    memory: "2Gi"  # Increase if needed
```

### Scaling Issues

```bash
# Check HPA status
kubectl get hpa -n customer-success

# Describe HPA for events
kubectl describe hpa customer-success-api-hpa -n customer-success

# Manual scaling
kubectl scale deployment/customer-success-api --replicas=5 -n customer-success
```

---

## Monitoring Queries

### Prometheus Queries

```promql
# Request rate
sum(rate(http_requests_total{namespace="customer-success"}[5m]))

# Error rate
sum(rate(http_requests_total{namespace="customer-success",status=~"5.."}[5m]))
/ sum(rate(http_requests_total{namespace="customer-success"}[5m]))

# P95 latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{namespace="customer-success"}[5m])) by (le))

# Kafka consumer lag
kafka_consumer_group_lag{consumergroup="customer-success-worker"}

# Database connections
db_pool_available{app="customer-success-fte"}
```

### Grafana Dashboard Panels

1. **Request Rate** - `sum(rate(http_requests_total[5m]))`
2. **Error Rate** - Error percentage over time
3. **Latency** - P50, P95, P99 latencies
4. **Pod CPU/Memory** - Resource utilization
5. **Kafka Lag** - Consumer lag per topic
6. **Database Connections** - Pool utilization

---

## Cost Optimization

### Resource Rightsizing

```yaml
# Start with conservative limits, adjust based on metrics
resources:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "1Gi"
```

### Spot Instances

- Use spot/preemptible instances for worker pods
- Configure pod disruption budgets
- Use node affinity for stateful workloads

### Image Optimization

- Use multi-stage builds (already configured)
- Minimize layer count
- Use slim base images

---

## Support

For issues or questions:

1. Check logs: `kubectl logs -f deployment/customer-success-api -n customer-success`
2. Review metrics in Prometheus/Grafana
3. Check Kubernetes events: `kubectl get events -n customer-success`
4. Consult runbooks for alert responses
