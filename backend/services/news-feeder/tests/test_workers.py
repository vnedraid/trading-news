"""Tests for worker implementations."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from workers.base_worker import BaseWorker, WorkerStatus
from workers.rss_worker import RSSWorker
from workers.worker_factory import WorkerFactory
from models.worker_config import RSSWorkerConfig
from models.news_item import NewsItem


class TestWorkerStatus:
    """Test cases for WorkerStatus enum."""

    def test_worker_status_values(self):
        """Test WorkerStatus enum values."""
        assert WorkerStatus.STOPPED.value == "stopped"
        assert WorkerStatus.STARTING.value == "starting"
        assert WorkerStatus.RUNNING.value == "running"
        assert WorkerStatus.STOPPING.value == "stopping"
        assert WorkerStatus.ERROR.value == "error"


class TestBaseWorker:
    """Test cases for BaseWorker abstract class."""

    def test_base_worker_creation(self):
        """Test creating a BaseWorker instance."""
        config = Mock()
        config.name = "test_worker"
        config.worker_id = "test_001"
        
        # Create a concrete implementation for testing
        class TestWorker(BaseWorker):
            async def _fetch_news(self):
                return []
        
        worker = TestWorker(config)
        
        assert worker.config == config
        assert worker.name == "test_worker"
        assert worker.worker_id == "test_001"
        assert worker.status == WorkerStatus.STOPPED
        assert worker._stop_event is not None

    def test_base_worker_abstract_methods(self):
        """Test that BaseWorker cannot be instantiated directly."""
        config = Mock()
        
        with pytest.raises(TypeError):
            BaseWorker(config)

    @pytest.mark.asyncio
    async def test_base_worker_start_stop(self):
        """Test starting and stopping a worker."""
        config = Mock()
        config.name = "test_worker"
        config.worker_id = "test_001"
        
        class TestWorker(BaseWorker):
            def __init__(self, config):
                super().__init__(config)
                self.fetch_called = False
            
            async def _fetch_news(self):
                self.fetch_called = True
                return []
        
        worker = TestWorker(config)
        
        # Start worker
        start_task = asyncio.create_task(worker.start())
        await asyncio.sleep(0.01)  # Let it start
        
        assert worker.status == WorkerStatus.RUNNING
        
        # Stop worker
        await worker.stop()
        await start_task
        
        assert worker.status == WorkerStatus.STOPPED

    @pytest.mark.asyncio
    async def test_base_worker_error_handling(self):
        """Test error handling in worker."""
        config = Mock()
        config.name = "test_worker"
        config.worker_id = "test_001"
        
        class TestWorker(BaseWorker):
            async def _fetch_news(self):
                raise Exception("Test error")
        
        worker = TestWorker(config)
        
        # Start worker
        start_task = asyncio.create_task(worker.start())
        await asyncio.sleep(0.01)  # Let it start and fail
        
        # Stop worker
        await worker.stop()
        await start_task
        
        assert worker.status == WorkerStatus.STOPPED

    def test_base_worker_is_running(self):
        """Test is_running property."""
        config = Mock()
        config.name = "test_worker"
        config.worker_id = "test_001"
        
        class TestWorker(BaseWorker):
            async def _fetch_news(self):
                return []
        
        worker = TestWorker(config)
        
        assert not worker.is_running
        
        worker.status = WorkerStatus.RUNNING
        assert worker.is_running
        
        worker.status = WorkerStatus.STARTING
        assert not worker.is_running


class TestRSSWorker:
    """Test cases for RSSWorker."""

    def test_rss_worker_creation(self):
        """Test creating an RSSWorker."""
        config = RSSWorkerConfig(
            name="test_rss",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        worker = RSSWorker(config)
        
        assert worker.config == config
        assert worker.name == "test_rss"
        assert worker.worker_id == "rss_001"
        assert worker.status == WorkerStatus.STOPPED

    @pytest.mark.asyncio
    async def test_rss_worker_fetch_news_success(self):
        """Test successful RSS feed fetching."""
        config = RSSWorkerConfig(
            name="test_rss",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        worker = RSSWorker(config)
        
        # Mock feedparser response
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                title="Test News 1",
                link="https://example.com/news/1",
                summary="Test summary 1",
                published_parsed=None
            ),
            Mock(
                title="Test News 2",
                link="https://example.com/news/2",
                summary="Test summary 2",
                published_parsed=None
            )
        ]
        
        with patch('workers.rss_worker.feedparser.parse', return_value=mock_feed):
            news_items = await worker._fetch_news()
        
        assert len(news_items) == 2
        assert all(isinstance(item, NewsItem) for item in news_items)
        assert news_items[0].title == "Test News 1"
        assert news_items[0].url == "https://example.com/news/1"
        assert news_items[0].source == "test_rss"
        assert news_items[1].title == "Test News 2"

    @pytest.mark.asyncio
    async def test_rss_worker_fetch_news_with_published_date(self):
        """Test RSS feed fetching with published dates."""
        config = RSSWorkerConfig(
            name="test_rss",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        worker = RSSWorker(config)
        
        # Mock feedparser response with published date
        import time
        published_time = time.struct_time((2023, 1, 1, 12, 0, 0, 0, 1, 0))
        
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                title="Test News",
                link="https://example.com/news/1",
                summary="Test summary",
                published_parsed=published_time
            )
        ]
        
        with patch('workers.rss_worker.feedparser.parse', return_value=mock_feed):
            news_items = await worker._fetch_news()
        
        assert len(news_items) == 1
        assert news_items[0].published_at is not None
        assert news_items[0].published_at.year == 2023

    @pytest.mark.asyncio
    async def test_rss_worker_fetch_news_empty_feed(self):
        """Test RSS feed fetching with empty feed."""
        config = RSSWorkerConfig(
            name="test_rss",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        worker = RSSWorker(config)
        
        # Mock empty feedparser response
        mock_feed = Mock()
        mock_feed.entries = []
        
        with patch('workers.rss_worker.feedparser.parse', return_value=mock_feed):
            news_items = await worker._fetch_news()
        
        assert len(news_items) == 0

    @pytest.mark.asyncio
    async def test_rss_worker_fetch_news_network_error(self):
        """Test RSS feed fetching with network error."""
        config = RSSWorkerConfig(
            name="test_rss",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        worker = RSSWorker(config)
        
        with patch('workers.rss_worker.feedparser.parse', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Network error"):
                await worker._fetch_news()

    @pytest.mark.asyncio
    async def test_rss_worker_fetch_news_invalid_entry(self):
        """Test RSS feed fetching with invalid entries."""
        config = RSSWorkerConfig(
            name="test_rss",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        worker = RSSWorker(config)
        
        # Mock feedparser response with invalid entry
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                title="",  # Empty title
                link="https://example.com/news/1",
                summary="Test summary",
                published_parsed=None
            ),
            Mock(
                title="Valid News",
                link="https://example.com/news/2",
                summary="Test summary",
                published_parsed=None
            )
        ]
        
        with patch('workers.rss_worker.feedparser.parse', return_value=mock_feed):
            news_items = await worker._fetch_news()
        
        # Should skip invalid entry and return only valid one
        assert len(news_items) == 1
        assert news_items[0].title == "Valid News"

    def test_rss_worker_parse_time_struct(self):
        """Test parsing time struct to datetime."""
        config = RSSWorkerConfig(
            name="test_rss",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        worker = RSSWorker(config)
        
        import time
        time_struct = time.struct_time((2023, 1, 1, 12, 0, 0, 0, 1, 0))
        
        result = worker._parse_time_struct(time_struct)
        
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 1
        # Note: hour may differ due to timezone conversion from local to UTC
        assert result.tzinfo == timezone.utc

    def test_rss_worker_parse_time_struct_none(self):
        """Test parsing None time struct."""
        config = RSSWorkerConfig(
            name="test_rss",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        worker = RSSWorker(config)
        
        result = worker._parse_time_struct(None)
        
        assert result is None


class TestWorkerFactory:
    """Test cases for WorkerFactory."""

    def test_worker_factory_create_rss_worker(self):
        """Test creating RSS worker through factory."""
        config = RSSWorkerConfig(
            name="test_rss",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        worker = WorkerFactory.create_worker(config)
        
        assert isinstance(worker, RSSWorker)
        assert worker.config == config

    def test_worker_factory_unsupported_type(self):
        """Test creating worker with unsupported type."""
        config = Mock()
        config.type = "unsupported"
        
        with pytest.raises(ValueError, match="Unsupported worker type"):
            WorkerFactory.create_worker(config)

    def test_worker_factory_get_supported_types(self):
        """Test getting supported worker types."""
        types = WorkerFactory.get_supported_types()
        
        assert "rss" in types
        assert isinstance(types, list)