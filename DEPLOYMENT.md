# Deployment Guide

## Production Deployment

This guide covers deploying RecoveryAssistant to production environments.

## Prerequisites

- Domain name with SSL certificate
- Production database (PostgreSQL 15+)
- Redis instance
- API keys for all external services
- Container orchestration platform (Docker, Kubernetes, etc.)

## Environment Configuration

### Required API Keys

1. **OpenAI API Key**
   - Sign up at https://platform.openai.com/
   - Create API key with GPT-4 access
   - Set `OPENAI_API_KEY` in environment

2. **Stripe API Key**
   - Create account at https://stripe.com
   - Get API keys from Dashboard
   - Set `STRIPE_API_KEY` and `STRIPE_PUBLISHABLE_KEY`
   - Configure webhooks for payment events

3. **SendGrid (Optional but Recommended)**
   - Sign up at https://sendgrid.com
   - Create API key
   - Verify sender domain
   - Set `SENDGRID_API_KEY`

4. **Twilio (Optional for SMS)**
   - Create account at https://twilio.com
   - Get Account SID and Auth Token
   - Purchase phone number
   - Set `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`

### Database Setup

1. Create production PostgreSQL database
2. Update `DATABASE_URL` in environment
3. Run migrations:
   ```bash
   alembic upgrade head
   ```

### Redis Setup

1. Provision Redis instance (Redis Cloud, AWS ElastiCache, etc.)
2. Update `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

## Docker Deployment

### 1. Build Production Images

```bash
# Build backend
docker build -t recovery-assistant-backend:latest ./backend

# Build frontend
docker build -t recovery-assistant-frontend:latest ./frontend
```

### 2. Push to Registry

```bash
# Tag for registry
docker tag recovery-assistant-backend:latest your-registry/recovery-assistant-backend:latest
docker tag recovery-assistant-frontend:latest your-registry/recovery-assistant-frontend:latest

# Push
docker push your-registry/recovery-assistant-backend:latest
docker push your-registry/recovery-assistant-frontend:latest
```

### 3. Deploy with Docker Compose

Update `docker-compose.yml` for production:

```yaml
services:
  backend:
    image: your-registry/recovery-assistant-backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      # ... other env vars
    restart: always

  frontend:
    image: your-registry/recovery-assistant-frontend:latest
    environment:
      - VITE_API_URL=https://api.yourdomain.com
    restart: always
```

Run:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### 1. Create Secrets

```bash
kubectl create secret generic recovery-assistant-secrets \
  --from-literal=database-url=$DATABASE_URL \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=stripe-api-key=$STRIPE_API_KEY
```

### 2. Deploy Backend

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recovery-assistant-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: recovery-assistant-backend
  template:
    metadata:
      labels:
        app: recovery-assistant-backend
    spec:
      containers:
      - name: backend
        image: your-registry/recovery-assistant-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: recovery-assistant-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: recovery-assistant-secrets
              key: openai-api-key
```

### 3. Deploy Frontend

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recovery-assistant-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: recovery-assistant-frontend
  template:
    metadata:
      labels:
        app: recovery-assistant-frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/recovery-assistant-frontend:latest
        ports:
        - containerPort: 3000
```

### 4. Create Services & Ingress

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: recovery-assistant-backend
  ports:
  - port: 8000
    targetPort: 8000

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: recovery-assistant-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    - app.yourdomain.com
    secretName: recovery-assistant-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
```

## Monitoring & Logging

### Prometheus Metrics

Backend exposes metrics at `/metrics`:
- Request count
- Response time
- Error rate
- Active connections

### Logging

Configure centralized logging:
- Use structured JSON logs
- Ship to ELK stack or similar
- Monitor error logs for issues

### Alerts

Set up alerts for:
- High error rate (> 1%)
- Slow response time (> 2s)
- Failed payment processing
- Celery worker failures
- Database connection issues

## Backup & Disaster Recovery

### Database Backups

```bash
# Daily automated backup
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).sql s3://your-backup-bucket/
```

### Recovery Procedure

1. Restore database from backup
2. Redeploy application containers
3. Run any pending migrations
4. Verify system health

## Security Checklist

- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Rotate API keys regularly
- [ ] Enable database encryption at rest
- [ ] Set up VPC/network isolation
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Implement IP whitelisting for admin
- [ ] Regular security updates
- [ ] Vulnerability scanning

## Performance Optimization

### Database

- Enable connection pooling
- Create appropriate indexes
- Regular VACUUM and ANALYZE
- Consider read replicas for heavy queries

### Caching

- Use Redis for frequently accessed data
- Cache API responses where appropriate
- Implement query result caching

### Scaling

- Horizontal scaling of API servers
- Auto-scaling based on load
- CDN for frontend assets
- Separate Celery workers by task type

## Cost Optimization

### API Usage

- Monitor OpenAI API usage
- Implement request caching
- Rate limit AI generation

### Infrastructure

- Use auto-scaling to match demand
- Schedule Celery workers based on workload
- Use spot instances for non-critical workers

## Health Checks

### Endpoints

- `/health` - Basic health check
- `/health/db` - Database connectivity
- `/health/redis` - Redis connectivity
- `/health/ready` - Ready to serve traffic

### Monitoring

```bash
# Check all services
curl https://api.yourdomain.com/health

# Expected response
{
  "status": "healthy",
  "service": "RecoveryAssistant",
  "version": "1.0.0"
}
```

## Troubleshooting

### Common Production Issues

**High Memory Usage:**
- Check for memory leaks in Celery workers
- Increase worker concurrency limits
- Scale horizontally instead of vertically

**Slow API Responses:**
- Check database query performance
- Verify Redis connection
- Review API endpoint implementations

**Payment Processing Failures:**
- Verify Stripe webhook endpoints
- Check Stripe dashboard for errors
- Review payment logs

## Support

For production support:
- Monitor logs in real-time
- Set up PagerDuty or similar alerting
- Maintain runbook for common issues
- Document incident response procedures
