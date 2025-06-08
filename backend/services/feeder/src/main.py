"""Main application entry point for the News Feeder Service."""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from src.orchestrator import create_orchestrator, NewsOrchestrator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('news_feeder.log')
    ]
)

logger = logging.getLogger(__name__)


class NewsFeederApp:
    """Main News Feeder application."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the application."""
        self.config_path = config_path
        self.orchestrator: Optional[NewsOrchestrator] = None
        self._shutdown_event = asyncio.Event()
        
    async def start(self) -> None:
        """Start the News Feeder application."""
        logger.info("Starting News Feeder Service...")
        
        try:
            # Create and initialize orchestrator
            self.orchestrator = await create_orchestrator(self.config_path)
            
            # Start the orchestrator
            await self.orchestrator.start()
            
            logger.info("News Feeder Service started successfully")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Failed to start News Feeder Service: {e}")
            raise
        finally:
            await self.stop()
            
    async def stop(self) -> None:
        """Stop the News Feeder application."""
        logger.info("Stopping News Feeder Service...")
        
        if self.orchestrator:
            await self.orchestrator.stop()
            
        logger.info("News Feeder Service stopped")
        
    def shutdown(self) -> None:
        """Signal shutdown."""
        logger.info("Received shutdown signal")
        self._shutdown_event.set()
        
    async def get_status(self) -> dict:
        """Get application status."""
        if self.orchestrator:
            return await self.orchestrator.get_status()
        else:
            return {"status": "not_running"}


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="News Feeder Service")
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create application
    app = NewsFeederApp(args.config)
    
    # Setup signal handlers
    def signal_handler():
        app.shutdown()
        
    # Handle SIGINT and SIGTERM
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)