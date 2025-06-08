# News Feeder Service

A high-performance, event-driven news aggregation service that monitors multiple news sources and triggers Temporal workflows for real-time news processing.

## Overview

The News Feeder Service is designed to collect news from various sources (RSS feeds, web scrapers, Telegram channels, WebSockets, webhooks) and forward them to Temporal workflows for processing. It supports both polling-based and event-driven update mechanisms to ensure the fastest possible news delivery.

## Key Features

- **Multi-Source Support**: RSS feeds, web scraping, Telegram channels, WebSockets, webhooks
- **Event-Driven Architecture**: Real-time updates for sources that support events (< 100ms latency)
- **Intelligent Polling**: Configurable intervals for traditional sources
- **Duplicate Detection**: Redis-based content hashing to prevent duplicate processing
- **Temporal Integration**: Automatic workflow triggering for each news item
- **Docker Ready**: Containerized deployment with configurable instances
- **High Performance**: Async architecture with concurrent source processing

## Quick Start

### Prerequisites

- Python 3.13+
- Redis server
- Temporal server
- Docker (optional)

### Installation

```bash
# Clone and setup
cd backend/services/feeder
pip install -r requirements.txt

# Configure your sources
cp docs/examples/config.yaml config/config.yaml
# Edit config/config.yaml with your sources

# Run the service
python -m src.main
```

### Docker Deployment

```bash
# Build the image
docker build -t news-feeder .

# Run with docker-compose
docker-compose up -d
```

## Architecture

The service uses a hybrid architecture supporting both polling and event-driven sources:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   RSS Feeds     │───▶│  Polling Sources │───▶│                 │
├─────────────────┤    ├──────────────────┤    │                 │
│  Web Scrapers   │───▶│   (5-30 min)     │───▶│  Content        │
└─────────────────┘    └──────────────────┘    │  Processor      │
                                               │                 │
┌─────────────────┐    ┌──────────────────┐    │                 │
│  Telegram API   │───▶│  Event Sources   │───▶│                 │
├─────────────────┤    ├──────────────────┤    └─────────────────┘
│  WebSockets     │───▶│   (<100ms)       │           │
├─────────────────┤    ├──────────────────┤           ▼
│  Webhooks       │───▶│                  │    ┌─────────────────┐
└─────────────────┘    └──────────────────┘    │ Duplicate       │
                                               │ Detection       │
                                               │ (Redis)         │
                                               └─────────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────────┐
                                               │ Temporal        │
                                               │ Workflow        │
                                               │ Starter         │
                                               └─────────────────┘
```

## Configuration

Sources are configured via YAML files. Each source specifies its type, update mechanism, and specific settings:

```yaml
sources:
  - type: "rss"
    name: "Reuters Business"
    url: "https://feeds.reuters.com/reuters/businessNews"
    update_mechanism: "polling"
    polling_config:
      interval_seconds: 300
    
  - type: "telegram_event"
    name: "News Channel"
    url: "https://t.me/news_channel"
    update_mechanism: "event_driven"
    specific_config:
      api_id: "${TELEGRAM_API_ID}"
      api_hash: "${TELEGRAM_API_HASH}"
```

## Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - Detailed system design and component interactions
- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete configuration reference and examples
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Docker, Kubernetes, and production deployment
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup, testing, and contribution guidelines

## Performance

| Source Type | Update Mechanism | Typical Latency | Resource Usage |
|-------------|------------------|-----------------|----------------|
| RSS | Polling | 5-15 minutes | Low CPU, Low Memory |
| Web Scraper | Polling | 10-30 minutes | Medium CPU, Medium Memory |
| Telegram | Event-driven | <1 second | Low CPU, Low Memory |
| WebSocket | Event-driven | <100ms | Low CPU, Medium Memory |
| Webhook | Event-driven | <50ms | Very Low CPU, Low Memory |

## Monitoring

The service exposes health check endpoints and metrics:

- Health Check: `http://localhost:8090/health`
- Metrics: `http://localhost:8090/metrics` (Prometheus format)
- Source Status: `http://localhost:8090/sources`

## License

[Add your license here]

## Contributing

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for development setup and contribution guidelines.