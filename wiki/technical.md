# Техническое описание чат-бота для трейдеров

## Обзор технического решения

Чат-бот для трейдеров представляет собой современное микросервисное приложение, построенное на базе Temporal как центральной платформы для управления бизнес-процессами. Система обеспечивает надежный сбор, обработку и анализ финансовых новостей с использованием передовых AI технологий.

## Технологический стек

### Backend Technologies

#### Core Platform
- **Temporal**: Платформа для надежного выполнения workflow
  - Версия: latest (1.20+)
  - Назначение: Оркестрация всех бизнес-процессов
  - Преимущества: Durability, observability, scalability

- **Python 3.11**: Основной язык разработки
  - Выбор обусловлен: богатая экосистема для AI/ML, отличная поддержка Temporal

- **temporalio**: Python SDK для Temporal
  - Версия: 1.4+
  - Функции: Workflow definitions, activity implementations

#### AI/ML Stack
- **LangGraph**: AI workflow engine
  - Назначение: Управление сложными AI процессами
  - Интеграция: Граф состояний для обработки запросов

- **OpenAI API**: Large Language Model
  - Модель: GPT-4 или GPT-3.5-turbo
  - Использование: Генерация ответов, анализ текста

- **TextBlob/VADER**: Анализ настроений
  - Назначение: Определение тональности новостей
  - Альтернатива: Transformers-based models

#### Data Storage
- **PostgreSQL 13+**: Основная реляционная БД
  - Схема: Пользователи, новости, чаты, аналитика
  - Расширения: UUID, JSONB, GIN индексы

- **Redis 7**: Кэширование и временное хранение
  - Использование: Session storage, cache, pub/sub
  - Конфигурация: Persistence enabled

#### Web Framework
- **FastAPI**: HTTP API (через Temporal Activities)
  - Версия: 0.100+
  - Особенности: Async support, automatic OpenAPI docs

- **WebSocket**: Real-time коммуникация
  - Реализация: Через Temporal workflow
  - Назначение: Live updates, chat interface

### Frontend Technologies

#### Core Framework
- **Vue.js 3**: Прогрессивный JavaScript фреймворк
  - Версия: 3.3+
  - Composition API для лучшей организации кода
  - TypeScript support

- **Vite**: Build tool и dev server
  - Быстрая разработка и сборка
  - Hot Module Replacement (HMR)

#### UI Components
- **TradingView Charting Library**: Финансовые графики
  - Интерактивные графики цен
  - Технические индикаторы
  - Customizable interface

- **Element Plus / Vuetify**: UI компоненты
  - Готовые компоненты для быстрой разработки
  - Responsive design

#### State Management
- **Pinia**: Современный state management
  - Замена Vuex для Vue 3
  - TypeScript support
  - Devtools integration

### Infrastructure

#### Containerization
- **Docker**: Контейнеризация приложений
  - Multi-stage builds для оптимизации размера
  - Health checks для мониторинга

- **Docker Compose**: Локальная оркестрация
  - Определение всех сервисов
  - Управление зависимостями
  - Volume management

#### Networking
- **Nginx**: Reverse proxy (опционально)
  - Load balancing
  - SSL termination
  - Static file serving

## Архитектурные паттерны

### Temporal Patterns

#### Workflow Patterns
```python
# Saga Pattern для распределенных транзакций
@workflow.defn
class NewsProcessingSaga:
    @workflow.run
    async def run(self, news_items: List[NewsItem]) -> ProcessingResult:
        compensations = []
        try:
            # Step 1: Validate news
            validated = await workflow.execute_activity(
                validate_news, news_items
            )
            compensations.append(lambda: self.rollback_validation(validated))
            
            # Step 2: Analyze sentiment
            analyzed = await workflow.execute_activity(
                analyze_sentiment_batch, validated
            )
            compensations.append(lambda: self.rollback_analysis(analyzed))
            
            # Step 3: Save to database
            saved = await workflow.execute_activity(
                save_news_batch, analyzed
            )
            
            return ProcessingResult(success=True, processed=saved)
            
        except Exception as e:
            # Execute compensations in reverse order
            for compensation in reversed(compensations):
                await compensation()
            raise
```

#### Activity Patterns
```python
# Retry Pattern с экспоненциальным backoff
@activity.defn(
    retry_policy=RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(minutes=5),
        maximum_attempts=5
    )
)
async def fetch_external_api(url: str) -> APIResponse:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return APIResponse.parse_obj(response.json())
```

### Data Access Patterns

#### Repository Pattern
```python
class NewsRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create(self, news_item: NewsCreate) -> News:
        db_news = News(**news_item.dict())
        self.db.add(db_news)
        await self.db.commit()
        await self.db.refresh(db_news)
        return db_news
    
    async def get_by_symbols(self, symbols: List[str]) -> List[News]:
        query = select(News).where(News.symbols.overlap(symbols))
        result = await self.db.execute(query)
        return result.scalars().all()
```

