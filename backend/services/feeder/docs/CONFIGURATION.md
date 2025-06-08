# Configuration Guide

This guide covers all configuration options for the News Feeder Service, including source configurations, system settings, and deployment options.

## Configuration File Structure

The service uses YAML configuration files with the following structure:

```yaml
# Global service configuration
service:
  name: "news-feeder"
  log_level: "INFO"
  check_interval_minutes: 10
  max_concurrent_sources: 10

# Source definitions
sources:
  - type: "rss"
    # ... source-specific config

# Redis configuration
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: null
  ssl: false

# Temporal configuration
temporal:
  host: "localhost"
  port: 7233
  namespace: "default"
  task_queue: "news-processing"

# Webhook configuration
webhook:
  base_port: 9000
  port_range: 100
  auto_assign: true
  health_check_path: "/health"

# Monitoring configuration
monitoring:
  health_check_port: 8090
  metrics_enabled: true
  prometheus_port: 8091
```

## Source Configuration

### Common Source Fields

All sources share these common configuration fields:

```yaml
sources:
  - type: "source_type"           # Required: Source type identifier
    name: "source_name"           # Required: Human-readable source name
    url: "source_url"             # Required: Source URL or identifier
    update_mechanism: "polling"   # Required: "polling", "event_driven", or "hybrid"
    enabled: true                 # Optional: Enable/disable source (default: true)
    
    # Polling configuration (for polling/hybrid sources)
    polling_config:
      interval_seconds: 600       # Polling interval (default: 600)
      max_concurrent_requests: 1  # Max concurrent requests (default: 1)
      retry_attempts: 3           # Retry attempts on failure (default: 3)
      retry_delay_seconds: 30     # Delay between retries (default: 30)
      timeout_seconds: 30         # Request timeout (default: 30)
    
    # Event configuration (for event_driven/hybrid sources)
    event_config:
      webhook_port: null          # Specific webhook port (auto-assigned if null)
      webhook_path: "/webhook"    # Webhook endpoint path
      websocket_reconnect: true   # Auto-reconnect WebSockets (default: true)
      event_buffer_size: 1000     # Event buffer size (default: 1000)
      max_event_age_seconds: 3600 # Max age for buffered events (default: 3600)
    
    # Source-specific configuration
    specific_config:
      # Varies by source type
```

### RSS Source Configuration

```yaml
sources:
  - type: "rss"
    name: "Reuters Business News"
    url: "https://feeds.reuters.com/reuters/businessNews"
    update_mechanism: "polling"
    
    polling_config:
      interval_seconds: 300       # Check every 5 minutes
      max_concurrent_requests: 1
      retry_attempts: 3
      timeout_seconds: 30
    
    specific_config:
      # Content extraction
      extract_full_content: true  # Extract full article content (default: false)
      max_content_length: 10000   # Max content length in characters
      
      # HTTP settings
      user_agent: "NewsFeeder/1.0"
      headers:
        "Accept": "application/rss+xml, application/xml, text/xml"
      
      # Feed parsing
      respect_ttl: true           # Respect feed TTL directive (default: true)
      use_etag: true              # Use ETag for conditional requests (default: true)
      use_last_modified: true     # Use Last-Modified header (default: true)
      
      # Content filtering
      min_title_length: 10        # Minimum title length (default: 0)
      max_title_length: 200       # Maximum title length (default: unlimited)
      exclude_categories: []      # Categories to exclude
      include_categories: []      # Categories to include (empty = all)
      
      # Language detection
      detect_language: false      # Detect content language (default: false)
      allowed_languages: ["en"]   # Allowed languages (empty = all)
```

### Web Scraper Source Configuration

```yaml
sources:
  - type: "web_scraper"
    name: "Example News Site"
    url: "https://example-news-site.com/news"
    update_mechanism: "polling"
    
    polling_config:
      interval_seconds: 900       # Check every 15 minutes
      max_concurrent_requests: 2
      retry_attempts: 3
    
    specific_config:
      # Content selectors (CSS selectors)
      article_list_selector: ".article-list .article"
      title_selector: "h2.title a"
      link_selector: "h2.title a"
      description_selector: ".summary"
      date_selector: ".publish-date"
      author_selector: ".author"
      category_selector: ".category"
      
      # Full content extraction
      extract_full_content: true
      content_selector: ".article-content"
      
      # Pagination
      pagination_enabled: true
      next_page_selector: ".pagination .next"
      max_pages: 5
      
      # HTTP settings
      user_agent: "Mozilla/5.0 (compatible; NewsFeeder/1.0)"
      headers:
        "Accept": "text/html,application/xhtml+xml"
      cookies: {}
      
      # Rate limiting
      delay_between_requests: 1   # Seconds between requests
      respect_robots_txt: true    # Respect robots.txt (default: true)
      
      # Content filtering
      min_content_length: 100     # Minimum content length
      exclude_patterns: []        # Regex patterns to exclude
      include_patterns: []        # Regex patterns to include
      
      # JavaScript rendering (if needed)
      use_selenium: false         # Use Selenium for JS rendering
      selenium_timeout: 30        # Selenium page load timeout
```

