#!/usr/bin/env python3
"""
Demo script to show news-tagger functionality.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.news_item import NewsItem
from models.tagger_config import LLMConfig, TaggerConfig
from services.llm_service import LLMService


def setup_logging():
    """Configure logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers to DEBUG for more detailed output
    logging.getLogger('services.llm_service').setLevel(logging.DEBUG)


async def demo_news_tagger():
    """Demonstrate news-tagger functionality with sample news."""
    print("🏷️  News Tagger Service - Demo")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Create sample news items (similar to what news-feeder would provide)
    sample_news = [
        NewsItem(
            title="Мосбиржа с 10 июня запустит торги фьючерсами на апельсиновый сок",
            url="https://www.kommersant.ru/doc/7777077",
            source="kommersant",
            content="Московская биржа объявила о запуске торгов фьючерсными контрактами на апельсиновый сок с 10 июня. Новый инструмент позволит участникам рынка хеджировать риски, связанные с волатильностью цен на сельскохозяйственную продукцию.",
            published_at=datetime.now(timezone.utc)
        ),
        NewsItem(
            title="Boeing договорился с властями США о прекращении преследования за крушения 737 Max",
            url="https://www.kommersant.ru/doc/7776979",
            source="kommersant", 
            content="Компания Boeing достигла соглашения с Министерством юстиции США о прекращении уголовного преследования в связи с двумя авиакатастрофами самолетов 737 Max. Соглашение предусматривает выплату штрафа и усиление мер безопасности.",
            published_at=datetime.now(timezone.utc)
        ),
        NewsItem(
            title="Экспорт российской пшеницы сократится на 20% в текущем сезоне",
            url="https://www.kommersant.ru/doc/7776695",
            source="kommersant",
            content="По данным аналитиков, экспорт российской пшеницы в текущем сельскохозяйственном сезоне может сократиться на 20% по сравнению с предыдущим периодом из-за неблагоприятных погодных условий и снижения урожайности.",
            published_at=datetime.now(timezone.utc)
        )
    ]
    
    print(f"📰 Processing {len(sample_news)} sample news items")
    print()
    
    # Create LLM configuration (using mock/test settings)
    llm_config = LLMConfig(
        api_key="test-key-demo",  # This will fail API calls, but we can test the logic
        model="gpt-4",
        base_url="https://openrouter.ai/api/v1",
        max_tokens=150,
        temperature=0.3,
        timeout=30
    )
    
    # Create tagger configuration
    tagger_config = TaggerConfig(
        llm=llm_config,
        categories=[
            "finance", "trading", "markets", "commodities", "agriculture",
            "aviation", "corporate", "exports", "futures", "derivatives"
        ],
        min_confidence=0.7,
        max_tags=5
    )
    
    print(f"🔧 LLM Model: {tagger_config.llm.model}")
    print(f"🏷️  Available categories: {len(tagger_config.categories)}")
    print(f"📊 Min confidence: {tagger_config.min_confidence}")
    print(f"🔢 Max tags: {tagger_config.max_tags}")
    print()
    
    # Create LLM service
    service = LLMService(tagger_config)
    
    # Process each news item
    for i, news_item in enumerate(sample_news, 1):
        print(f"📄 Processing News Item {i}/{len(sample_news)}")
        print(f"   Title: {news_item.title}")
        print(f"   Source: {news_item.source}")
        print(f"   Content length: {len(news_item.content)} chars")
        print()
        
        try:
            # Test content extraction and validation
            content = service._extract_content(news_item)
            print(f"✅ Content extracted successfully ({len(content)} chars)")
            
            # Test prompt building
            prompt = service._build_prompt(news_item)
            print(f"✅ Prompt built successfully ({len(prompt)} chars)")
            print()
            
            # Note: We won't actually call the LLM API since we don't have valid credentials
            # But we can test the parsing logic with mock responses
            mock_response = {
                "tags": ["finance", "markets", "trading"],
                "confidence_scores": {
                    "finance": 0.95,
                    "markets": 0.87,
                    "trading": 0.72
                }
            }
            
            # Test response parsing
            import json
            mock_response_str = json.dumps(mock_response)
            result = service._parse_llm_response(mock_response_str, tagger_config.llm.model)
            print(f"✅ Mock response parsed successfully")
            print(f"   Tags: {result.tags}")
            print(f"   Confidence scores: {result.confidence_scores}")
            
            # Test filtering
            filtered_result = service._apply_filters(result)
            print(f"✅ Filtering applied successfully")
            print(f"   Filtered tags: {filtered_result.tags}")
            print(f"   Filtered scores: {filtered_result.confidence_scores}")
            print()
            
        except Exception as e:
            print(f"❌ Error processing news item: {e}")
            print()
    
    print("🎯 Demo completed successfully!")
    print("The News Tagger Service is ready to receive news from the feeder service.")


