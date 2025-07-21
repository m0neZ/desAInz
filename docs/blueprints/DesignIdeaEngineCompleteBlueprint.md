# Design Idea Engine - Complete Blueprint

This document consolidates all previous markdown files in the repository, including the project summary, system architecture and technology stack details, deployment guide, implementation plan, and earlier blueprint iterations.

---
## Key Features

- Automated trending signal ingestion with deduplication
- Multi-factor scoring engine for idea ranking
- AI mock-up generation and listing creation
- Marketplace publisher for multiple platforms
- Feedback loop for continuous optimization

## 🏗️ Technical Architecture


### Microservices

1. **API Gateway** (Port 5000) - Unified API access point
2. **Signal Ingestion** (Port 5001) - Content signal processing
3. **Scoring Engine** (Port 5002) - AI-powered idea scoring
4. **AI Mockup Generation** (Port 5003) - Design creation
5. **Marketplace Publisher** (Port 5004) - Multi-platform publishing
6. **Feedback Loop** (Port 5005) - A/B testing and optimization
7. **Monitoring** (Port 5006) - System monitoring and analytics
8. **Optimization** (Port 5007) - Performance optimization

### Infrastructure

- **Database**: PostgreSQL 15 with pgvector extension
- **Cache**: Redis 7 for session and response caching
- **Message Queue**: Apache Kafka for async processing
- **Storage**: MinIO (S3-compatible) for object storage
- **Frontend**: React 18 with TypeScript and Tailwind CSS

### Security Features

- **CORS Protection**: Properly configured cross-origin requests
- **Rate Limiting**: API endpoint protection
- **Input Validation**: Comprehensive data validation
- **SSL/TLS**: Production-ready HTTPS configuration
- **Environment Isolation**: Secure secret management

## 🚀 Deployment Options

### Local Development

- **Docker Compose**: Single-command deployment
- **Hot Reload**: Development-friendly configuration
- **Comprehensive Logging**: Easy debugging and monitoring

### Production Deployment

- **Multi-Cloud Support**: AWS, GCP, Azure deployment guides
- **Container Orchestration**: Kubernetes and Docker Swarm ready
- **Load Balancing**: Nginx reverse proxy with SSL termination
- **Auto-Scaling**: Horizontal and vertical scaling capabilities

### Cloud-Specific Deployments

- **AWS**: ECS, EC2, RDS, ElastiCache integration
- **Google Cloud**: Cloud Run, Cloud SQL, Redis integration
- **Azure**: Container Instances, Database for PostgreSQL

# Design Idea Engine - System Architecture and Technology Stack

## Executive Summary

This document outlines the detailed system architecture and technology stack for the Design Idea Engine, a sophisticated platform designed to automate the creation and publishing of design ideas to various online marketplaces. The architecture follows microservices principles with event-driven communication, prioritizing cost-effectiveness, scalability, and maintainability while delivering an Apple-level user experience.

## 1. Technology Stack Selection

### 1.1 Core Infrastructure

**Container Orchestration and Deployment**

- **Docker**: Containerization of all services for consistent deployment across environments
- **Kubernetes (K8s)**: Container orchestration for production environments, providing auto-scaling, service discovery, and rolling updates
- **Local Development**: Docker Compose for simplified local development environment setup

**Cloud Provider Strategy**

- **Primary**: AWS (Amazon Web Services) for comprehensive service ecosystem and mature AI/ML offerings
- **Alternative**: Google Cloud Platform (GCP) for cost-effective alternatives and superior AI services
- **Multi-cloud approach**: Design services to be cloud-agnostic where possible to avoid vendor lock-in

### 1.2 Backend Services Technology Stack

**Programming Language and Framework**

- **Python 3.11+ (tested against 3.11 and 3.12)**: Primary language for backend services due to excellent AI/ML library ecosystem
- **Flask**: Lightweight web framework for microservices APIs
- **FastAPI**: Alternative for high-performance APIs requiring automatic documentation and type validation
- **Pydantic**: Data validation and serialization for robust API contracts

**Message Broker and Event Bus**

- **Apache Kafka**: Primary choice for high-throughput, fault-tolerant event streaming
- **Redis Streams**: Lightweight alternative for simpler use cases and development environments
- **Event Schema Registry**: Confluent Schema Registry or custom solution for event schema management

**Database Solutions**

- **PostgreSQL 15+**: Primary relational database with excellent JSON support and extensibility
- **pgvector**: PostgreSQL extension for vector similarity search and embeddings storage
- **Redis 7+**: In-memory data store for caching, session management, and real-time features
- **Amazon S3**: Object storage for mock-up images, generated assets, and file uploads
- **ClickHouse**: Optional columnar database for analytics and time-series data if needed

### 1.3 AI and Machine Learning Stack

**Image Generation**

- **Stable Diffusion XL**: Primary model for design generation, deployed on GPU instances
- **DALL-E 3 API**: Fallback option for high-quality image generation when local resources are unavailable
- **ComfyUI**: Workflow management for complex image generation pipelines
- **Automatic1111**: Alternative interface for Stable Diffusion with extensive plugin ecosystem

