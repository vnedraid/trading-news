"""Base worker class for all news feed workers."""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional

from models.news_item import NewsItem
from models.worker_config import WorkerConfig


class WorkerStatus(Enum):
    """Worker status enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class BaseWorker(ABC):
    """Abstract base class for all news feed workers."""

    def __init__(self, config: WorkerConfig):
        """Initialize the base worker.
        
        Args:
            config: Worker configuration
        """
        self.config = config
        self.name = config.name
        self.worker_id = config.worker_id
        self.status = WorkerStatus.STOPPED
        self._stop_event = asyncio.Event()
        self._logger = logging.getLogger(f"{__name__}.{self.name}")

    @property
    def is_running(self) -> bool:
        """Check if the worker is currently running."""
        return self.status == WorkerStatus.RUNNING

    async def start(self) -> None:
        """Start the worker."""
        if self.status != WorkerStatus.STOPPED:
            self._logger.warning(f"Worker {self.name} is already running or starting")
            return

        self._logger.info(f"Starting worker {self.name}")
        self.status = WorkerStatus.STARTING
        self._stop_event.clear()

        try:
            self.status = WorkerStatus.RUNNING
            await self._run_loop()
        except Exception as e:
            self._logger.error(f"Error in worker {self.name}: {e}")
            self.status = WorkerStatus.ERROR
        finally:
            self.status = WorkerStatus.STOPPED
            self._logger.info(f"Worker {self.name} stopped")

    async def stop(self) -> None:
        """Stop the worker."""
        if self.status in [WorkerStatus.STOPPED, WorkerStatus.STOPPING]:
            return

        self._logger.info(f"Stopping worker {self.name}")
        self.status = WorkerStatus.STOPPING
        self._stop_event.set()

    async def _run_loop(self) -> None:
        """Main worker loop."""
        while not self._stop_event.is_set():
            try:
                # Fetch news from the source
                news_items = await self._fetch_news()
                
                if news_items:
                    self._logger.info(f"Fetched {len(news_items)} news items from {self.name}")
                    # TODO: Send news items to processing workflow
                    await self._process_news_items(news_items)
                
                # Wait for the next polling cycle or stop event
                await self._wait_for_next_cycle()
                
            except Exception as e:
                self._logger.error(f"Error in worker loop for {self.name}: {e}")
                # Continue running despite errors
                await asyncio.sleep(1)

    async def _wait_for_next_cycle(self) -> None:
        """Wait for the next polling cycle."""
        # For now, just wait a short time to prevent tight loop
        # This will be overridden by specific worker implementations
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            pass

    async def _process_news_items(self, news_items: List[NewsItem]) -> None:
        """Process fetched news items.
        
        Args:
            news_items: List of news items to process
        """
        # TODO: Implement sending to Temporal workflow
        self._logger.info(f"Processing {len(news_items)} news items")
        
        for i, item in enumerate(news_items, 1):
            self._logger.info(f"[{i}/{len(news_items)}] Processing: {item.title}")
            self._logger.debug(f"  URL: {item.url}")
            self._logger.debug(f"  Source: {item.source}")
            self._logger.debug(f"  Published: {item.published_at}")
            self._logger.debug(f"  Content length: {len(item.content) if item.content else 0} chars")
            
        self._logger.info(f"Completed processing {len(news_items)} news items")

    @abstractmethod
    async def _fetch_news(self) -> List[NewsItem]:
        """Fetch news from the source.
        
        Returns:
            List of news items
        """
        pass

    def __repr__(self) -> str:
        """String representation of the worker."""
        return f"{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')"