async def demo_integration_simulation():
    """Simulate integration between news-feeder and news-tagger."""
    print("\n" + "=" * 50)
    print("🔄 Integration Simulation Demo")
    print("=" * 50)
    
    # This simulates what would happen when news-feeder sends news to news-tagger
    print("📡 Simulating news-feeder → news-tagger integration...")
    print()
    
    # Sample news item from feeder
    news_from_feeder = NewsItem(
        title="Fix Price обменяет ГДР казахстанского холдинга на акции российского актива",
        url="https://www.kommersant.ru/doc/7776920",
        source="news_feeder_rss",
        content="Компания Fix Price планирует обменять глобальные депозитарные расписки (ГДР) казахстанского холдинга на акции российского актива. Операция направлена на оптимизацию корпоративной структуры и повышение эффективности управления активами.",
        published_at=datetime.now(timezone.utc)
    )
    
    print(f"📨 Received news from feeder:")
    print(f"   Title: {news_from_feeder.title}")
    print(f"   Source: {news_from_feeder.source}")
    print(f"   URL: {news_from_feeder.url}")
    print()
    
    # Create tagger service
    llm_config = LLMConfig(
        api_key="test-integration-key",
        model="gpt-4"
    )
    
    tagger_config = TaggerConfig(
        llm=llm_config,
        categories=["finance", "corporate", "trading", "markets", "retail"],
        min_confidence=0.6,
        max_tags=3
    )
    
    service = LLMService(tagger_config)
    
    print("🏷️  Processing with tagger service...")
    
    # Validate content
    content = service._extract_content(news_from_feeder)
    if content.strip():
        print(f"✅ Content validation passed ({len(content)} chars)")
        
        # Build prompt
        prompt = service._build_prompt(news_from_feeder)
        print(f"✅ Prompt generated ({len(prompt)} chars)")
        
        # Simulate successful tagging (mock response)
        mock_tagged_result = {
            "tags": ["finance", "corporate", "retail"],
            "confidence_scores": {
                "finance": 0.92,
                "corporate": 0.85,
                "retail": 0.78
            }
        }
        
        print(f"✅ Mock tagging completed:")
        print(f"   Generated tags: {mock_tagged_result['tags']}")
        print(f"   Confidence scores: {mock_tagged_result['confidence_scores']}")
        
        # Apply filtering
        import json
        result = service._parse_llm_response(json.dumps(mock_tagged_result), "gpt-4")
        filtered = service._apply_filters(result)
        
        print(f"✅ Filtering applied (min_confidence={tagger_config.min_confidence}):")
        print(f"   Final tags: {filtered.tags}")
        print(f"   Final scores: {filtered.confidence_scores}")
        
        print()
        print("📤 Tagged news would be sent to next workflow stage...")
        
    else:
        print("❌ Content validation failed - no meaningful content")
    
    print()
    print("✅ Integration simulation completed!")


if __name__ == "__main__":
    print("Starting News Tagger Service Demo...")
    print()
    
    asyncio.run(demo_news_tagger())
    asyncio.run(demo_integration_simulation())
    
    print("\n🎉 All demos completed!")
    print("The News Tagger Service is ready for integration with the news-feeder service.")