#### Unit of Work Pattern
```python
class UnitOfWork:
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory
    
    async def __aenter__(self):
        self.session = self.session_factory()
        self.news_repo = NewsRepository(self.session)
        self.chat_repo = ChatRepository(self.session)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
```

### AI/ML Patterns

#### Chain of Responsibility для AI Processing
```python
class AIProcessingChain:
    def __init__(self):
        self.handlers = []
    
    def add_handler(self, handler: AIHandler):
        self.handlers.append(handler)
    
    async def process(self, request: AIRequest) -> AIResponse:
        for handler in self.handlers:
            if await handler.can_handle(request):
                return await handler.handle(request)
        raise ValueError("No handler found for request")

# Handlers
class SentimentAnalysisHandler(AIHandler):
    async def can_handle(self, request: AIRequest) -> bool:
        return request.type == "sentiment_analysis"
    
    async def handle(self, request: AIRequest) -> AIResponse:
        # Sentiment analysis logic
        pass

class ChatResponseHandler(AIHandler):
    async def can_handle(self, request: AIRequest) -> bool:
        return request.type == "chat_response"
    
    async def handle(self, request: AIRequest) -> AIResponse:
        # Chat response generation logic
        pass
```

## Data Models

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    preferences JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### News Table
```sql
CREATE TABLE news (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    source VARCHAR(100) NOT NULL,
    url TEXT UNIQUE,
    sentiment_score FLOAT CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    symbols TEXT[],
    tags TEXT[],
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT unique_url UNIQUE (url)
);

-- Performance indexes
CREATE INDEX idx_news_created_at ON news(created_at DESC);
CREATE INDEX idx_news_symbols ON news USING GIN(symbols);
CREATE INDEX idx_news_sentiment ON news(sentiment_score) WHERE sentiment_score IS NOT NULL;
CREATE INDEX idx_news_source_date ON news(source, created_at DESC);
```

#### Chats Table
```sql
CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(100),
    message TEXT NOT NULL,
    response TEXT,
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_chats_user_session (user_id, session_id),
    INDEX idx_chats_created_at (created_at DESC)
);
```

### Pydantic Models

#### Request/Response Models
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ChatRequest(BaseModel):
    user_id: int
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    message: str
    context: Dict[str, Any]
    processing_time_ms: int
    sources: List[str] = []

class NewsItem(BaseModel):
    title: str
    content: Optional[str] = None
    source: str
    url: str
    symbols: List[str] = []
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    published_at: Optional[datetime] = None

class AnalyticsRequest(BaseModel):
    symbols: List[str]
    analysis_type: str = Field(..., regex="^(sentiment|technical|fundamental)$")
    time_range: str = Field("1d", regex="^(1h|1d|1w|1m)$")
```

## API Specifications

### REST API Endpoints

#### Chat Endpoints
```python
# POST /api/v1/chat
{
    "user_id": 123,
    "session_id": "session_uuid",
    "message": "Что думаешь о акциях Apple?"
}

