# Развертывание чат-бота для трейдеров

## Обзор развертывания

Система развертывается с использованием Docker Compose для обеспечения простоты настройки и консистентности окружения. Все компоненты упакованы в контейнеры и оркестрируются через единый docker-compose файл.

## Docker-композиция архитектуры

```mermaid
graph TB
    subgraph "Docker Compose Environment"
        subgraph "Frontend Container"
            Vue[Vue.js App<br/>:3000]
        end
        
        subgraph "Temporal Stack"
            TS[Temporal Server<br/>:7233]
            TUI[Temporal Web UI<br/>:8080]
            TSql[(Temporal PostgreSQL<br/>:5432)]
        end
        
        subgraph "Application Containers"
            Worker1[Chat Worker<br/>Container]
            Worker2[News Worker<br/>Container]
            Worker3[Analytics Worker<br/>Container]
            Worker4[API Gateway Worker<br/>Container]
        end
        
        subgraph "Data Services"
            AppDB[(App PostgreSQL<br/>:5433)]
            Redis[Redis Cache<br/>:6379]
        end
        
        subgraph "External Services"
            LangGraph[LangGraph Service<br/>:8000]
        end
    end
    
    Vue --> Worker4
    Worker4 --> TS
    Worker1 --> TS
    Worker2 --> TS
    Worker3 --> TS
    
    TS --> TSql
    TS --> TUI
    
    Worker1 --> AppDB
    Worker2 --> AppDB
    Worker3 --> Redis
    Worker4 --> LangGraph
```

## Основной Docker Compose файл

### docker-compose.yml

```yaml
version: '3.8'

services:
  # Temporal Server Infrastructure
  temporal-postgresql:
    image: postgres:13
    container_name: temporal-db
    environment:
      POSTGRES_PASSWORD: temporal
      POSTGRES_USER: temporal
      POSTGRES_DB: temporal
    ports:
      - "5432:5432"
    volumes:
      - temporal_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U temporal"]
      interval: 10s
      timeout: 5s
      retries: 5

  temporal-server:
    image: temporalio/auto-setup:latest
    container_name: temporal-server
    depends_on:
      temporal-postgresql:
        condition: service_healthy
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=temporal-postgresql
    ports:
      - "7233:7233"
    healthcheck:
      test: ["CMD", "tctl", "--address", "temporal-server:7233", "workflow", "list"]
      interval: 30s
      timeout: 10s
      retries: 5

  temporal-web:
    image: temporalio/web:latest
    container_name: temporal-web
    depends_on:
      temporal-server:
        condition: service_healthy
    environment:
      - TEMPORAL_GRPC_ENDPOINT=temporal-server:7233
    ports:
      - "8080:8080"

  # Application Database
  app-postgresql:
    image: postgres:13
    container_name: app-db
    environment:
      POSTGRES_PASSWORD: apppass
      POSTGRES_USER: appuser
      POSTGRES_DB: trading_news
    ports:
      - "5433:5432"
    volumes:
      - app_postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d trading_news"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: redis-cache
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # LangGraph Service
  langgraph-service:
    build:
      context: ./langgraph_service
      dockerfile: Dockerfile
    container_name: langgraph-service
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
    ports:
      - "8000:8000"
    depends_on:
      redis:
        condition: service_healthy

  # Temporal Workers
  chat-worker:
    build:
      context: ./temporal_app
      dockerfile: Dockerfile.worker
    container_name: chat-worker
    environment:
      - TEMPORAL_HOST=temporal-server:7233
      - DATABASE_URL=postgresql://appuser:apppass@app-postgresql:5432/trading_news
      - REDIS_URL=redis://redis:6379
      - WORKER_TYPE=chat
      - LANGGRAPH_URL=http://langgraph-service:8000
    depends_on:
      temporal-server:
        condition: service_healthy
      app-postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
      langgraph-service:
        condition: service_started
    restart: unless-stopped

  news-worker:
    build:
      context: ./temporal_app
      dockerfile: Dockerfile.worker
    container_name: news-worker
    environment:
      - TEMPORAL_HOST=temporal-server:7233
      - DATABASE_URL=postgresql://appuser:apppass@app-postgresql:5432/trading_news
      - REDIS_URL=redis://redis:6379
      - WORKER_TYPE=news
      - ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
    depends_on:
      temporal-server:
        condition: service_healthy
      app-postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  analytics-worker:
    build:
      context: ./temporal_app
      dockerfile: Dockerfile.worker
    container_name: analytics-worker
    environment:
      - TEMPORAL_HOST=temporal-server:7233
      - DATABASE_URL=postgresql://appuser:apppass@app-postgresql:5432/trading_news
      - REDIS_URL=redis://redis:6379
      - WORKER_TYPE=analytics
      - LANGGRAPH_URL=http://langgraph-service:8000
    depends_on:
      temporal-server:
        condition: service_healthy
      app-postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
      langgraph-service:
        condition: service_started
    restart: unless-stopped

  api-gateway-worker:
    build:
      context: ./temporal_app
      dockerfile: Dockerfile.worker
    container_name: api-gateway-worker
    environment:
      - TEMPORAL_HOST=temporal-server:7233
      - DATABASE_URL=postgresql://appuser:apppass@app-postgresql:5432/trading_news
      - REDIS_URL=redis://redis:6379
      - WORKER_TYPE=api_gateway
    ports:
      - "8001:8001"
    depends_on:
      temporal-server:
        condition: service_healthy
      app-postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8001
      - VITE_WS_URL=ws://localhost:8001
    depends_on:
      - api-gateway-worker
    restart: unless-stopped

volumes:
  temporal_postgres_data:
    driver: local
  app_postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  default:
    name: trading-news-network
    driver: bridge
```

