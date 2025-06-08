# Development Guide

This guide covers development setup, testing, debugging, and contribution guidelines for the News Feeder Service.

## Development Environment Setup

### Prerequisites

- **Python 3.13+**: Required runtime
- **uv**: Fast Python package installer and resolver
- **Docker**: For running dependencies
- **Git**: Version control
- **IDE**: VS Code, PyCharm, or similar

### Local Setup

#### 1. Install uv

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

#### 2. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd trading-news/backend/services/feeder

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install production dependencies
uv pip install -r requirements.txt

# Install development dependencies
uv pip install -r requirements-dev.txt
```

#### 3. Development Dependencies

```txt
# requirements-dev.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
black>=23.7.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.5.0
pre-commit>=3.3.0
httpx>=0.24.0
fakeredis>=2.18.0
```

#### 4. Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.13

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Development Dependencies

#### Docker Compose for Development

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes

  temporal:
    image: temporalio/auto-setup:latest
    environment:
      - DB=sqlite
    ports:
      - "7233:7233"
      - "8080:8080"
    volumes:
      - temporal_data:/etc/temporal

  # Test RSS server
  test-rss:
    image: nginx:alpine
    ports:
      - "8888:80"
    volumes:
      - ./tests/fixtures/rss:/usr/share/nginx/html

volumes:
  temporal_data:
```

#### Start Development Environment

```bash
# Start dependencies
docker-compose -f docker-compose.dev.yml up -d

# Verify services
curl http://localhost:8080/  # Temporal UI
redis-cli ping              # Redis
curl http://localhost:8888/test.rss  # Test RSS feed
```

## Project Structure

```
backend/services/feeder/
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   ├── config/            # Configuration management
│   ├── core/              # Core business logic
│   ├── sources/           # Source implementations
│   ├── models/            # Data models
│   ├── temporal_client/   # Temporal integration
│   └── utils/             # Utilities
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── fixtures/          # Test data
│   └── conftest.py        # Pytest configuration
├── docs/                  # Documentation
├── config/                # Configuration files
├── scripts/               # Development scripts
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pyproject.toml         # Project configuration
├── Dockerfile             # Container definition
└── README.md              # Project overview
```

## Development Workflow with uv

### Package Management

```bash
# Add a new dependency
uv add requests

# Add a development dependency
uv add --dev pytest

# Remove a dependency
uv remove requests

# Update all dependencies
uv pip install --upgrade -r requirements.txt

# Sync environment with lock file
uv pip sync requirements.txt

# Generate requirements.txt from pyproject.toml
uv pip compile pyproject.toml -o requirements.txt

# Install from pyproject.toml
uv pip install -e .
```

### Virtual Environment Management

```bash
# Create virtual environment
uv venv

# Create with specific Python version
uv venv --python 3.13

# Activate environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies in one command
uv pip install -r requirements.txt -r requirements-dev.txt

# Run commands in virtual environment without activation
uv run python -m src.main
uv run pytest
```

### Code Style and Formatting

#### Configuration Files

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "news-feeder"
version = "0.1.0"
description = "RSS news feed aggregation service"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "feedparser>=6.0.10",
    "newspaper3k>=0.2.8",
    "temporalio>=1.5.0",
    "redis>=5.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "python-dateutil>=2.8.0",
    "structlog>=23.0.0",
    "aiohttp>=3.9.0",
    "asyncio-throttle>=1.0.2",
    "scrapy>=2.11.0",
    "selenium>=4.15.0",
    "telethon>=1.30.0",
    "readability-lxml>=0.8.1",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "websockets>=12.0",
    "prometheus-client>=0.19.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "black>=23.7.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
    "pre-commit>=3.3.0",
    "httpx>=0.24.0",
    "fakeredis>=2.18.0"
]

[tool.black]
line-length = 88
target-version = ['py313']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
    "external: Tests requiring external services",
]
```

#### Formatting Commands with uv

```bash
# Format code
uv run black src/ tests/
uv run isort src/ tests/

# Lint code
uv run flake8 src/ tests/
uv run mypy src/