# Response
{
    "message": "На основе последних новостей...",
    "context": {"symbols": ["AAPL"], "sentiment": "positive"},
    "processing_time_ms": 1250,
    "sources": ["https://cnbc.com/...", "https://reuters.com/..."]
}
```

#### News Endpoints
```python
# GET /api/v1/news?symbols=AAPL,GOOGL&limit=10
{
    "news": [
        {
            "id": "uuid",
            "title": "Apple Reports Strong Q4 Results",
            "summary": "Apple exceeded expectations...",
            "sentiment_score": 0.8,
            "symbols": ["AAPL"],
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "total": 150,
    "page": 1,
    "limit": 10
}
```

#### Analytics Endpoints
```python
# POST /api/v1/analytics
{
    "symbols": ["AAPL", "GOOGL"],
    "analysis_type": "sentiment",
    "time_range": "1d"
}

# Response
{
    "analysis": "Общий настрой по AAPL положительный...",
    "metrics": {
        "AAPL": {"sentiment": 0.7, "news_count": 15},
        "GOOGL": {"sentiment": 0.3, "news_count": 8}
    },
    "generated_at": "2024-01-15T15:30:00Z"
}
```

### WebSocket API

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

// Authentication
ws.send(JSON.stringify({
    type: 'auth',
    token: 'jwt_token_here'
}));
```

#### Chat Messages
```javascript
// Send message
ws.send(JSON.stringify({
    type: 'chat',
    session_id: 'session_uuid',
    message: 'Анализ рынка на сегодня'
}));

// Receive response
{
    type: 'chat_response',
    session_id: 'session_uuid',
    message: 'Сегодняшний рынок показывает...',
    context: {...}
}
```

#### Real-time Updates
```javascript
// News updates
{
    type: 'news_update',
    news: {
        title: 'Breaking: Fed Raises Interest Rates',
        symbols: ['SPY', 'QQQ'],
        sentiment_score: -0.3
    }
}

// Market alerts
{
    type: 'market_alert',
    symbol: 'AAPL',
    message: 'Significant price movement detected',
    change_percent: -5.2
}
```

## Performance Considerations

### Database Optimization

#### Indexing Strategy
```sql
-- Composite indexes for common queries
CREATE INDEX idx_news_symbol_date ON news(symbols, created_at DESC) 
WHERE array_length(symbols, 1) > 0;

-- Partial indexes for active data
CREATE INDEX idx_active_users ON users(id) WHERE is_active = true;

-- Expression indexes for JSON queries
CREATE INDEX idx_chat_context_symbols ON chats 
USING GIN((context->'symbols')) WHERE context ? 'symbols';
```

#### Query Optimization
```python
# Efficient pagination with cursor-based approach
async def get_news_paginated(
    cursor: Optional[datetime] = None,
    limit: int = 20,
    symbols: Optional[List[str]] = None
) -> List[News]:
    query = select(News).order_by(News.created_at.desc())
    
    if cursor:
        query = query.where(News.created_at < cursor)
    
    if symbols:
        query = query.where(News.symbols.overlap(symbols))
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()
```

### Caching Strategy

#### Redis Caching Patterns
```python
class CacheManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def get_or_set(
        self, 
        key: str, 
        factory: Callable[[], Awaitable[Any]], 
        ttl: int = 3600
    ) -> Any:
        # Try to get from cache
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Generate and cache
        value = await factory()
        await self.redis.setex(key, ttl, json.dumps(value, default=str))
        return value

# Usage
cache_manager = CacheManager(redis_client)

async def get_market_analysis(symbols: List[str]) -> Dict:
    cache_key = f"analysis:{':'.join(sorted(symbols))}"
    return await cache_manager.get_or_set(
        cache_key,
        lambda: generate_analysis(symbols),
        ttl=1800  # 30 minutes
    )
```

### Temporal Optimization

#### Worker Scaling
```python
# Dynamic worker scaling based on queue size
@activity.defn
async def scale_workers_if_needed():
    queue_size = await get_temporal_queue_size()
    current_workers = await get_active_worker_count()
    
    if queue_size > current_workers * 10:  # Scale up
        await spawn_additional_workers(min(queue_size // 10, 5))
    elif queue_size < current_workers * 2:  # Scale down
        await terminate_excess_workers(current_workers - queue_size // 2)
```

#### Workflow Optimization
```python
# Parallel execution of independent activities
@workflow.defn
class OptimizedNewsProcessing:
    @workflow.run
    async def run(self, news_items: List[NewsItem]) -> ProcessingResult:
        # Process in parallel batches
        batch_size = 10
        batches = [news_items[i:i+batch_size] 
                  for i in range(0, len(news_items), batch_size)]
        
        # Execute all batches in parallel
        tasks = [
            workflow.execute_activity(
                process_news_batch, batch,
                start_to_close_timeout=timedelta(minutes=5)
            )
            for batch in batches
        ]
        
        results = await asyncio.gather(*tasks)
        return ProcessingResult(processed=sum(results, []))
```

## Security Considerations

### Authentication & Authorization
```python
from jose import JWTError, jwt
from passlib.context import CryptContext

class SecurityManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt
```

### Input Validation
```python
from pydantic import validator, Field
import re

class SecureChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    
    @validator('message')
    def validate_message(cls, v):
        # Remove potentially dangerous content
        if re.search(r'<script|javascript:|data:', v, re.IGNORECASE):
            raise ValueError('Invalid message content')
        return v.strip()
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    # Chat logic here
    pass
```

## Monitoring and Observability

### Logging Configuration
```python
import structlog
from pythonjsonlogger import jsonlogger

# Structured logging setup
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in activities
@activity.defn
async def process_news_with_logging(news_item: NewsItem) -> ProcessedNews:
    logger.info("Processing news item", 
                title=news_item.title, 
                source=news_item.source)
    
    try:
        result = await process_news(news_item)
        logger.info("News processed successfully", 
                   processing_time_ms=result.processing_time)
        return result
    except Exception as e:
        logger.error("News processing failed", 
                    error=str(e), 
                    news_id=news_item.id)
        raise
```

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
news_processed_total = Counter('news_processed_total', 'Total news items processed')
chat_response_time = Histogram('chat_response_seconds', 'Chat response time')
active_users = Gauge('active_users_total', 'Number of active users')

# Usage in code
@activity.defn
async def process_chat_with_metrics(request: ChatRequest) -> ChatResponse:
    start_time = time.time()
    
    try:
        response = await process_chat(request)
        chat_response_time.observe(time.time() - start_time)
        return response
    except Exception as e:
        chat_errors_total.inc()
        raise
```

Это техническое описание обеспечивает полное понимание архитектурных решений, паттернов проектирования и технических деталей реализации чат-бота для трейдеров.