## Dockerfiles

### Dockerfile для Temporal Workers

```dockerfile
# temporal_app/Dockerfile.worker
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

CMD ["python", "worker_main.py"]
```

### Dockerfile для Frontend

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

### Dockerfile для LangGraph Service

```dockerfile
# langgraph_service/Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Environment файлы

### .env.example
```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# Database URLs
DATABASE_URL=postgresql://appuser:apppass@localhost:5433/trading_news

# Redis
REDIS_URL=redis://localhost:6379

# Temporal
TEMPORAL_HOST=localhost:7233

# Development
DEBUG=true
LOG_LEVEL=INFO
```

## Скрипты развертывания

### Makefile

```makefile
.PHONY: help up down build logs clean init status

help:
	@echo "Доступные команды:"
	@echo "  up          - Запустить все сервисы"
	@echo "  down        - Остановить все сервисы"
	@echo "  build       - Собрать все образы"
	@echo "  logs        - Показать логи всех сервисов"
	@echo "  clean       - Очистить все данные и образы"
	@echo "  init        - Инициализировать проект"
	@echo "  status      - Показать состояние сервисов"

up:
	@echo "Запуск Trading News Bot..."
	docker-compose up -d
	@echo "Сервисы запущены:"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - Temporal Web UI: http://localhost:8080"
	@echo "  - API Gateway: http://localhost:8001"

down:
	@echo "Остановка сервисов..."
	docker-compose down

build:
	@echo "Сборка образов..."
	docker-compose build --no-cache

logs:
	docker-compose logs -f

clean:
	@echo "Очистка данных и образов..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

init:
	@echo "Инициализация проекта..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Создан .env файл"; fi
	@echo "Обновите .env файл с вашими API ключами"
	$(MAKE) build
	$(MAKE) up
	@echo "Проект готов к использованию!"

status:
	@echo "Состояние сервисов:"
	docker-compose ps
```

### Скрипт инициализации

```bash
#!/bin/bash
# scripts/init.sh

set -e

echo "🚀 Инициализация Trading News Bot..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

# Создание .env файла
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp .env.example .env
    echo "✅ .env файл создан"
    echo "Обновите его с вашими API ключами"
    read -p "Нажмите Enter после обновления .env файла..."
fi

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p logs backups temporal-config

# Сборка образов
echo "🔨 Сборка Docker образов..."
docker-compose build

# Запуск сервисов
echo "🚀 Запуск сервисов..."
docker-compose up -d

# Ожидание готовности
echo "⏳ Ожидание готовности сервисов..."
sleep 30

echo "🎉 Инициализация завершена!"
echo "📱 Доступ к приложению:"
echo "   - Frontend: http://localhost:3000"
echo "   - Temporal Web UI: http://localhost:8080"
echo "   - API Gateway: http://localhost:8001"
```

## Database initialization

### scripts/init-db.sql
```sql
-- Создание схемы базы данных
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    preferences JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица новостей
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    source VARCHAR(100) NOT NULL,
    url TEXT UNIQUE,
    sentiment_score FLOAT,
    symbols TEXT[],
    tags TEXT[],
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица истории чатов
CREATE TABLE IF NOT EXISTS chats (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(100),
    message TEXT NOT NULL,
    response TEXT,
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_news_created_at ON news(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_symbols ON news USING GIN(symbols);
CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id);
CREATE INDEX IF NOT EXISTS idx_chats_created_at ON chats(created_at DESC);
```

## Инструкции по развертыванию

### Быстрый старт

1. **Клонирование репозитория**
   ```bash
   git clone <repository-url>
   cd trading-news
   ```

2. **Инициализация проекта**
   ```bash
   chmod +x scripts/init.sh
   ./scripts/init.sh
   ```

3. **Настройка API ключей**
   ```bash
   nano .env
   ```

4. **Запуск системы**
   ```bash
   make up
   ```

### Мониторинг и отладка

1. **Просмотр логов**
   ```bash
   make logs
   ```

2. **Проверка состояния**
   ```bash
   make status
   ```

3. **Подключение к контейнеру**
   ```bash
   docker-compose exec chat-worker bash
   ```

### Масштабирование

```bash
docker-compose up -d --scale chat-worker=3 --scale news-worker=2
```

### Резервное копирование

```bash
# Создание резервной копии
docker-compose exec app-postgresql pg_dump -U appuser trading_news > backup.sql

# Восстановление
docker-compose exec -T app-postgresql psql -U appuser -d trading_news < backup.sql
```

Эта конфигурация обеспечивает надежное и масштабируемое развертывание системы с минимальными усилиями по настройке.