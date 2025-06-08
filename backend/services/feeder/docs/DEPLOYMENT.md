# Deployment Guide

This guide covers deployment options for the News Feeder Service, including Docker, Kubernetes, and production considerations.

## Prerequisites

### System Requirements
- **CPU**: 2+ cores recommended
- **Memory**: 2GB+ RAM per instance
- **Storage**: 10GB+ for logs and temporary files
- **Network**: Stable internet connection with low latency

### Dependencies
- **Redis**: 6.0+ for duplicate detection and caching
- **Temporal**: 1.20+ for workflow orchestration
- **Python**: 3.13+ runtime environment

## Docker Deployment

### Building the Image

```dockerfile
# Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY docs/ ./docs/

# Create non-root user
RUN useradd --create-home --shell /bin/bash feeder
RUN chown -R feeder:feeder /app
USER feeder

# Expose ports
EXPOSE 8090 9000-9099

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8090/health || exit 1

# Run the application
CMD ["python", "-m", "src.main"]
```

### Build Commands

```bash
# Build the image
docker build -t news-feeder:latest .

# Build with specific tag
docker build -t news-feeder:1.0.0 .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t news-feeder:latest .
```

### Single Container Deployment

```bash
# Run with environment variables
docker run -d \
  --name news-feeder \
  --restart unless-stopped \
  -p 8090:8090 \
  -p 9000-9099:9000-9099 \
  -e REDIS_HOST=redis.example.com \
  -e TEMPORAL_HOST=temporal.example.com \
  -e TELEGRAM_API_ID=your_api_id \
  -e TELEGRAM_API_HASH=your_api_hash \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  news-feeder:latest

# Run with config file
docker run -d \
  --name news-feeder \
  --restart unless-stopped \
  -p 8090:8090 \
  -v $(pwd)/config/production.yaml:/app/config/config.yaml \
  news-feeder:latest
```

## Docker Compose Deployment

