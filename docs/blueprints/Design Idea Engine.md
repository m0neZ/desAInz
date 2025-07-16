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
- Node.js 20+ and npm
- Python 3.11+

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

## 📚 API Documentation

### REST API Endpoints
- `GET /api/signals` - List ingested signals
- `POST /api/ideas` - Create new idea
- `GET /api/mockups` - List generated mock-ups
- `POST /api/publish` - Publish to marketplace

### Event Schema
```json
{
  "eventType": "signal.ingested",
  "eventId": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "signalId": "uuid",
    "source": "tiktok",
    "content": "...",
    "metadata": {...}
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- **Python**: Black formatting, flake8 linting
- **TypeScript**: ESLint + Prettier
- **Commit messages**: Conventional commits format

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## 🗺️ Roadmap

- [ ] Phase 1: Core backend services (Current)
- [ ] Phase 2: AI integration layer
- [ ] Phase 3: Frontend dashboard
- [ ] Phase 4: Marketplace integrations
- [ ] Phase 5: Analytics and optimization
- [ ] Phase 6: Production deployment

## 📊 Success Metrics

| Metric | Target |
|--------|--------|
| Ideas generated per day | ≥ 200 |
| Mock-up success rate | 95% |
| Time to publish | ≤ 2 hours |
| Positive signal rate | 25% |

