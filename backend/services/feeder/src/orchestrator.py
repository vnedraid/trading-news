"""Main orchestrator service for the News Feeder."""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta

from src.config.settings import load_config
from src.models.source_config import FeederConfig
from src.models.news_item import NewsItem
from src.models.events import EventType, WorkflowEvent
from src.sources.factory import get_source_factory
from src.sources.base import BaseSource, PollingSource, EventSource
from src.temporal_client.workflow_starter import get_temporal_client, WorkflowStarter
from src.redis_client import get_duplicate_detector, DuplicateDetector


logger = logging.getLogger(__name__)


class NewsOrchestrator:
    """Main orchestrator for news processing workflows."""
    
    def __init__(self, config: FeederConfig):
        """Initialize the orchestrator with configuration."""
        self.config = config
        self.temporal_client: Optional[WorkflowStarter] = None
        self.duplicate_detector: Optional[DuplicateDetector] = None
        self.source_factory = get_source_factory()
        self.sources: Dict[str, BaseSource] = {}
        self.running_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self) -> None:
        """Initialize the orchestrator and all components."""
        logger.info("Initializing News Orchestrator...")
        
        # Initialize Temporal client
        self.temporal_client = await get_temporal_client(self.config.temporal)
        logger.info("Temporal client initialized")
        
        # Initialize Redis duplicate detector
        self.duplicate_detector = await get_duplicate_detector(self.config.redis)
        logger.info("Redis duplicate detector initialized")
        
        # Initialize sources
        await self._initialize_sources()
        logger.info(f"Initialized {len(self.sources)} sources")
        
    async def _initialize_sources(self) -> None:
        """Initialize all configured sources."""
        for source_config in self.config.get_enabled_sources():
            try:
                source = self.source_factory.create_source(source_config)
                self.sources[source_config.name] = source
                
                # Set up callbacks for news items
                source.add_news_callback(self._handle_news_item)
                    
                logger.info(f"Initialized source: {source_config.name} ({source_config.type})")
                
            except Exception as e:
                logger.error(f"Failed to initialize source {source_config.name}: {e}")
                
    async def start(self) -> None:
        """Start the orchestrator and all sources."""
        if not self.temporal_client:
            await self.initialize()
            
        logger.info("Starting News Orchestrator...")
        
        # Start all sources
        for name, source in self.sources.items():
            try:
                await source.start()
                logger.info(f"Started source: {name}")
            except Exception as e:
                logger.error(f"Failed to start source {name}: {e}")
            
        # Start health monitoring
        health_task = asyncio.create_task(
            self._health_monitor(),
            name="health-monitor"
        )
        self.running_tasks.add(health_task)
        
        logger.info(f"Started {len(self.sources)} sources and {len(self.running_tasks)} tasks")
        
    async def stop(self) -> None:
        """Stop the orchestrator and all sources."""
        logger.info("Stopping News Orchestrator...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Stop all sources
        for name, source in self.sources.items():
            try:
                await source.stop()
                logger.info(f"Stopped source: {name}")
            except Exception as e:
                logger.error(f"Failed to stop source {name}: {e}")
        
        # Cancel all running tasks
        for task in self.running_tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks, return_exceptions=True)
            
        # Cleanup Temporal client
        if self.temporal_client:
            await self.temporal_client.disconnect()
            
        # Cleanup Redis client
        if self.duplicate_detector:
            await self.duplicate_detector.cleanup()
            
        logger.info("News Orchestrator stopped")
        
    def _handle_news_item(self, news_item: NewsItem) -> None:
        """Handle a news item from a source (callback)."""
        # Create a task to process the news item asynchronously
        task = asyncio.create_task(self._process_news_item(news_item, news_item.source_name))
        self.running_tasks.add(task)
        
        # Clean up completed tasks
        self.running_tasks = {task for task in self.running_tasks if not task.done()}
            
    async def _process_news_item(self, item: NewsItem, source_name: str) -> None:
        """Process a single news item."""
        try:
            # Check for duplicates using Redis
            if self.duplicate_detector:
                is_duplicate = await self.duplicate_detector.is_duplicate(item.content_hash)
                if is_duplicate:
                    logger.debug(f"Skipping duplicate item: {item.content_hash}")
                    return
                    
                # Mark as processed
                await self.duplicate_detector.mark_processed(item.content_hash)
            
            # Start Temporal workflow
            if self.temporal_client:
                event = await self.temporal_client.start_news_processing_workflow(item)
                
                if event.event_type == EventType.WORKFLOW_STARTED:
                    logger.info(f"Started workflow for news item from {source_name}: {item.title[:50]}...")
                else:
                    logger.error(f"Failed to start workflow: {event.error_message}")
            else:
                logger.warning("No Temporal client available, skipping workflow start")
                
        except Exception as e:
            logger.error(f"Error processing news item from {source_name}: {e}")
            
    async def _health_monitor(self) -> None:
        """Monitor the health of the orchestrator and its components."""
        logger.info("Starting health monitor")
        
        while not self._shutdown_event.is_set():
            try:
                # Check Temporal health
                if self.temporal_client:
                    temporal_healthy = await self.temporal_client.health_check()
                    if not temporal_healthy:
                        logger.warning("Temporal client health check failed")
                        
                # Check Redis health
                if self.duplicate_detector:
                    redis_healthy = self.duplicate_detector.is_healthy()
                    if not redis_healthy:
                        logger.warning("Redis duplicate detector health check failed")
                        
                # Check source health
                unhealthy_sources = []
                for name, source in self.sources.items():
                    if not source.is_healthy():
                        unhealthy_sources.append(name)
                        
                if unhealthy_sources:
                    logger.warning(f"Unhealthy sources: {unhealthy_sources}")
                    
                # Wait before next health check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                logger.info("Health monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(30)
                
    async def get_status(self) -> Dict:
        """Get the current status of the orchestrator."""
        active_tasks = [task for task in self.running_tasks if not task.done()]
        
        # Get Redis stats
        redis_stats = {}
        if self.duplicate_detector:
            redis_stats = await self.duplicate_detector.get_stats()
        
        status = {
            "orchestrator": {
                "running": not self._shutdown_event.is_set(),
                "active_tasks": len(active_tasks),
                "total_tasks": len(self.running_tasks)
            },
            "sources": {
                "count": len(self.sources),
                "names": list(self.sources.keys()),
                "healthy": [name for name, source in self.sources.items() if source.is_healthy()],
                "unhealthy": [name for name, source in self.sources.items() if not source.is_healthy()]
            },
            "temporal": {
                "connected": self.temporal_client.is_connected() if self.temporal_client else False,
                "healthy": await self.temporal_client.health_check() if self.temporal_client else False
            },
            "redis": redis_stats
        }
        
        return status


async def create_orchestrator(config_path: Optional[str] = None) -> NewsOrchestrator:
    """Create and initialize a news orchestrator."""
    config = load_config(config_path)
    orchestrator = NewsOrchestrator(config)
    await orchestrator.initialize()
    return orchestrator


async def main():
    """Main entry point for running the orchestrator."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        orchestrator = await create_orchestrator(config_path)
        await orchestrator.start()
        
        # Keep running until interrupted
        try:
            await asyncio.Event().wait()  # Wait forever
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            
    except Exception as e:
        logger.error(f"Failed to start orchestrator: {e}")
        sys.exit(1)
    finally:
        if 'orchestrator' in locals():
            await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())