**Natural Language Processing**

- **OpenAI GPT-4**: Primary LLM for listing generation, content creation, and prompt engineering
- **Anthropic Claude**: Alternative LLM for specific use cases requiring different capabilities
- **Hugging Face Transformers**: Open-source models for embedding generation and text classification
- **spaCy**: NLP library for text processing, entity recognition, and linguistic analysis

**Computer Vision and Image Processing**

- **OpenCV**: Image processing, background removal, and computer vision tasks
- **Pillow (PIL)**: Python imaging library for format conversion, resizing, and basic manipulations
- **CLIP**: Vision-language model for image understanding and NSFW content detection
- **RemBG**: Specialized background removal service

### 1.4 Frontend Technology Stack

**Core Framework and Libraries**

- **Next.js 14+**: React-based framework with server-side rendering, API routes, and excellent developer experience
- **React 18+**: Component-based UI library with hooks and concurrent features
- **TypeScript**: Type-safe JavaScript for better development experience and fewer runtime errors
- **tRPC**: End-to-end typesafe APIs between frontend and backend

**UI/UX and Styling**

- **Tailwind CSS**: Utility-first CSS framework for rapid, consistent styling
 - **Shadcn/UI**: High-quality React components built on Radix UI
- **Framer Motion**: Animation library for smooth, Apple-like transitions and interactions
- **Lucide React**: Beautiful, customizable icon library

**State Management and Data Fetching**

- **Zustand**: Lightweight state management for client-side state
- **TanStack Query (React Query)**: Server state management, caching, and synchronization
- **SWR**: Alternative data fetching library with built-in caching

### 1.5 DevOps and Infrastructure

**CI/CD Pipeline**

- **GitHub Actions**: Automated testing, building, and deployment workflows
- **Docker Hub**: Container registry for storing and distributing Docker images
- **AWS ECR**: Alternative container registry integrated with AWS services

**Infrastructure as Code**

- **Terraform**: Infrastructure provisioning and management across cloud providers
- **AWS CDK**: Alternative for AWS-specific infrastructure with familiar programming languages
- **Helm Charts**: Kubernetes application packaging and deployment

**Monitoring and Observability**

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboarding for metrics and logs
- **Jaeger**: Distributed tracing for microservices
- **OpenTelemetry**: Unified observability framework for metrics, logs, and traces
- **PagerDuty**: Incident management and alerting

### 1.6 Security and Compliance

**Authentication and Authorization**

- **Auth0**: Managed authentication service with social login support
- **JWT**: Token-based authentication for API access
- **OAuth 2.0**: Standard protocol for secure API authorization

**Security Tools**

- **OWASP ZAP**: Security testing and vulnerability scanning
- **Snyk**: Dependency vulnerability scanning
- **HashiCorp Vault**: Secrets management and encryption

## 2. Detailed System Architecture

### 2.1 High-Level Architecture Overview

The Design Idea Engine follows a microservices architecture pattern with clear separation of concerns and event-driven communication. The system is designed to handle both batch processing for large-scale data ingestion and real-time processing for immediate response to trending signals.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Load Balancer / API Gateway                        │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                        Frontend (Next.js)                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Admin Dashboard │  │ Mock-up Gallery │  │ Analytics View  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │ tRPC/REST API
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                      API Gateway Service                                    │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────────────┐
│                        Event Bus (Kafka)                                    │
└─────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬───────────┘
      │         │         │         │         │         │         │
      ▼         ▼         ▼         ▼         ▼         ▼         ▼
┌───────────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌─────────┐
│  Signal   │ │Scoring│ │  AI   │ │Feedback│ │Market │ │Monitor│ │Workflow │
│ Ingestion │ │Engine │ │Mock-up│ │ Loop  │ │ place │ │  ing  │ │Orchestr.│
│  Service  │ │Service│ │ Gen.  │ │Service│ │Publish│ │Service│ │ Service │
└─────┬─────┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └────┬────┘
      │           │         │         │         │         │          │
      ▼           ▼         ▼         ▼         ▼         ▼          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Data Layer                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ PostgreSQL  │  │    Redis    │  │   AWS S3    │  │ ClickHouse  │       │
│  │ (pgvector)  │  │   Cache     │  │  Storage    │  │ Analytics   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Microservices Detailed Design

#### 2.2.1 Signal Ingestion Service

**Responsibility**: Collect and normalize signals from various social media platforms, event calendars, and trending sources.

**Technology Stack**:

- **Framework**: FastAPI for high-performance API endpoints
- **Web Scraping**: Selenium with headless Chrome for JavaScript-heavy sites
- **HTTP Client**: httpx for async HTTP requests
- **Rate Limiting**: Redis-based rate limiting to respect API quotas
- **Proxy Management**: Rotating proxy pool for anti-detection

**Key Components**:

- **Source Adapters**: Modular adapters for each signal source (TikTok, Instagram, Reddit, YouTube, etc.)
- **Normalization Engine**: Converts diverse signal formats into a unified schema
- **Deduplication Service**: Uses Redis Bloom filters to prevent duplicate signal processing
- **Rate Limiter**: Intelligent rate limiting based on source-specific quotas and policies

**Data Flow**:

1. Scheduled jobs trigger signal collection from configured sources
2. Source adapters fetch raw data using appropriate methods (API, scraping, etc.)
3. Raw signals are normalized into the standard Signal schema
4. Deduplication check prevents processing of duplicate content
5. Normalized signals are published to the event bus for downstream processing

#### 2.2.2 Scoring Engine Service

**Responsibility**: Calculate relevance and potential scores for ideas based on multiple factors including freshness, engagement, novelty, community fit, and seasonality.

**Technology Stack**:

- **Framework**: Flask for lightweight API service
- **ML Libraries**: scikit-learn for statistical calculations, NumPy for numerical operations
- **Vector Operations**: pgvector for similarity calculations
- **Caching**: Redis for hot-path caching of frequently accessed scores

**Scoring Algorithm Implementation**:

```python
def calculate_score(signal: Signal) -> float:
    """
    Calculate composite score: S = w₁·Freshness + w₂·Engagement + w₃·Novelty + w₄·CommunityFit + w₅·Seasonality
    """
    weights = get_current_weights()  # Dynamically updated based on feedback

    freshness = sigmoid(decay_function(hours_since_peak(signal)))
    engagement = zscore(signal.engagement_rate, historical_median(signal.source, days=7))
    novelty = 1 - cosine_similarity(signal.embedding, recent_centroid(signal.category))
    community_fit = calculate_community_affinity(signal.metadata)
    seasonality = seasonal_boost(signal.timestamp, signal.topics)

    return (weights.freshness * freshness +
            weights.engagement * engagement +
            weights.novelty * novelty +
            weights.community_fit * community_fit +
            weights.seasonality * seasonality)
```

#### 2.2.3 AI Mock-up Generation Service

**Responsibility**: Generate high-quality design mock-ups and listing content using AI models.

**Technology Stack**:

- **Framework**: FastAPI with async support for long-running operations
- **Image Generation**: Stable Diffusion XL with custom fine-tuning
- **GPU Management**: NVIDIA Docker containers with CUDA support
- **Queue System**: Celery with Redis broker for job management
- **Image Processing**: OpenCV and Pillow for post-processing

**Service Architecture**:

- **Prompt Builder**: Constructs optimized prompts using templates, keywords, and context
- **Generation Queue**: Manages GPU resources and job prioritization
- **Post-Processor**: Handles background removal, format conversion, and quality validation
- **Listing Generator**: Uses LLM to create compelling product titles, descriptions, and tags

**Scaling Strategy**:

- **Auto-scaling**: Kubernetes HPA based on queue length and GPU utilization
- **Spot Instances**: Cost optimization using AWS Spot instances with on-demand fallback
- **Model Caching**: Intelligent model loading and caching to minimize cold start times

#### 2.2.4 Feedback Loop Service

**Responsibility**: Collect marketplace performance data, conduct A/B tests, and optimize system parameters.

**Technology Stack**:

- **Framework**: Flask with scheduled background tasks
- **A/B Testing**: Custom implementation with statistical significance testing
- **Analytics**: Integration with marketplace APIs and custom tracking
- **Machine Learning**: Online learning algorithms for dynamic optimization

**Key Features**:

- **Marketplace Integration**: Automated data collection from Redbubble, Amazon Merch, etc.
- **A/B Test Management**: Design and execute micro-tests for idea validation
- **Performance Tracking**: Monitor CTR, conversion rates, and sales metrics
- **Dynamic Optimization**: Thompson Sampling for budget allocation and parameter tuning

#### 2.2.5 Marketplace Publishing Service

**Responsibility**: Automate the publishing process to various print-on-demand marketplaces.

**Technology Stack**:

- **Framework**: Flask with robust error handling and retry mechanisms
- **Browser Automation**: Selenium for RPA when APIs are unavailable
- **API Integration**: Direct integration with marketplace APIs where available
- **File Management**: Automated file preparation and format conversion

**Publishing Workflow**:

1. Receive publishing request with design assets and metadata
2. Validate design quality and compliance requirements
3. Format assets according to marketplace specifications
4. Execute publishing via API or RPA automation
5. Monitor publishing status and handle errors gracefully
6. Report success/failure back to the orchestration system

### 2.3 Data Architecture

#### 2.3.1 Database Schema Design

**PostgreSQL Primary Database**:

