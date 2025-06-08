# News Listener Service - LLM Analysis Implementation

## Overview
This service has been enhanced to include LLM-powered news analysis and PostgreSQL storage capabilities.

## New Features Added

### 1. LLM Analysis Integration
- **Service**: `LLMService` - Integrates with OpenRouter API (Google Gemini 2.0 Flash)
- **Template**: `news-analysis-prompt.md` - Markdown-based prompt template with predefined lists
- **Reference Data**: Uses predefined lists from `unique_sectors.json`, `unique_industries.json`, and `moex_stocks.json`
- **Configuration**: Uses `appsettings.json` for API URL and `appsettings.secrets.json` for API key

### 2. PostgreSQL Database Storage
- **Service**: `PostgreSQLService` - Handles database operations
- **Table**: `analyzed_news` - Stores analyzed news with structured data
- **Features**: JSONB columns for tickers and entities, indexes for performance

### 3. Background Processing
- **Service**: `NewsAnalysisBackgroundService` - Processes news analysis in background
- **Queue**: In-memory queue for news processing
- **Flow**: Workflow → Queue → Background Service → LLM → Database

## Database Schema

```sql
CREATE TABLE analyzed_news (
    id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    link TEXT,
    published_at TIMESTAMP,
    source VARCHAR(500),
    category VARCHAR(100),
    original_sentiment VARCHAR(50),
    analyzed_sentiment VARCHAR(50),
    sector VARCHAR(100),
    industry VARCHAR(200),
    tickers JSONB,
    entities JSONB,
    summary TEXT,
    confidence DECIMAL(5,4),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration Files

### appsettings.json
```json
{
  "OpenRouter": {
    "BaseUrl": "https://openrouter.ai/api/v1",
    "Model": "google/gemini-2.0-flash-001"
  },
  "PostgreSQL": {
    "ConnectionString": "Host=localhost;Port=5432;Database=trading_news;Username=temporal;Password=temporal"
  }
}
```

### appsettings.secrets.json
```json
{
  "OpenRouter": {
    "ApiKey": "sk-or-v1-..."
  }
}
```

## Processing Flow

1. **News Reception**: NewsListenerWorkflow receives news signals
2. **Queue Addition**: News is added to in-memory processing queue
3. **Background Processing**: NewsAnalysisBackgroundService picks up news from queue
4. **LLM Analysis**: News is sent to OpenRouter API for analysis
5. **Data Extraction**: Response is parsed to extract:
   - Related stock tickers
   - Market sector
   - Sentiment analysis
   - Key entities
   - Summary
   - Confidence score
6. **Database Storage**: Analyzed data is saved to PostgreSQL

## LLM Analysis Output

The LLM provides structured analysis in JSON format:
```json
{
  "tickers": ["SBER", "GAZP"],
  "sector": "Финансы",
  "industry": "Банки",
  "sentiment": "positive",
  "entities": ["Сбербанк", "Газпром"],
  "summary": "Brief market relevance summary",
  "confidence": 0.85
}
```

## Enhanced Prompt Template

The system now uses a markdown-based prompt template (`news-analysis-prompt.md`) with the following enhancements:

### Predefined Lists
- **MOEX Tickers**: 300+ Russian stock tickers from Moscow Exchange
- **Russian Sectors**: 12 predefined sectors in Russian language
- **Russian Industries**: 56+ specific industries in Russian language

### Template Structure
- **System Prompt**: Defines the AI's role as a Russian market analyst
- **User Prompt**: Structured analysis request with constraints
- **Constraints**: Strict validation against predefined lists
- **Response Format**: JSON schema with required fields

### Key Features
- **Accuracy**: Only valid MOEX tickers are extracted
- **Consistency**: Standardized sector and industry classifications
- **Localization**: Russian language support for sectors and industries
- **Maintainability**: Easy to update via markdown file

## Dependencies Added

- `Microsoft.Extensions.Http` - HTTP client factory
- `Npgsql` - PostgreSQL driver
- `System.Text.Json` - JSON serialization

## Running the Service

1. Ensure PostgreSQL is running (Docker container: `temporal-postgresql`)
2. Update API key in `appsettings.secrets.json`
3. Run: `dotnet run`

The service will:
- Initialize PostgreSQL table
- Start Temporal workflow
- Begin background news analysis processing
- Process incoming news signals automatically

## Monitoring

The service provides detailed logging for:
- News signal reception
- LLM analysis progress
- Database operations
- Error handling and retries