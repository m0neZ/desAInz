# Design Idea Engine - Deployment Guide

## 🚀 Production Deployment

This guide covers deploying the Design Idea Engine to production using Docker containers and cloud infrastructure.

## Prerequisites

- Docker and Docker Compose installed
- Domain name configured with DNS
- SSL certificate (Let's Encrypt recommended)
- Cloud provider account (AWS, GCP, or Azure)

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repository>
cd design-idea-engine
cp deployment/.env.example deployment/.env
```

### 2. Configure Environment

Edit `deployment/.env` with your production values:

```bash
# Required Configuration
POSTGRES_PASSWORD=your_secure_postgres_password
SECRET_KEY=your_super_secret_key_change_in_production
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
API_BASE_URL=https://your-domain.com

# Optional: Marketplace Integration
REDBUBBLE_API_KEY=your_redbubble_api_key
AMAZON_MERCH_API_KEY=your_amazon_merch_api_key
ETSY_API_KEY=your_etsy_api_key

# Optional: AI Services
OPENAI_API_KEY=your_openai_api_key
STABILITY_AI_API_KEY=your_stability_ai_api_key
```

### 3. SSL Certificate Setup

Place your SSL certificate files in `deployment/ssl/`:
- `cert.pem` - SSL certificate
- `key.pem` - Private key

For Let's Encrypt:
```bash
mkdir -p deployment/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deployment/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem deployment/ssl/key.pem
```

### 4. Deploy

```bash
cd deployment
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test endpoints
curl https://your-domain.com/health
curl https://your-domain.com/api/health
```

## Architecture Overview

### Services

| Service | Port | Description |
|---------|------|-------------|
| Nginx | 80/443 | Reverse proxy and SSL termination |
| Frontend | 3000 | React admin dashboard |
| API Gateway | 5000 | Main API endpoint |
| Signal Ingestion | 5001 | Content signal processing |
| Scoring Engine | 5002 | AI-powered idea scoring |
| AI Mockup Generation | 5003 | Design mockup creation |
| Marketplace Publisher | 5004 | Multi-marketplace publishing |
| Feedback Loop | 5005 | A/B testing and optimization |
| Monitoring | 5006 | System monitoring and analytics |
| Optimization | 5007 | Performance optimization |

### Infrastructure

| Component | Purpose |
|-----------|---------|
| PostgreSQL + pgvector | Primary database with vector search |
| Redis | Caching and session storage |
| Kafka + Zookeeper | Message queue for async processing |
| MinIO | S3-compatible object storage |

## Cloud Deployment Options

### AWS Deployment

#### Using ECS (Recommended)

1. **Create ECS Cluster**
```bash
aws ecs create-cluster --cluster-name design-idea-engine
```

2. **Setup RDS PostgreSQL**
```bash
aws rds create-db-instance \
  --db-instance-identifier design-idea-engine-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password your_password \
  --allocated-storage 20
```

3. **Setup ElastiCache Redis**
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id design-idea-engine-cache \
  --cache-node-type cache.t3.micro \
  --engine redis
```

4. **Deploy using ECS Task Definitions**
- Convert docker-compose.yml to ECS task definitions
- Use AWS Application Load Balancer for traffic distribution
- Configure auto-scaling policies

#### Using EC2

1. **Launch EC2 Instance**
   - Recommended: t3.large or larger
   - Ubuntu 22.04 LTS
   - Security groups: 80, 443, 22

2. **Install Dependencies**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
```

3. **Deploy Application**
```bash
git clone <repository>
cd design-idea-engine/deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and Push Images**
```bash
# Build all service images
./scripts/build-images.sh

# Push to Google Container Registry
./scripts/push-to-gcr.sh
```

2. **Deploy Services**
```bash
# Deploy each service to Cloud Run
gcloud run deploy api-gateway --image gcr.io/PROJECT_ID/api-gateway
gcloud run deploy frontend --image gcr.io/PROJECT_ID/frontend
# ... repeat for all services
```

3. **Setup Cloud SQL and Redis**
```bash
# Create PostgreSQL instance
gcloud sql instances create design-idea-engine-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro

# Create Redis instance
gcloud redis instances create design-idea-engine-cache \
  --size=1 \
  --region=us-central1
```

### Azure Deployment

#### Using Container Instances

1. **Create Resource Group**
```bash
az group create --name design-idea-engine --location eastus
```

2. **Deploy Container Group**
```bash
az container create \
  --resource-group design-idea-engine \
  --file azure-container-group.yaml
```

3. **Setup Azure Database for PostgreSQL**
```bash
az postgres server create \
  --resource-group design-idea-engine \
  --name design-idea-engine-db \
  --admin-user postgres \
  --admin-password your_password
```

## Monitoring and Maintenance

### Health Checks

The system includes comprehensive health checks:

```bash
# System overview
curl https://your-domain.com/api/health

# Individual service health
curl https://your-domain.com/api/monitoring/system/overview

# Performance metrics
curl https://your-domain.com/api/monitoring/analytics/dashboard
```

### Logging

Centralized logging with structured JSON format:

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# Service-specific logs
docker-compose -f docker-compose.prod.yml logs -f api-gateway
```

### Backup Strategy

#### Database Backup
```bash
# Automated daily backup
docker exec postgres pg_dump -U postgres design_idea_engine > backup_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i postgres psql -U postgres design_idea_engine < backup_20231201.sql
```

#### Object Storage Backup
```bash
# Sync MinIO data to S3
aws s3 sync /path/to/minio/data s3://your-backup-bucket/minio-backup/
```

### Scaling

#### Horizontal Scaling

1. **Load Balancer Configuration**
   - Use AWS ALB, GCP Load Balancer, or Azure Load Balancer
   - Configure health checks for all services
   - Enable auto-scaling based on CPU/memory metrics

2. **Database Scaling**
   - Read replicas for PostgreSQL
   - Redis cluster for caching
   - Connection pooling with PgBouncer

3. **Service Scaling**
```bash
# Scale specific services
docker-compose -f docker-compose.prod.yml up -d --scale api-gateway=3
docker-compose -f docker-compose.prod.yml up -d --scale scoring-engine=2
```

#### Vertical Scaling

Update resource limits in docker-compose.prod.yml:

```yaml
services:
  api-gateway:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Security Considerations

### Network Security

1. **Firewall Rules**
   - Only expose ports 80 and 443 to public
   - Restrict database access to application servers only
   - Use VPC/private networks for internal communication

2. **SSL/TLS Configuration**
   - Use strong cipher suites
   - Enable HSTS headers
   - Regular certificate renewal

### Application Security

1. **Environment Variables**
   - Never commit secrets to version control
   - Use secret management services (AWS Secrets Manager, etc.)
   - Rotate secrets regularly

2. **Database Security**
   - Use strong passwords
   - Enable SSL connections
   - Regular security updates

3. **API Security**
   - Rate limiting implemented
   - Input validation on all endpoints
   - CORS properly configured

## Performance Optimization

### Caching Strategy

1. **Redis Caching**
   - API response caching
   - Session storage
   - Temporary data storage

2. **CDN Integration**
   - Static asset delivery
   - Image optimization
   - Global content distribution

### Database Optimization

1. **Indexing**
   - Automatic index creation for frequently queried columns
   - Vector indexes for similarity search
   - Composite indexes for complex queries

2. **Query Optimization**
   - Connection pooling
   - Prepared statements
   - Query result caching

## Troubleshooting

### Common Issues

1. **Service Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs service-name

# Check resource usage
docker stats

# Restart service
docker-compose -f docker-compose.prod.yml restart service-name
```

2. **Database Connection Issues**
```bash
# Test database connectivity
docker exec -it postgres psql -U postgres -d design_idea_engine

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres
```

3. **High Memory Usage**
```bash
# Monitor resource usage
docker stats

# Check for memory leaks
docker exec api-gateway ps aux --sort=-%mem
```

### Performance Issues

1. **Slow API Responses**
   - Check database query performance
   - Review caching configuration
   - Monitor resource utilization

2. **High CPU Usage**
   - Scale horizontally
   - Optimize AI model inference
   - Review batch processing configuration

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   - Review system logs
   - Check disk space usage
   - Verify backup integrity

2. **Monthly**
   - Update dependencies
   - Review security patches
   - Performance optimization review

3. **Quarterly**
   - Security audit
   - Disaster recovery testing
   - Capacity planning review

### Getting Help

- Check the troubleshooting section above
- Review service logs for error messages
- Monitor system health endpoints
- Contact support with detailed error information

## Cost Optimization

### Resource Right-Sizing

1. **Monitor Usage Patterns**
   - Use cloud provider monitoring tools
   - Analyze peak vs. average usage
   - Identify underutilized resources

2. **Auto-Scaling Configuration**
   - Set appropriate scaling thresholds
   - Use spot instances for batch processing
   - Schedule scaling for predictable patterns

3. **Storage Optimization**
   - Implement data lifecycle policies
   - Use appropriate storage classes
   - Regular cleanup of temporary data

### Cost Monitoring

- Set up billing alerts
- Use cost allocation tags
- Regular cost review meetings
- Optimize based on usage patterns

---

For additional support or questions, please refer to the project documentation or contact the development team.