### Complete Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL for Temporal
  postgresql:
    image: postgres:15
    environment:
      POSTGRES_DB: temporal
      POSTGRES_USER: temporal
      POSTGRES_PASSWORD: temporal
    volumes:
      - postgresql_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U temporal"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Temporal server
  temporal:
    image: temporalio/auto-setup:latest
    depends_on:
      postgresql:
        condition: service_healthy
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgresql
    ports:
      - "7233:7233"  # Temporal server
      - "8080:8080"  # Temporal admin UI
    healthcheck:
      test: ["CMD", "tctl", "cluster", "health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis for caching and duplicate detection
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # News Feeder - Financial sources
  feeder-finance:
    build: .
    depends_on:
      redis:
        condition: service_healthy
      temporal:
        condition: service_healthy
    environment:
      - CONFIG_FILE=/app/config/finance.yaml
      - REDIS_HOST=redis
      - TEMPORAL_HOST=temporal
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    ports:
      - "8090:8090"  # Health check
      - "9000-9049:9000-9049"  # Webhook ports
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8090/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # News Feeder - Technology sources
  feeder-tech:
    build: .
    depends_on:
      redis:
        condition: service_healthy
      temporal:
        condition: service_healthy
    environment:
      - CONFIG_FILE=/app/config/tech.yaml
      - REDIS_HOST=redis
      - TEMPORAL_HOST=temporal
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    ports:
      - "8091:8090"  # Health check
      - "9050-9099:9050-9099"  # Webhook ports
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8090/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Prometheus for monitoring
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  # Grafana for dashboards
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    ports:
      - "3000:3000"

volumes:
  postgresql_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### Development Stack

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  temporal:
    image: temporalio/auto-setup:latest
    environment:
      - DB=sqlite
    ports:
      - "7233:7233"
      - "8080:8080"

  feeder-dev:
    build: .
    depends_on:
      - redis
      - temporal
    environment:
      - CONFIG_FILE=/app/config/development.yaml
      - REDIS_HOST=redis
      - TEMPORAL_HOST=temporal
      - LOG_LEVEL=DEBUG
    volumes:
      - ./config:/app/config
      - ./src:/app/src  # Mount source for development
      - ./logs:/app/logs
    ports:
      - "8090:8090"
      - "9000-9099:9000-9099"
    command: ["python", "-m", "src.main", "--reload"]
```

### Deployment Commands

```bash
# Start the complete stack
docker-compose up -d

# Start development stack
docker-compose -f docker-compose.dev.yml up -d

# Scale feeder instances
docker-compose up -d --scale feeder-finance=2

# View logs
docker-compose logs -f feeder-finance

# Stop and remove
docker-compose down

# Stop and remove with volumes
docker-compose down -v
```

## Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: news-feeder
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: feeder-config
  namespace: news-feeder
data:
  config.yaml: |
    service:
      name: "news-feeder"
      log_level: "INFO"
    
    sources:
      - type: "rss"
        name: "Reuters Business"
        url: "https://feeds.reuters.com/reuters/businessNews"
        update_mechanism: "polling"
        polling_config:
          interval_seconds: 300
    
    redis:
      host: "redis-service"
      port: 6379
    
    temporal:
      host: "temporal-service"
      port: 7233
```

### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: feeder-secrets
  namespace: news-feeder
type: Opaque
data:
  telegram-api-id: <base64-encoded-api-id>
  telegram-api-hash: <base64-encoded-api-hash>
  telegram-phone: <base64-encoded-phone>
  news-api-token: <base64-encoded-token>
```

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: news-feeder
  namespace: news-feeder
  labels:
    app: news-feeder
spec:
  replicas: 3
  selector:
    matchLabels:
      app: news-feeder
  template:
    metadata:
      labels:
        app: news-feeder
    spec:
      containers:
      - name: news-feeder
        image: news-feeder:1.0.0
        ports:
        - containerPort: 8090
          name: health
        - containerPort: 9000
          name: webhook-base
        env:
        - name: CONFIG_FILE
          value: "/app/config/config.yaml"
        - name: REDIS_HOST
          value: "redis-service"
        - name: TEMPORAL_HOST
          value: "temporal-service"
        - name: TELEGRAM_API_ID
          valueFrom:
            secretKeyRef:
              name: feeder-secrets
              key: telegram-api-id
        - name: TELEGRAM_API_HASH
          valueFrom:
            secretKeyRef:
              name: feeder-secrets
              key: telegram-api-hash
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: logs-volume
          mountPath: /app/logs
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8090
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8090
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config-volume
        configMap:
          name: feeder-config
      - name: logs-volume
        emptyDir: {}
```

### Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: news-feeder-service
  namespace: news-feeder
spec:
  selector:
    app: news-feeder
  ports:
  - name: health
    port: 8090
    targetPort: 8090
  - name: webhook
    port: 9000
    targetPort: 9000
  type: ClusterIP
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: news-feeder-hpa
  namespace: news-feeder
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: news-feeder
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: news-feeder-ingress
  namespace: news-feeder
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - feeder.example.com
    secretName: feeder-tls
  rules:
  - host: feeder.example.com
    http:
      paths:
      - path: /health
        pathType: Prefix
        backend:
          service:
            name: news-feeder-service
            port:
              number: 8090
      - path: /webhook
        pathType: Prefix
        backend:
          service:
            name: news-feeder-service
            port:
              number: 9000
```

### Deployment Commands

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n news-feeder

# View logs
kubectl logs -f deployment/news-feeder -n news-feeder

# Scale deployment
kubectl scale deployment news-feeder --replicas=5 -n news-feeder

# Update deployment
kubectl set image deployment/news-feeder news-feeder=news-feeder:1.1.0 -n news-feeder

# Delete deployment
kubectl delete -f k8s/
```

## Production Considerations

### Security

#### Network Security
```yaml
# Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: news-feeder-netpol
  namespace: news-feeder
spec:
  podSelector:
    matchLabels:
      app: news-feeder
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8090
    - protocol: TCP
      port: 9000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector:
        matchLabels:
          name: temporal
    ports:
    - protocol: TCP
      port: 7233
```

#### Pod Security Policy
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: news-feeder-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### Monitoring and Logging

#### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'news-feeder'
    static_configs:
      - targets: ['feeder-finance:8091', 'feeder-tech:8091']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'temporal'
    static_configs:
      - targets: ['temporal:8080']
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "News Feeder Metrics",
    "panels": [
      {
        "title": "Items Processed",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(news_items_processed_total[5m])",
            "legendFormat": "{{source_name}}"
          }
        ]
      },
      {
        "title": "Source Health",
        "type": "stat",
        "targets": [
          {
            "expr": "source_health_status",
            "legendFormat": "{{source_name}}"
          }
        ]
      }
    ]
  }
}
```

### Backup and Recovery

#### Redis Backup
```bash
# Backup Redis data
kubectl exec -n news-feeder redis-0 -- redis-cli BGSAVE
kubectl cp news-feeder/redis-0:/data/dump.rdb ./backup/redis-$(date +%Y%m%d).rdb

# Restore Redis data
kubectl cp ./backup/redis-20240101.rdb news-feeder/redis-0:/data/dump.rdb
kubectl rollout restart statefulset/redis -n news-feeder
```

#### Configuration Backup
```bash
# Backup configurations
kubectl get configmap feeder-config -n news-feeder -o yaml > backup/config-$(date +%Y%m%d).yaml
kubectl get secret feeder-secrets -n news-feeder -o yaml > backup/secrets-$(date +%Y%m%d).yaml
```

### Performance Tuning

#### Resource Optimization
```yaml
# Optimized resource requests/limits
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"

# JVM tuning for better performance
env:
- name: PYTHONUNBUFFERED
  value: "1"
- name: PYTHONOPTIMIZE
  value: "1"
```

#### Redis Optimization
```yaml
# Redis configuration for production
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
data:
  redis.conf: |
    maxmemory 256mb
    maxmemory-policy allkeys-lru
    save 900 1
    save 300 10
    save 60 10000
    appendonly yes
    appendfsync everysec
```

### Disaster Recovery

#### Multi-Region Deployment
```yaml
# Deploy across multiple availability zones
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - news-feeder
              topologyKey: kubernetes.io/hostname
```

#### Backup Strategy
1. **Daily**: Configuration and secrets backup
2. **Hourly**: Redis data backup
3. **Weekly**: Full system backup
4. **Monthly**: Long-term archive

This deployment guide provides comprehensive coverage for deploying the News Feeder Service in various environments, from development to production-scale Kubernetes clusters.