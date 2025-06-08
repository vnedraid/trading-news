#!/usr/bin/env python3
"""
Demo script to show RSS worker functionality.
"""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from workers.rss_worker import RSSWorker
from models.worker_config import RSSWorkerConfig


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
    logging.getLogger('workers.base_worker').setLevel(logging.DEBUG)
    logging.getLogger('workers.rss_worker').setLevel(logging.DEBUG)


async def demo_rss_worker():
    """Demonstrate RSS worker functionality."""
    print("🚀 News Feeder Service - RSS Worker Demo")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Create RSS worker configuration
    config = RSSWorkerConfig(
        name="kommersant_demo",
        worker_id="demo_001",
        url="https://www.kommersant.ru/rss/news.xml",
        polling_interval="10s",  # Short interval for demo
        timeout="30s",
        max_retries=3
    )
    
    print(f"📰 Creating RSS worker for: {config.url}")
    print(f"⏱️  Polling interval: {config.polling_interval}")
    print(f"🔧 Worker ID: {config.worker_id}")
    print()
    
    # Create worker
    worker = RSSWorker(config)
    
    try:
        print("🔄 Fetching news from RSS feed...")
        news_items = await worker._fetch_news()
        
        print(f"✅ Successfully fetched {len(news_items)} news items!")
        print()
        
        # Display first few news items
        for i, item in enumerate(news_items[:5], 1):
            print(f"📄 News Item {i}:")
            print(f"   Title: {item.title}")
            print(f"   URL: {item.url}")
            print(f"   Source: {item.source}")
            if item.published_at:
                print(f"   Published: {item.published_at}")
            print(f"   Created: {item.created_at}")
            print()
        
        if len(news_items) > 5:
            print(f"... and {len(news_items) - 5} more items")
            print()
        
        print("🎯 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error fetching news: {e}")
        print("This might be due to network issues or RSS feed unavailability.")
        print("The worker is designed to handle such errors gracefully in production.")


async def demo_worker_lifecycle():
    """Demonstrate worker lifecycle management."""
    print("\n" + "=" * 50)
    print("🔄 Worker Lifecycle Demo")
    print("=" * 50)
    
    config = RSSWorkerConfig(
        name="lifecycle_demo",
        worker_id="lifecycle_001",
        url="https://www.kommersant.ru/rss/news.xml",
        polling_interval="5s"
    )
    
    worker = RSSWorker(config)
    
    print(f"📊 Initial worker status: {worker.status.value}")
    print(f"🏃 Is running: {worker.is_running}")
    print()
    
    print("▶️  Starting worker...")
    start_task = asyncio.create_task(worker.start())
    await asyncio.sleep(0.1)  # Let it start
    
    print(f"📊 Worker status: {worker.status.value}")
    print(f"🏃 Is running: {worker.is_running}")
    print()
    
    print("⏳ Letting worker run for a few seconds...")
    await asyncio.sleep(2)
    
    print("⏹️  Stopping worker...")
    await worker.stop()
    await start_task
    
    print(f"📊 Final worker status: {worker.status.value}")
    print(f"🏃 Is running: {worker.is_running}")
    print()
    
    print("✅ Worker lifecycle demo completed!")


if __name__ == "__main__":
    print("Starting News Feeder Service Demo...")
    print()
    
    asyncio.run(demo_rss_worker())
    asyncio.run(demo_worker_lifecycle())
    
    print("\n🎉 All demos completed!")
    print("The News Feeder Service is ready for integration with Temporal workflows.")