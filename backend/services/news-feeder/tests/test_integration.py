"""Integration tests for the news feeder service."""

import pytest
import asyncio
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from workers.rss_worker import RSSWorker
from models.worker_config import RSSWorkerConfig


class TestRSSWorkerIntegration:
    """Integration tests for RSS worker with real feeds."""

    @pytest.mark.asyncio
    async def test_rss_worker_with_kommersant_feed(self):
        """Test RSS worker with Kommersant feed (mocked for reliability)."""
        config = RSSWorkerConfig(
            name="kommersant_test",
            worker_id="kommersant_001",
            url="https://www.kommersant.ru/rss/news.xml",
            polling_interval="5m"
        )
        
        worker = RSSWorker(config)
        
        # Mock a realistic RSS response
        mock_feed_data = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Коммерсантъ</title>
                <item>
                    <title>Тестовая новость 1</title>
                    <link>https://www.kommersant.ru/doc/1234567</link>
                    <description>Описание тестовой новости</description>
                    <pubDate>Mon, 01 Jan 2024 12:00:00 +0000</pubDate>
                </item>
                <item>
                    <title>Тестовая новость 2</title>
                    <link>https://www.kommersant.ru/doc/1234568</link>
                    <description>Описание второй тестовой новости</description>
                    <pubDate>Mon, 01 Jan 2024 13:00:00 +0000</pubDate>
                </item>
            </channel>
        </rss>"""
        
        # Create mock feed entries directly
        from unittest.mock import Mock
        
        mock_entry1 = Mock()
        mock_entry1.title = "Тестовая новость 1"
        mock_entry1.link = "https://www.kommersant.ru/doc/1234567"
        mock_entry1.summary = "Описание тестовой новости"
        mock_entry1.published_parsed = None
        
        mock_entry2 = Mock()
        mock_entry2.title = "Тестовая новость 2"
        mock_entry2.link = "https://www.kommersant.ru/doc/1234568"
        mock_entry2.summary = "Описание второй тестовой новости"
        mock_entry2.published_parsed = None
        
        mock_feed = Mock()
        mock_feed.entries = [mock_entry1, mock_entry2]
        
        with patch('workers.rss_worker.feedparser.parse') as mock_parse:
            mock_parse.return_value = mock_feed
            
            # Fetch news
            news_items = await worker._fetch_news()
            
            # Verify results
            assert len(news_items) == 2
            assert news_items[0].title == "Тестовая новость 1"
            assert news_items[0].url == "https://www.kommersant.ru/doc/1234567"
            assert news_items[0].source == "kommersant_test"
            assert news_items[1].title == "Тестовая новость 2"

    @pytest.mark.asyncio
    async def test_worker_lifecycle(self):
        """Test complete worker lifecycle."""
        config = RSSWorkerConfig(
            name="lifecycle_test",
            worker_id="lifecycle_001",
            url="https://example.com/rss.xml",
            polling_interval="1s"  # Short interval for testing
        )
        
        worker = RSSWorker(config)
        
        # Mock feedparser to return empty feed
        with patch('workers.rss_worker.feedparser.parse') as mock_parse:
            mock_feed = type('MockFeed', (), {'entries': []})()
            mock_parse.return_value = mock_feed
            
            # Test worker lifecycle
            assert not worker.is_running
            
            # Start worker
            start_task = asyncio.create_task(worker.start())
            await asyncio.sleep(0.1)  # Let it start
            
            assert worker.is_running
            
            # Stop worker
            await worker.stop()
            await start_task
            
            assert not worker.is_running

    @pytest.mark.asyncio
    async def test_worker_error_recovery(self):
        """Test worker error handling and recovery."""
        config = RSSWorkerConfig(
            name="error_test",
            worker_id="error_001",
            url="https://example.com/rss.xml",
            polling_interval="1s"
        )
        
        worker = RSSWorker(config)
        
        call_count = 0
        
        def mock_parse_with_error(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network error")
            else:
                # Return empty feed on subsequent calls
                return type('MockFeed', (), {'entries': []})()
        
        with patch('workers.rss_worker.feedparser.parse', side_effect=mock_parse_with_error):
            # Start worker
            start_task = asyncio.create_task(worker.start())
            await asyncio.sleep(1.5)  # Let it start, encounter error, and retry
            
            # Worker should still be running despite error
            assert worker.is_running
            
            # Stop worker
            await worker.stop()
            await start_task
            
            # Should have attempted multiple calls (initial + retry after 1s interval)
            assert call_count >= 2