```sql
-- Signals table for raw ingested data
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    source signal_source_enum NOT NULL,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    content_hash CHAR(32) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ideas derived from signals
CREATE TABLE ideas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signals(id),
    title TEXT NOT NULL,
    description TEXT,
    embedding VECTOR(768),
    score FLOAT NOT NULL DEFAULT 0,
    status idea_status_enum DEFAULT 'queued',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generated mock-ups
CREATE TABLE mockups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id UUID REFERENCES ideas(id),
    s3_uri TEXT NOT NULL,
    variant mockup_variant_enum NOT NULL,
    generation_params JSONB,
    ctr FLOAT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Marketplace listings
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mockup_id UUID REFERENCES mockups(id),
    marketplace marketplace_enum NOT NULL,
    external_id TEXT,
    listing_url TEXT,
    status listing_status_enum DEFAULT 'draft',
    performance_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Redis Data Structures**:

- **Hot Topics Cache**: Sorted sets for trending topics with TTL
- **Rate Limiting**: Token bucket implementation for API rate limiting
- **Session Storage**: User session data for the admin dashboard
- **Job Queues**: Celery task queues for background processing

**S3 Storage Organization**:

```
design-idea-engine-bucket/
├── raw-signals/
│   ├── year=2024/month=01/day=15/
│   └── ...
├── generated-mockups/
│   ├── idea-id/
│   │   ├── variants/
│   │   └── metadata.json
│   └── ...
├── published-assets/
│   ├── marketplace/
│   └── ...
└── backups/
    ├── database/
    └── configurations/