### Telegram Event Source Configuration

```yaml
sources:
  - type: "telegram_event"
    name: "News Channel"
    url: "https://t.me/news_channel"
    update_mechanism: "event_driven"
    
    event_config:
      event_buffer_size: 500
      max_event_age_seconds: 1800
    
    specific_config:
      # Telegram API credentials
      api_id: "${TELEGRAM_API_ID}"
      api_hash: "${TELEGRAM_API_HASH}"
      phone: "${TELEGRAM_PHONE}"
      session_name: "news_feeder"
      
      # Channel configuration
      channel_username: "news_channel"  # Without @
      channel_id: null                  # Alternative to username
      
      # Message filtering
      message_types: ["text", "photo", "document"]  # Message types to process
      min_message_length: 10            # Minimum message length
      exclude_forwarded: false          # Exclude forwarded messages
      exclude_replies: true             # Exclude reply messages
      
      # Content extraction
      extract_links: true               # Extract URLs from messages
      extract_media: true               # Download and process media
      media_download_path: "/tmp/media" # Media download directory
      
      # Rate limiting
      flood_sleep_threshold: 60         # Sleep on flood wait (seconds)
```

### WebSocket Source Configuration

```yaml
sources:
  - type: "websocket"
    name: "News API WebSocket"
    url: "wss://api.newsservice.com/live"
    update_mechanism: "event_driven"
    
    event_config:
      websocket_reconnect: true
      event_buffer_size: 1000
    
    specific_config:
      # Authentication
      auth_method: "header"             # "header", "query", "message"
      auth_header: "Authorization"
      auth_token: "${NEWS_API_TOKEN}"
      
      # Connection settings
      ping_interval: 30                 # Ping interval (seconds)
      ping_timeout: 10                  # Ping timeout (seconds)
      max_reconnect_attempts: 10        # Max reconnection attempts
      reconnect_delay: 5                # Initial reconnect delay (seconds)
      
      # Message handling
      message_format: "json"            # "json", "text", "binary"
      message_schema: null              # JSON schema for validation
      
      # Subscription (if required)
      subscribe_on_connect: true
      subscription_message:
        type: "subscribe"
        topics: ["finance", "technology"]
      
      # Content mapping
      title_field: "title"
      description_field: "summary"
      link_field: "url"
      date_field: "published_at"
      author_field: "author"
```

### Webhook Source Configuration

```yaml
sources:
  - type: "webhook"
    name: "News Provider Webhook"
    url: "http://localhost:9001/webhook/news-provider"
    update_mechanism: "event_driven"
    
    event_config:
      webhook_port: 9001
      webhook_path: "/webhook/news-provider"
    
    specific_config:
      # Authentication
      auth_method: "token"              # "none", "token", "signature", "basic"
      auth_token: "${WEBHOOK_AUTH_TOKEN}"
      auth_header: "X-Auth-Token"
      
      # Signature verification (for "signature" auth)
      signature_header: "X-Signature"
      signature_algorithm: "sha256"     # "sha1", "sha256", "sha512"
      signature_secret: "${WEBHOOK_SECRET}"
      
      # Request validation
      allowed_ips: []                   # Allowed source IPs (empty = all)
      max_payload_size: 1048576         # Max payload size (1MB)
      content_types: ["application/json"]
      
      # Content mapping
      title_field: "title"
      description_field: "description"
      link_field: "link"
      date_field: "published"
      author_field: "author"
      
      # Response configuration
      success_response: {"status": "ok"}
      error_response: {"status": "error"}
```

## Environment Variables

Configuration values can be overridden using environment variables:

### Service Configuration
```bash
# Service settings
FEEDER_SERVICE_NAME="news-feeder"
FEEDER_LOG_LEVEL="INFO"
FEEDER_CHECK_INTERVAL_MINUTES=10
FEEDER_MAX_CONCURRENT_SOURCES=10

# Redis configuration
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=""
REDIS_SSL=false

# Temporal configuration
TEMPORAL_HOST="localhost"
TEMPORAL_PORT=7233
TEMPORAL_NAMESPACE="default"
TEMPORAL_TASK_QUEUE="news-processing"

# Webhook configuration
WEBHOOK_BASE_PORT=9000
WEBHOOK_PORT_RANGE=100
WEBHOOK_AUTO_ASSIGN=true

# Monitoring
HEALTH_CHECK_PORT=8090
METRICS_ENABLED=true
PROMETHEUS_PORT=8091
```

### Source-Specific Variables
```bash
# Telegram
TELEGRAM_API_ID="your_api_id"
TELEGRAM_API_HASH="your_api_hash"
TELEGRAM_PHONE="your_phone_number"

# News APIs
NEWS_API_TOKEN="your_news_api_token"
WEBHOOK_AUTH_TOKEN="your_webhook_token"
WEBHOOK_SECRET="your_webhook_secret"

# Database URLs
REDIS_URL="redis://localhost:6379/0"
TEMPORAL_URL="temporal://localhost:7233"
```

## Configuration Examples

### Development Configuration

