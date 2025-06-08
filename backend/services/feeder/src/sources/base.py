"""Base source classes and interfaces."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Callable, Any
from dataclasses import dataclass

from ..models.news_item import NewsItem
from ..models.source_config import SourceConfig
from ..models.events import (
    SourceEvent, 
    create_source_started_event,
    create_source_stopped_event,
    create_source_error_event,
)


@dataclass
class SourceMetrics:
    """Metrics for source performance tracking."""
    items_processed: int = 0
    items_failed: int = 0
    last_fetch_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    last_error_message: Optional[str] = None
    average_fetch_time_ms: float = 0.0
    total_fetch_time_ms: float = 0.0
    fetch_count: int = 0
    
    def record_fetch(self, duration_ms: float, items_count: int = 0, error: Optional[str] = None):
        """Record a fetch operation."""
        self.last_fetch_time = datetime.now()
        self.fetch_count += 1
        self.total_fetch_time_ms += duration_ms
        self.average_fetch_time_ms = self.total_fetch_time_ms / self.fetch_count
        
        if error:
            self.items_failed += items_count
            self.last_error_time = datetime.now()
            self.last_error_message = error
        else:
            self.items_processed += items_count


class BaseSource(ABC):
    """Abstract base class for all news sources."""
    
    def __init__(self, config: SourceConfig):
        """Initialize the source with configuration."""
        self.config = config
        self.logger = logging.getLogger(f"source.{config.name}")
        self.metrics = SourceMetrics()
        self._running = False
        self._event_callbacks: List[Callable[[SourceEvent], None]] = []
        self._news_callbacks: List[Callable[[NewsItem], None]] = []
    
    @property
    def name(self) -> str:
        """Get the source name."""
        return self.config.name
    
    @property
    def source_type(self) -> str:
        """Get the source type."""
        return self.config.type
    
    @property
    def url(self) -> str:
        """Get the source URL."""
        return self.config.url
    
    @property
    def is_running(self) -> bool:
        """Check if the source is currently running."""
        return self._running
    
    def add_event_callback(self, callback: Callable[[SourceEvent], None]):
        """Add a callback for source events."""
        self._event_callbacks.append(callback)
    
    def add_news_callback(self, callback: Callable[[NewsItem], None]):
        """Add a callback for news items."""
        self._news_callbacks.append(callback)
    
    def emit_event(self, event: SourceEvent):
        """Emit a source event to all registered callbacks."""
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in event callback: {e}")
    
    def emit_news_item(self, news_item: NewsItem):
        """Emit a news item to all registered callbacks."""
        for callback in self._news_callbacks:
            try:
                callback(news_item)
            except Exception as e:
                self.logger.error(f"Error in news callback: {e}")
    
    @abstractmethod
    async def start(self):
        """Start the source."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the source."""
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if the source is healthy."""
        pass
    
    def get_metrics(self) -> SourceMetrics:
        """Get source metrics."""
        return self.metrics
    
    def _emit_started_event(self):
        """Emit source started event."""
        event = create_source_started_event(
            source_name=self.name,
            source_type=self.source_type,
            source_url=self.url
        )
        self.emit_event(event)
    
    def _emit_stopped_event(self):
        """Emit source stopped event."""
        event = create_source_stopped_event(
            source_name=self.name,
            source_type=self.source_type,
            source_url=self.url
        )
        self.emit_event(event)
    
    def _emit_error_event(self, error_message: str):
        """Emit source error event."""
        event = create_source_error_event(
            source_name=self.name,
            source_type=self.source_type,
            source_url=self.url,
            error_message=error_message
        )
        self.emit_event(event)


class PollingSource(BaseSource):
    """Base class for polling-based sources."""
    
    def __init__(self, config: SourceConfig):
        """Initialize the polling source."""
        super().__init__(config)
        self._polling_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        if not config.polling_config:
            raise ValueError("Polling configuration is required for polling sources")
        
        self.polling_config = config.polling_config
    
    @abstractmethod
    async def fetch_items(self) -> List[NewsItem]:
        """Fetch news items from the source."""
        pass
    
    async def start(self):
        """Start the polling source."""
        if self._running:
            self.logger.warning("Source is already running")
            return
        
        self._running = True
        self._stop_event.clear()
        self._emit_started_event()
        
        # Start polling task
        self._polling_task = asyncio.create_task(self._polling_loop())
        self.logger.info(f"Started polling source '{self.name}' with interval {self.polling_config.interval_seconds}s")
    
    async def stop(self):
        """Stop the polling source."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        # Cancel polling task
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        self._emit_stopped_event()
        self.logger.info(f"Stopped polling source '{self.name}'")
    
    async def _polling_loop(self):
        """Main polling loop."""
        while not self._stop_event.is_set():
            try:
                start_time = datetime.now()
                
                # Fetch items
                items = await self.fetch_items()
                
                # Calculate fetch time
                fetch_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                # Emit news items
                for item in items:
                    self.emit_news_item(item)
                
                # Record metrics
                self.metrics.record_fetch(fetch_time_ms, len(items))
                
                self.logger.debug(f"Fetched {len(items)} items in {fetch_time_ms:.2f}ms")
                
            except Exception as e:
                error_msg = f"Error fetching items: {e}"
                self.logger.error(error_msg)
                self.metrics.record_fetch(0, 0, error_msg)
                self._emit_error_event(error_msg)
            
            # Wait for next polling interval or stop event
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.polling_config.interval_seconds
                )
                break  # Stop event was set
            except asyncio.TimeoutError:
                continue  # Continue polling
    
    def is_healthy(self) -> bool:
        """Check if the polling source is healthy."""
        if not self._running:
            return False
        
        # Check if we've had recent successful fetches
        if self.metrics.last_fetch_time:
            time_since_last_fetch = datetime.now() - self.metrics.last_fetch_time
            max_interval = self.polling_config.interval_seconds * 2  # Allow 2x interval
            if time_since_last_fetch.total_seconds() > max_interval:
                return False
        
        # Check error rate
        if self.metrics.fetch_count > 0:
            error_rate = self.metrics.items_failed / (self.metrics.items_processed + self.metrics.items_failed)
            if error_rate > 0.5:  # More than 50% error rate
                return False
        
        return True