```

Use the `setup_storage.sh` script to create this layout automatically.

#### 2.3.2 Event Schema Design

**Event Bus Message Format**:

```
{
  "eventType": "signal.ingested",
  "eventId": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "signal-ingestion-service",
  "version": "1.0",
  "data": {
    "signalId": "uuid",
    "source": "tiktok",
    "content": "...",
    "metadata": {...}
  },
  "correlationId": "uuid"
}
```

**Key Event Types**:

- `signal.ingested`: New signal collected from external source
- `idea.scored`: Idea scoring completed
- `mockup.generated`: AI mock-up generation completed
- `listing.published`: Design published to marketplace
- `feedback.received`: Performance data received from marketplace

### 2.4 Security Architecture

#### 2.4.1 Authentication and Authorization

**Multi-layered Security Approach**:

- **API Gateway**: Centralized authentication and rate limiting
- **Service-to-Service**: JWT tokens with short expiration times
- **Database**: Row-level security and encrypted connections
- **Storage**: S3 bucket policies and IAM roles

**User Authentication Flow**:

1. User authenticates via Auth0 with social login or email/password
2. Auth0 returns JWT token with user claims and permissions
3. Frontend includes JWT in all API requests
4. API Gateway validates token and forwards requests to services
5. Services use token claims for authorization decisions

#### 2.4.2 Data Protection and Privacy

**Compliance Measures**:

- **GDPR Compliance**: Data minimization, right to deletion, consent management
- **Data Encryption**: At-rest encryption for databases and S3, in-transit TLS 1.3
- **PII Handling**: Automatic detection and purging of personally identifiable information
- **Audit Logging**: Comprehensive logging of all data access and modifications

**Brand Safety and Content Moderation**:

- **Trademark Checking**: Integration with USPTO and EUIPO APIs
- **NSFW Detection**: CLIP-based content filtering for generated images
- **Content Validation**: Multi-stage validation pipeline for generated content

## 3. Cost Optimization Strategy

### 3.1 Infrastructure Cost Management

**Compute Optimization**:

- **Spot Instances**: Use AWS Spot instances for GPU-intensive workloads with 60-90% cost savings
- **Auto-scaling**: Implement aggressive auto-scaling policies to minimize idle resources
- **Reserved Instances**: Purchase reserved instances for predictable baseline workloads
- **Serverless**: Use AWS Lambda for infrequent, event-driven tasks

**Storage Optimization**:

- **Lifecycle Policies**: Automatic transition of old data to cheaper storage classes
- **Compression**: Implement compression for stored images and data
- **CDN**: Use CloudFront for global content delivery and reduced bandwidth costs

**Database Optimization**:

- **Connection Pooling**: Minimize database connections and associated costs
- **Query Optimization**: Regular query performance analysis and optimization
- **Read Replicas**: Use read replicas for analytics workloads to reduce primary database load

### 3.2 Operational Cost Management

**Development and Deployment**:

- **Open Source First**: Prioritize open-source solutions over proprietary alternatives
- **Shared Resources**: Use shared development and staging environments
- **Automated Testing**: Comprehensive test coverage to reduce manual testing costs

**Monitoring and Alerting**:

- **Proactive Monitoring**: Prevent issues before they impact users or require expensive fixes
- **Cost Alerts**: Automated alerts when spending exceeds predefined thresholds
- **Resource Optimization**: Regular analysis of resource utilization and right-sizing

## 4. Scalability and Performance

### 4.1 Horizontal Scaling Strategy

**Microservices Scaling**:

- **Independent Scaling**: Each service scales based on its specific load patterns
- **Load Balancing**: Intelligent load balancing with health checks and circuit breakers
- **Database Sharding**: Horizontal partitioning of large tables when needed

**Event Bus Scaling**:

- **Kafka Partitioning**: Proper partitioning strategy for parallel processing
- **Consumer Groups**: Multiple consumer instances for high-throughput processing
- **Dead Letter Queues**: Robust error handling and retry mechanisms

### 4.2 Performance Optimization

**Caching Strategy**:

- **Multi-level Caching**: Application-level, database-level, and CDN caching
- **Cache Invalidation**: Intelligent cache invalidation strategies
- **Hot Data Identification**: Automatic identification and caching of frequently accessed data

**Database Performance**:

- **Indexing Strategy**: Comprehensive indexing for query optimization
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Regular query performance analysis and optimization

## 5. Deployment and DevOps Strategy

### 5.1 CI/CD Pipeline Design

**Development Workflow**:

```
Developer Push → GitHub → GitHub Actions → Tests → Build → Deploy to Dev → Integration Tests → Deploy to Staging → UAT → Deploy to Production
```

**Pipeline Stages**:

1. **Code Quality**: Linting, type checking, security scanning
2. **Testing**: Unit tests, integration tests, contract tests
3. **Building**: Docker image creation and vulnerability scanning
4. **Deployment**: Blue-green deployment with automated rollback
5. **Monitoring**: Post-deployment health checks and performance monitoring

### 5.2 Environment Management

**Environment Strategy**:

- **Development**: Local Docker Compose setup for rapid development
- **Staging**: Production-like environment for final testing
- **Production**: High-availability, multi-AZ deployment

**Configuration Management**:

- **Environment Variables**: Externalized configuration for different environments
- **Secrets Management**: HashiCorp Vault or AWS Secrets Manager
- **Feature Flags**: Gradual feature rollout and A/B testing capabilities

## 6. Monitoring and Observability

### 6.1 Metrics and Alerting

**Key Performance Indicators**:

- **Business Metrics**: Ideas generated per day, mock-up success rate, marketplace performance
- **Technical Metrics**: API response times, error rates, resource utilization
- **User Experience**: Page load times, user engagement, conversion rates

**Alerting Strategy**:

- **Tiered Alerting**: Critical, warning, and informational alerts
- **Escalation Policies**: Automatic escalation for unresolved critical issues
- **Alert Fatigue Prevention**: Intelligent alert grouping and suppression

### 6.2 Logging and Tracing

**Structured Logging**:

- **JSON Format**: Consistent, machine-readable log format
- **Correlation IDs**: Request tracing across microservices
- **Log Aggregation**: Centralized logging with Elasticsearch or CloudWatch

**Distributed Tracing**:

- **OpenTelemetry**: Standardized tracing across all services
- **Performance Analysis**: Identify bottlenecks and optimization opportunities
- **Error Tracking**: Comprehensive error tracking and root cause analysis

This comprehensive architecture and technology stack design provides a solid foundation for building the Design Idea Engine. The next phase will focus on setting up the development environment and implementing the core backend services.

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

| Service               | Port   | Description                       |
| --------------------- | ------ | --------------------------------- |
| Nginx                 | 80/443 | Reverse proxy and SSL termination |
| Frontend              | 3000   | React admin dashboard             |
| API Gateway           | 5000   | Main API endpoint                 |
| Signal Ingestion      | 5001   | Content signal processing         |
| Scoring Engine        | 5002   | AI-powered idea scoring           |
| AI Mockup Generation  | 5003   | Design mockup creation            |
| Marketplace Publisher | 5004   | Multi-marketplace publishing      |
| Feedback Loop         | 5005   | A/B testing and optimization      |
| Monitoring            | 5006   | System monitoring and analytics   |
| Optimization          | 5007   | Performance optimization          |

### Infrastructure

| Component             | Purpose                             |
| --------------------- | ----------------------------------- |
| PostgreSQL + pgvector | Primary database with vector search |
| Redis                 | Caching and session storage         |
| Kafka + Zookeeper     | Message queue for async processing  |
| MinIO                 | S3-compatible object storage        |

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

#### Storage and CDN Setup

Use `scripts/setup_storage.sh` to initialize S3 or MinIO buckets with the required structure. After the bucket is ready, run `scripts/configure_cdn.sh` to create a CloudFront distribution. When mockups change, invalidate caches with `scripts/invalidate_cache.sh`.

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

# Design Idea Engine Blueprint

This consolidated blueprint summarizes the project's goals, architecture, and deployment approach. It merges content from the previous design documents.

## Objectives and Success Metrics

| Goal                                 | KPI                                                                 | Target    |
| ------------------------------------ | ------------------------------------------------------------------- | --------- |
| Generate high-potential design ideas | Ideas scored in top-quartile freshness & engagement                 | ≥ 200/day |
| Automate mock-up creation            | Ideas with at least one AI mock-up                                  | 95%       |
| Validate via feedback loop           | Statistically significant positive signal (CTR, Saves, Add-to-Cart) | 25%       |
| Time-to-publish                      | Ingest → live mock-up on marketplace                                | ≤ 2 h     |

## High-Level Architecture

The system uses event-driven microservices communicating through a message bus. Core services include:

- **Signal Ingestion** – collects trending data from social networks and events.
- **Scoring Engine** – ranks ideas using freshness, engagement, novelty, community fit and seasonality.
- **AI Mock-up Generation** – produces design variations with Stable Diffusion XL and post-processing.
- **Marketplace Publisher** – automates listing creation and one-click publishing.
- **Feedback Loop** – gathers marketplace metrics and performs A/B tests for continuous optimization.
- **Orchestrator & CI/CD** – manages workflows, deploys with blue‑green strategies, and monitors health.

### Data Stores

PostgreSQL with pgvector stores metadata and embeddings. S3 holds mock-up assets. Redis caches hot topics and supports rate limiting. Kafka (or another event bus) connects the services.

## Implementation Roadmap (Summary)

1. **Analysis & Planning** – finalize technology stack and architecture diagrams.
2. **Core Services** – implement Signal Ingestion, Data Storage and Scoring Engine with API endpoints.
3. **AI Integration** – add Prompt Builder, mock-up generation and listing draft creation.
4. **Frontend Dashboard** – build a responsive Next.js admin dashboard.
5. **Marketplace Integration** – enable one-click publish and ingest performance data.
6. **Monitoring & Optimization** – integrate observability, automate scaling and ensure brand safety.
7. **Testing & Deployment** – run comprehensive tests, then deploy via Docker/Kubernetes.

## Deployment Overview

Deployment uses Docker containers orchestrated by Kubernetes or Docker Compose. Production setups include SSL termination, centralized logging, and auto‑scaling on cloud providers (AWS, GCP or Azure). A blue‑green strategy enables zero‑downtime updates.

## Cost and Performance Considerations

- Use spot instances for GPU-intensive tasks and batch embeddings to maximize VRAM.
- Archive mock-ups over 12 months in colder storage.
- Monitor quotas and stagger API calls to reduce third-party costs.

## Quality, Governance and Compliance

- Trademark checks with USPTO/EUIPO APIs before publishing.
- NSFW filtering using CLIP-based models.
- Data privacy via public-only content storage and PII purging.
- Automated tests and contract tests for external APIs using VCR.py cassettes.

## Key Takeaways

Event-driven microservices with a robust vector store provide scalability and flexibility. Layered scoring enables iterative improvements while GPU-intensive tasks remain isolated behind queues for cost effectiveness. The roadmap prioritizes shipping value early while building a foundation for future scale.

---


## **2\. High-Level Architecture**

┌──────────────────┐ ┌────────────────────┐ ┌──────────────────────┐  
│ Signal Ingestors│──────▶│ Normalization & │──────▶│ Idea Store (DB) │  
│ (Social, Events)│ │ Deduplication │ │ & Vector Index │  
└────────┬─────────┘ └─────────┬──────────┘ └─────────┬────────────┘  
 │ │ ▲  
 ▼ ▼ │  
┌──────────────────┐ ┌────────────────────┐ ┌────────┴───────────┐  
│ Scoring Engine │◀──────│ AI Mock-up Gen. │──────▶│ Feedback Loop │  
│ (Batch \+ Real- )│ │ (Image & Listing) │ │ (A/B & Market) │  
└────────┬─────────┘ └────────────────────┘ └────────┬───────────┘  
 │ ▲ │  
 ▼ │ ▼  
┌──────────────────┐ ┌────────────────────┐ ┌──────────────────────┐  
│ Orchestrator & │──────▶│ Human Review \- UI │──────▶│ Marketplace Pushers │  
│ Job Scheduler │ └────────────────────┘ └──────────────────────┘  
└──────────────────┘

- **Micro-services** communicate via an event bus (Kafka/Pub-Sub) for loose coupling and scalability.

- **Cold-start** (hourly) vs. **Hot** (real-time spikes via webhooks).

---

## **3\. Component Details**

### **3.1 Signal Ingestion Layer**

| Source                               | Method                              | Meta Extracted                     | Notes                                       |
| ------------------------------------ | ----------------------------------- | ---------------------------------- | ------------------------------------------- |
| TikTok Discover / IG Explore         | Unofficial API \+ headless fallback | Hashtag, view velocity, like ratio | Headless cluster on Fargate; rotate proxies |
| Reddit r/all & niche subs            | Reddit API \+ Pushshift backup      | Title, subreddit, upvote/hour      | Historical pulls; filter NSFW               |
| YouTube Trending                     | Data v3 API                         | Thumbnail palette, title tokens    | Skip comments on first pass                 |
| Event & Holiday Calendars            | Static CSV \+ lightweight scrape    | Event name, locale, date           | Cache with long TTL                         |
| Nostalgia Archives (Wiki, TV Tropes) | Daily scrape                        | Topic, anniversary year            | Low-frequency job                           |

**Normalization** into a common `Signal` schema; dedupe with a Redis Bloom filter.

### **3.2 Data Store**

- **PostgreSQL** \+ **pgvector** for metadata & embeddings.

- **S3** for mock-up binaries.

- **Redis** for hot-topic caching (TTL ≤ 48 h).

### **3.3 Scoring Engine**

**Score** `S = w₁·Freshness + w₂·Engagement + w₃·Novelty + w₄·CommunityFit + w₅·Seasonality`

| Feature      | Calc                                                 | Notes                        |
| ------------ | ---------------------------------------------------- | ---------------------------- |
| Freshness    | `sigmoid(decay(hours_since_peak))`                   | Real-time priority           |
| Engagement   | `zscore(likes+comments+views per min, 7-day median)` | Normalized across sources    |
| Novelty      | `1 – cosine(embed, recent_centroid)`                 | Penalizes redundancy         |
| CommunityFit | Avg(subreddit_affinity, hashtag_cohesion)            | Pre-trained niche embeddings |
| Seasonality  | `1 if within ±7 days of event else exp(-distance)`   | Boosts event-aligned ideas   |

- Stateless containers scale based on queue length.

### **3.4 AI Mock-up Generation**

1. **Prompt Builder**
   - Grammars combine top keywords, format templates, nostalgia hooks.

2. **Generative Model**
   - **Stable Diffusion XL** fine-tuned for vector-style; AWS Batch GPU autoscaling.

   - Fallback to external APIs if necessary.

3. **Post-processing**
   - Background removal, CMYK conversion, DPI validation (300 DPI via Pillow).

4. **Listing Draft**
   - LLM generates title, bullets, tags (token cap 256).

### **3.5 Feedback Loop**

- **A/B micro-tests** via email list or low-budget ads (measure CTR).

- Hourly ingest of **marketplace metrics** (views, favorites, add-to-cart, sales).

- **Thompson Sampling** allocates promotion budget.

- Nightly online-learning update of scoring weights.

### **3.6 Orchestrator & CI/CD**

- **Temporal.io** / **Dagster** workflows with retry & approval gates.

- **GitHub Actions** → Docker → EKS with blue-green deploys.

- **Observability**: OpenTelemetry \+ Prometheus \+ Grafana \+ PagerDuty alerts.

### **3.7 UI/UX Surfaces**

- **Admin Dashboard** (Next.js \+ tRPC): signal stream, heatmap, mock-up gallery, A/B results.

- **One-click Publish**: push to Redbubble/Amazon Merch via APIs or RPA.

---

### **Core Data Model (simplified)**

erDiagram  
 SIGNAL {  
 uuid id PK  
 text content  
 source ENUM  
 captured_at TIMESTAMP  
 metadata JSONB  
 hash CHAR(32) UNIQUE  
 }  
 IDEA ||--|| SIGNAL : derived_from  
 IDEA {  
 uuid id PK  
 title TEXT  
 embedding VECTOR(768)  
 score FLOAT  
 status ENUM(queued, mocked, live, archived)  
 created_at TIMESTAMP  
 updated_at TIMESTAMP  
 }  
 MOCKUP ||--|| IDEA : for  
 MOCKUP {  
 uuid id PK  
 s3_uri TEXT  
 variant ENUM(front, back, colorway)  
 ctr FLOAT  
 }

---

### **Performance & Cost Optimizations**

| Area               | Strategy                                                   |
| ------------------ | ---------------------------------------------------------- |
| API quotas         | Stagger pulls; ETag caching; delta-only updates            |
| Scoring throughput | Batch 1 000 embeddings/vector ops per GPU to maximize VRAM |
| GPU mock-ups       | Spot instances \+ on-demand fallback; reuse seeds          |
| Storage lifecycle  | Archive mock-ups \> 12 months in Glacier/Coldline          |

---

## **7\. Quality, Governance & Compliance**

- **Brand & IP Safety**:
  - Trademark check via USPTO & EUIPO APIs before publish.

  - NSFW filter (open‑source CLIP‑based) on generated images.

- **Data Privacy**:
  - Store only public social content; purge PII fields.

- **Testing**:
  - Pytest \+ FactoryBoy fixtures.

  - Contract tests for each external API; use VCR.py cassettes to keep CI fast.

- **Monitoring & Alerts**:
- Average time from signal ingestion to publishing is tracked via the `signal_to_publish_seconds` metric and displayed in the monitoring dashboard.
- PagerDuty alerts trigger if this average exceeds the configured `SLA_THRESHOLD_HOURS`.
- Alerts are suppressed for `SLA_ALERT_COOLDOWN_MINUTES` after each incident.

### **Key Takeaways**

- **Event‑driven micro‑services** plus a robust vector store give speed and flexibility.

- **Layered scoring** keeps the engine lean—start simple and iterate with feedback.

- **GPU‑intensive steps** are isolated behind queues so other services remain cheap and fast.

- The roadmap focuses on shipping value early (one source, one marketplace) while laying solid foundations for scale.

# Design Idea Engine

A sophisticated platform for automated design creation and marketplace publishing, leveraging AI to generate high-potential design ideas and automate the entire workflow from signal ingestion to marketplace publishing.

## 🎯 Overview

The Design Idea Engine is a microservices-based system that:

- Ingests signals from social media platforms, trending topics, and events
- Scores ideas based on freshness, engagement, novelty, community fit, and seasonality
- Generates AI-powered design mock-ups using Stable Diffusion XL
- Automates publishing to print-on-demand marketplaces (Redbubble, Amazon Merch, etc.)
- Implements feedback loops for continuous optimization

## 🏗️ Architecture

### Microservices

- **API Gateway**: Central entry point and request routing
- **Signal Ingestion**: Collects data from TikTok, Instagram, Reddit, YouTube, etc.
- **Scoring Engine**: Calculates idea potential using multi-factor scoring
- **AI Mock-up Generation**: Creates design variations using AI models
- **Feedback Loop**: A/B testing and performance optimization
- **Marketplace Publisher**: Automated publishing to various platforms

### Technology Stack

- **Backend**: Python, Flask/FastAPI
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Database**: PostgreSQL with pgvector, Redis
- **Message Broker**: Apache Kafka
- **Storage**: S3-compatible (MinIO for development)
- **AI**: Stable Diffusion XL, OpenAI GPT-4
- **Infrastructure**: Docker, Kubernetes

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18 or 20 LTS and npm
- Python 3.11 or 3.12

### Development Setup

1. **Clone and setup the project**:

```bash
git clone <repository-url>
cd design-idea-engine
```

2. **Start infrastructure services**:

```bash
docker-compose up -d
```

3. **Setup backend services**:

```bash
# API Gateway
cd backend/api-gateway
source venv/bin/activate
pip install -r requirements.txt
python src/main.py