# Run all checks
make lint  # or use the script below
```

### Testing

#### Test Structure

```python
# tests/conftest.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fakeredis import FakeRedis
from src.config.settings import FeederConfig
from src.core.duplicate_detector import DuplicateDetector

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    return FakeRedis()

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return FeederConfig(
        sources=[],
        redis_host="localhost",
        redis_port=6379,
        temporal_host="localhost",
        temporal_port=7233
    )

@pytest.fixture
def duplicate_detector(mock_redis):
    """Duplicate detector with mocked Redis."""
    return DuplicateDetector(redis_client=mock_redis)
```

#### Unit Tests

```python
# tests/unit/test_rss_source.py
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from src.sources.polling.rss_source import RSSSource
from src.models.source_config import SourceConfig, PollingConfig

class TestRSSSource:
    @pytest.fixture
    def rss_config(self):
        return SourceConfig(
            type="rss",
            name="Test RSS",
            url="https://example.com/feed.rss",
            update_mechanism="polling",
            polling_config=PollingConfig(interval_seconds=300)
        )

    @pytest.fixture
    def rss_source(self, rss_config):
        return RSSSource(rss_config)

    @pytest.mark.asyncio
    async def test_fetch_items_success(self, rss_source):
        """Test successful RSS feed fetching."""
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = {
                'entries': [
                    {
                        'title': 'Test Article',
                        'link': 'https://example.com/article1',
                        'summary': 'Test summary',
                        'published_parsed': datetime.now().timetuple()
                    }
                ]
            }
            
            items = await rss_source.fetch_items()
            
            assert len(items) == 1
            assert items[0].title == 'Test Article'
            assert items[0].source_name == 'Test RSS'

    @pytest.mark.asyncio
    async def test_fetch_items_network_error(self, rss_source):
        """Test handling of network errors."""
        with patch('feedparser.parse') as mock_parse:
            mock_parse.side_effect = Exception("Network error")
            
            items = await rss_source.fetch_items()
            
            assert items == []

    def test_is_healthy(self, rss_source):
        """Test health check."""
        assert rss_source.is_healthy() == True
```

#### Running Tests with uv

```bash
# Run all tests
uv run pytest

# Run specific test types
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m "not external"  # Skip external tests

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_rss_source.py

# Run with verbose output
uv run pytest -v

# Run tests in parallel
uv run pytest -n auto
```

### Debugging

#### Debug Configuration

```python
# src/utils/debug.py
import logging
import sys
from typing import Any

