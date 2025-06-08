"""News ingestion workflow for RSS feeds."""

import asyncio
from datetime import timedelta
from typing import List

from temporalio import workflow
from temporalio.common import RetryPolicy

from models.news_item import NewsItem
from models.worker_config import RSSWorkerConfig


@workflow.defn
class NewsIngestionWorkflow:
    """Workflow for ingesting news from RSS feeds."""

    @workflow.run
    async def run(self, config_dict: dict) -> None:
        """Run the news ingestion workflow.
        
        Args:
            config_dict: RSS worker configuration as dictionary
        """
        # Convert dict back to RSSWorkerConfig
        config = RSSWorkerConfig.from_dict(config_dict)
        workflow.logger.info(f"Starting news ingestion workflow for {config.name}")
        
        # Parse polling interval
        interval_seconds = self._parse_interval(config.polling_interval)
        
        while True:
            try:
                # Fetch news from RSS feed
                news_items = await workflow.execute_activity(
                    "fetch_rss_news",
                    config_dict,  # Pass the original dict to activity
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(seconds=30),
                        maximum_attempts=config.max_retries,
                        backoff_coefficient=2.0,
                    ),
                )
                
                workflow.logger.info(f"Fetched {len(news_items)} news items from {config.name}")
                
                # Process news items if any were found
                if news_items:
                    await workflow.execute_activity(
                        "process_news_items",
                        news_items,
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(
                            initial_interval=timedelta(seconds=1),
                            maximum_interval=timedelta(seconds=10),
                            maximum_attempts=3,
                            backoff_coefficient=2.0,
                        ),
                    )
                
                # Wait for next polling cycle
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                workflow.logger.error(f"Error in news ingestion workflow: {e}")
                # Wait before retrying
                await asyncio.sleep(30)

    def _parse_interval(self, interval: str) -> int:
        """Parse polling interval string to seconds.
        
        Args:
            interval: Interval string (e.g., "5m", "1h", "30s")
            
        Returns:
            Interval in seconds
        """
        if interval.endswith('s'):
            return int(interval[:-1])
        elif interval.endswith('m'):
            return int(interval[:-1]) * 60
        elif interval.endswith('h'):
            return int(interval[:-1]) * 3600
        elif interval.endswith('d'):
            return int(interval[:-1]) * 86400
        else:
            raise ValueError(f"Invalid interval format: {interval}")


# Activity imports - these will be resolved at runtime by Temporal
# from activities.rss_activities import fetch_rss_news, process_news_items