# Signal Ingestion (in new terminal)
cd backend/signal-ingestion
source venv/bin/activate
pip install -r requirements.txt
python src/main.py

# Repeat for other services...
```

4. **Setup frontend**:

```bash
cd frontend/admin-dashboard
npm install
npm run dev
```

5. **Access the application**:

- Frontend: http://localhost:3000
- API Gateway: http://localhost:5000
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

## 📊 Key Features

### Signal Ingestion

- **Multi-platform support**: TikTok, Instagram, Reddit, YouTube
- **Real-time processing**: Webhook-based and scheduled ingestion
- **Deduplication**: Redis Bloom filters prevent duplicate processing
- **Rate limiting**: Intelligent quota management

### AI-Powered Scoring

- **Multi-factor scoring**: Freshness, engagement, novelty, community fit, seasonality
- **Vector similarity**: pgvector for semantic similarity calculations
- **Dynamic weights**: Online learning for continuous optimization

### Design Generation

- **Stable Diffusion XL**: Fine-tuned for vector-style designs
- **Prompt engineering**: Grammar-based prompt construction
- **Post-processing**: Background removal, format conversion, DPI validation
- **Batch processing**: GPU auto-scaling for cost optimization

### Marketplace Integration

- **One-click publishing**: Automated publishing to multiple platforms
- **API integration**: Direct API calls where available
- **RPA fallback**: Browser automation for platforms without APIs
- **Performance tracking**: CTR, conversion rates, sales metrics

## 🔧 Configuration

### Environment Variables

Create `.env` files in each service directory:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/design_idea_engine
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your_openai_key
HUGGINGFACE_TOKEN=your_hf_token

# Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=design-idea-engine

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### Service Ports

- API Gateway: 5000
- Signal Ingestion: 5001
- Scoring Engine: 5002
- AI Mock-up Gen: 5003
- Feedback Loop: 5004
- Marketplace Publisher: 5005
- Frontend: 3000

## 📈 Monitoring

### Health Checks

Each service exposes health check endpoints:

- `GET /health` - Basic health status
- `GET /metrics` - Prometheus metrics

### Observability Stack

- **Metrics**: Prometheus + Grafana
- **Tracing**: Jaeger with OpenTelemetry
- **Logging**: Structured JSON logs
- **Alerting**: PagerDuty integration

## 🧪 Testing

### Backend Testing

```bash
cd backend/api-gateway
source venv/bin/activate
pytest tests/
```

### Frontend Testing

```bash
cd frontend/admin-dashboard
npm test
```

### Integration Testing

```bash
# Run full integration test suite
./scripts/run-integration-tests.sh
```

## 🚢 Deployment

### Production Deployment

1. **Build Docker images**:

```bash
./scripts/build-images.sh
```

2. **Deploy to Kubernetes**:

```bash
kubectl apply -f infrastructure/k8s/
```

3. **Configure monitoring**:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack
```

### CI/CD Pipeline

- **GitHub Actions**: Automated testing and deployment
- **Blue-green deployment**: Zero-downtime deployments
- **Automated rollback**: Health check-based rollback

## 📊 Success Metrics

| Metric                  | Target    |
| ----------------------- | --------- |
| Ideas generated per day | ≥ 200     |
| Mock-up success rate    | 95%       |
| Time to publish         | ≤ 2 hours |
| Positive signal rate    | 25%       |