```yaml
# config/development.yaml
service:
  name: "news-feeder-dev"
  log_level: "DEBUG"
  check_interval_minutes: 5

sources:
  - type: "rss"
    name: "Test RSS Feed"
    url: "https://feeds.reuters.com/reuters/topNews"
    update_mechanism: "polling"
    polling_config:
      interval_seconds: 300
    specific_config:
      extract_full_content: false

redis:
  host: "localhost"
  port: 6379
  db: 1  # Use different DB for development

temporal:
  host: "localhost"
  port: 7233
  namespace: "development"

webhook:
  base_port: 9100  # Different port range for dev
  port_range: 50

monitoring:
  health_check_port: 8190
  metrics_enabled: true
  prometheus_port: 8191
```

### Production Configuration

```yaml
# config/production.yaml
service:
  name: "news-feeder-prod"
  log_level: "INFO"
  check_interval_minutes: 10
  max_concurrent_sources: 20

sources:
  - type: "rss"
    name: "Reuters Business"
    url: "https://feeds.reuters.com/reuters/businessNews"
    update_mechanism: "polling"
    polling_config:
      interval_seconds: 300
    specific_config:
      extract_full_content: true
      user_agent: "NewsFeeder/1.0 (Production)"

  - type: "telegram_event"
    name: "Breaking News Channel"
    url: "https://t.me/breaking_news"
    update_mechanism: "event_driven"
    specific_config:
      api_id: "${TELEGRAM_API_ID}"
      api_hash: "${TELEGRAM_API_HASH}"
      phone: "${TELEGRAM_PHONE}"
      channel_username: "breaking_news"

redis:
  host: "${REDIS_HOST}"
  port: "${REDIS_PORT}"
  password: "${REDIS_PASSWORD}"
  ssl: true

temporal:
  host: "${TEMPORAL_HOST}"
  port: "${TEMPORAL_PORT}"
  namespace: "production"
  task_queue: "news-processing-prod"

webhook:
  base_port: 9000
  port_range: 100
  auto_assign: true

monitoring:
  health_check_port: 8090
  metrics_enabled: true
  prometheus_port: 8091
```

### Multi-Instance Configuration

For running multiple feeder instances:

```yaml
# config/instance-1.yaml (Financial news)
service:
  name: "news-feeder-finance"
  
sources:
  - type: "rss"
    name: "Bloomberg Markets"
    url: "https://feeds.bloomberg.com/markets/news.rss"
    # ... config
    
  - type: "rss"
    name: "MarketWatch"
    url: "https://feeds.marketwatch.com/marketwatch/topstories/"
    # ... config

webhook:
  base_port: 9000
  port_range: 50

monitoring:
  health_check_port: 8090
```

```yaml
# config/instance-2.yaml (Technology news)
service:
  name: "news-feeder-tech"
  
sources:
  - type: "rss"
    name: "TechCrunch"
    url: "https://techcrunch.com/feed/"
    # ... config
    
  - type: "websocket"
    name: "Tech News Live"
    url: "wss://api.technews.com/live"
    # ... config

webhook:
  base_port: 9050
  port_range: 50

monitoring:
  health_check_port: 8091
```

## Configuration Validation

The service validates configuration on startup:

### Required Fields
- `sources`: At least one source must be configured
- `sources[].type`: Must be a supported source type
- `sources[].name`: Must be unique across all sources
- `sources[].url`: Must be a valid URL
- `sources[].update_mechanism`: Must be "polling", "event_driven", or "hybrid"

### Validation Rules
- Port numbers must be between 1024-65535
- Polling intervals must be >= 60 seconds
- Event buffer sizes must be > 0
- Timeout values must be > 0

### Configuration Testing

Test your configuration before deployment:

```bash
# Validate configuration
python -m src.config.validator config/production.yaml

# Test source connectivity
python -m src.tools.test_sources config/production.yaml

# Dry run (validate without starting)
python -m src.main --config config/production.yaml --dry-run
```

## Best Practices

### Performance Optimization
1. **Polling Intervals**: Set appropriate intervals based on source update frequency
2. **Concurrent Sources**: Limit concurrent sources based on available resources
3. **Content Extraction**: Only extract full content when necessary
4. **Event Buffering**: Size buffers appropriately for expected event volume

### Security
1. **Credentials**: Use environment variables for sensitive data
2. **Webhook Authentication**: Always use authentication for webhooks
3. **IP Restrictions**: Limit webhook access to known IPs when possible
4. **Content Validation**: Validate all incoming content

### Reliability
1. **Retry Logic**: Configure appropriate retry attempts and delays
2. **Health Checks**: Enable health monitoring for all sources
3. **Error Handling**: Set up proper error notification
4. **Backup Sources**: Configure multiple sources for critical news

### Monitoring
1. **Metrics**: Enable Prometheus metrics for monitoring
2. **Logging**: Use appropriate log levels for different environments
3. **Alerts**: Set up alerts for source failures and performance issues
4. **Health Checks**: Monitor service and source health regularly

This configuration guide provides comprehensive coverage of all available options for customizing the News Feeder Service to your specific requirements.