class EventSource(BaseSource):
    """Base class for event-driven sources."""
    
    def __init__(self, config: SourceConfig):
        """Initialize the event source."""
        super().__init__(config)
        self._event_buffer: List[Any] = []
        self._buffer_lock = asyncio.Lock()
        self._processing_task: Optional[asyncio.Task] = None
        
        if not config.event_config:
            raise ValueError("Event configuration is required for event sources")
        
        self.event_config = config.event_config
    
    @abstractmethod
    async def setup_listeners(self):
        """Setup event listeners for the source."""
        pass
    
    @abstractmethod
    async def cleanup_listeners(self):
        """Cleanup event listeners for the source."""
        pass
    
    @abstractmethod
    async def handle_event(self, event: Any) -> Optional[NewsItem]:
        """Handle an incoming event and convert to NewsItem."""
        pass
    
    async def start(self):
        """Start the event source."""
        if self._running:
            self.logger.warning("Source is already running")
            return
        
        self._running = True
        self._emit_started_event()
        
        try:
            # Setup listeners
            await self.setup_listeners()
            
            # Start event processing task
            self._processing_task = asyncio.create_task(self._process_events())
            
            self.logger.info(f"Started event source '{self.name}'")
            
        except Exception as e:
            self._running = False
            error_msg = f"Failed to start event source: {e}"
            self.logger.error(error_msg)
            self._emit_error_event(error_msg)
            raise
    
    async def stop(self):
        """Stop the event source."""
        if not self._running:
            return
        
        self._running = False
        
        try:
            # Cleanup listeners
            await self.cleanup_listeners()
            
            # Cancel processing task
            if self._processing_task:
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass
            
            self._emit_stopped_event()
            self.logger.info(f"Stopped event source '{self.name}'")
            
        except Exception as e:
            error_msg = f"Error stopping event source: {e}"
            self.logger.error(error_msg)
            self._emit_error_event(error_msg)
    
    async def queue_event(self, event: Any):
        """Queue an event for processing."""
        async with self._buffer_lock:
            # Check buffer size limit
            if len(self._event_buffer) >= self.event_config.event_buffer_size:
                # Remove oldest event
                self._event_buffer.pop(0)
                self.logger.warning("Event buffer full, dropping oldest event")
            
            self._event_buffer.append({
                'event': event,
                'timestamp': datetime.now()
            })
    
    async def _process_events(self):
        """Process events from the buffer."""
        while self._running:
            try:
                # Get events to process
                events_to_process = []
                async with self._buffer_lock:
                    if self._event_buffer:
                        events_to_process = self._event_buffer.copy()
                        self._event_buffer.clear()
                
                # Process events
                for event_data in events_to_process:
                    try:
                        # Check event age
                        event_age = datetime.now() - event_data['timestamp']
                        if event_age.total_seconds() > self.event_config.max_event_age_seconds:
                            self.logger.warning("Dropping old event")
                            continue
                        
                        # Handle event
                        start_time = datetime.now()
                        news_item = await self.handle_event(event_data['event'])
                        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                        
                        if news_item:
                            self.emit_news_item(news_item)
                            self.metrics.record_fetch(processing_time_ms, 1)
                        
                    except Exception as e:
                        error_msg = f"Error processing event: {e}"
                        self.logger.error(error_msg)
                        self.metrics.record_fetch(0, 0, error_msg)
                
                # Sleep briefly before next processing cycle
                await asyncio.sleep(0.1)
                
            except Exception as e:
                error_msg = f"Error in event processing loop: {e}"
                self.logger.error(error_msg)
                self._emit_error_event(error_msg)
                await asyncio.sleep(1)  # Wait before retrying
    
    def is_healthy(self) -> bool:
        """Check if the event source is healthy."""
        if not self._running:
            return False
        
        # Check if processing task is running
        if self._processing_task and self._processing_task.done():
            return False
        
        # Check buffer size (shouldn't be consistently full)
        if len(self._event_buffer) >= self.event_config.event_buffer_size * 0.9:
            return False
        
        return True