def setup_debug_logging():
    """Setup debug logging configuration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug.log')
        ]
    )

def debug_print(obj: Any, name: str = "Debug"):
    """Debug print with formatting."""
    print(f"\n=== {name} ===")
    if hasattr(obj, '__dict__'):
        for key, value in obj.__dict__.items():
            print(f"{key}: {value}")
    else:
        print(obj)
    print("=" * (len(name) + 8))
```

#### VS Code Debug Configuration

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Feeder",
            "type": "python",
            "request": "launch",
            "module": "src.main",
            "args": ["--config", "config/development.yaml"],
            "console": "integratedTerminal",
            "python": "${workspaceFolder}/.venv/bin/python",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "LOG_LEVEL": "DEBUG"
            }
        },
        {
            "name": "Debug Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal",
            "python": "${workspaceFolder}/.venv/bin/python",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

### Development Scripts

#### Makefile with uv

```makefile
# Makefile
.PHONY: help install lint test clean dev-up dev-down

help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  lint        Run linting and formatting"
	@echo "  test        Run tests"
	@echo "  clean       Clean up generated files"
	@echo "  dev-up      Start development environment"
	@echo "  dev-down    Stop development environment"

install:
	uv venv
	uv pip install -r requirements.txt -r requirements-dev.txt
	uv run pre-commit install

lint:
	uv run black --check src/ tests/
	uv run isort --check-only src/ tests/
	uv run flake8 src/ tests/
	uv run mypy src/

format:
	uv run black src/ tests/
	uv run isort src/ tests/

test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=html

clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

dev-up:
	docker-compose -f docker-compose.dev.yml up -d

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

run:
	uv run python -m src.main

run-dev:
	uv run python -m src.main --config config/development.yaml
```

#### Development Scripts

```bash
#!/bin/bash
# scripts/dev-setup.sh
set -e

echo "Setting up development environment..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate

# Install all dependencies
uv pip install -r requirements.txt -r requirements-dev.txt

# Install pre-commit hooks
uv run pre-commit install

# Start development services
docker-compose -f docker-compose.dev.yml up -d

echo "Development environment ready!"
echo "Activate virtual environment: source .venv/bin/activate"
echo "Run tests: uv run pytest"
echo "Start feeder: uv run python -m src.main"
```

```bash
#!/bin/bash
# scripts/test-all.sh
set -e

echo "Running complete test suite..."

# Lint and format check
echo "Checking code formatting..."
uv run black --check src/ tests/
uv run isort --check-only src/ tests/

echo "Running linting..."
uv run flake8 src/ tests/
uv run mypy src/

# Run tests
echo "Running unit tests..."
uv run pytest -m unit

echo "Running integration tests..."
uv run pytest -m integration

echo "Running coverage report..."
uv run pytest --cov=src --cov-report=term-missing

echo "All tests passed!"
```

### Performance Profiling

#### Memory Profiling

```python
# scripts/profile_memory.py
import asyncio
import tracemalloc
from src.core.orchestrator import NewsFeederOrchestrator
from src.config.settings import load_config

async def profile_memory():
    """Profile memory usage during operation."""
    tracemalloc.start()
    
    config = load_config("config/development.yaml")
    orchestrator = NewsFeederOrchestrator(config)
    
    # Take initial snapshot
    snapshot1 = tracemalloc.take_snapshot()
    
    # Start orchestrator
    await orchestrator.start()
    
    # Wait for some processing
    await asyncio.sleep(60)
    
    # Take final snapshot
    snapshot2 = tracemalloc.take_snapshot()
    
    # Compare snapshots
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    
    print("Top 10 memory allocations:")
    for stat in top_stats[:10]:
        print(stat)
    
    await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(profile_memory())
```

#### Running Performance Scripts

```bash
# Run memory profiling
uv run python scripts/profile_memory.py

# Run benchmarks
uv run python scripts/benchmark.py
```

### Docker Development

#### Dockerfile for Development

```dockerfile
# Dockerfile.dev
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install dependencies
RUN uv venv && \
    uv pip install -r requirements.txt -r requirements-dev.txt

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY config/ ./config/

# Expose ports
EXPOSE 8090 9000-9099

# Development command with auto-reload
CMD ["uv", "run", "python", "-m", "src.main", "--reload"]
```

## Contributing Guidelines

### Code Review Process

1. **Create Feature Branch**: `git checkout -b feature/your-feature`
2. **Setup Environment**: `uv venv && uv pip install -r requirements.txt -r requirements-dev.txt`
3. **Make Changes**: Follow coding standards
4. **Write Tests**: Ensure good test coverage
5. **Run Tests**: `uv run pytest`
6. **Format Code**: `uv run black src/ tests/ && uv run isort src/ tests/`
7. **Create Pull Request**: Include description and tests
8. **Code Review**: Address reviewer feedback
9. **Merge**: After approval and CI passes

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(rss): add support for Atom feeds
fix(telegram): handle connection timeouts
docs(api): update configuration examples
test(sources): add integration tests for webhooks
```

### Release Process

1. **Version Bump**: Update version in `pyproject.toml`
2. **Update Dependencies**: `uv pip compile pyproject.toml -o requirements.txt`
3. **Changelog**: Update `CHANGELOG.md`
4. **Tag Release**: `git tag v1.0.0`
5. **Build Image**: `docker build -t news-feeder:1.0.0`
6. **Deploy**: Follow deployment guide

This development guide provides comprehensive coverage for setting up, developing, testing, and contributing to the News Feeder Service using the uv package manager.