#!/usr/bin/env python3
"""
Script to run a Temporal worker for RSS news ingestion.
"""

import asyncio
import logging
import sys
import os
from typing import List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from temporal_client import TemporalClient, TemporalConfig
from workflows.news_ingestion import NewsIngestionWorkflow
from activities.rss_activities import fetch_rss_news, process_news_items
from models.worker_config import RSSWorkerConfig


def setup_logging():
    """Configure logging for the worker."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers to DEBUG for more detailed output
    logging.getLogger('temporalio').setLevel(logging.INFO)
    logging.getLogger('activities').setLevel(logging.DEBUG)
    logging.getLogger('workflows').setLevel(logging.DEBUG)


async def create_rss_config() -> RSSWorkerConfig:
    """Create RSS worker configuration."""
    return RSSWorkerConfig(
        name="kommersant_news",
        worker_id="kommersant_001",
        url="https://www.kommersant.ru/rss/news.xml",
        polling_interval="30s",  # Poll every 30 seconds for demo
        timeout="30s",
        max_retries=3
    )


async def run_temporal_worker():
    """Run the Temporal worker."""
    print("🚀 Starting Temporal Worker for News Ingestion")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Create Temporal configuration
    temporal_config = TemporalConfig(
        server_url="localhost:7233",
        namespace="default",  # Using default namespace for simplicity
        task_queue="news-ingestion"
    )
    
    # Create Temporal client
    client = TemporalClient(temporal_config)
    
    try:
        print("🔌 Connecting to Temporal server...")
        await client.connect()
        print("✅ Connected to Temporal server")
        
        # Create worker with workflows and activities
        print("👷 Creating Temporal worker...")
        worker = client.create_worker(
            workflows=[NewsIngestionWorkflow],
            activities=[fetch_rss_news, process_news_items]
        )
        print("✅ Worker created successfully")
        
        print(f"📋 Task Queue: {temporal_config.task_queue}")
        print(f"🌐 Namespace: {temporal_config.namespace}")
        print(f"🔗 Server: {temporal_config.server_url}")
        print()
        
        print("🏃 Starting worker... (Press Ctrl+C to stop)")
        await client.start_worker()
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping worker...")
    except Exception as e:
        print(f"❌ Error running worker: {e}")
        raise
    finally:
        print("🧹 Cleaning up...")
        try:
            await client.stop_worker()
        except:
            pass
        try:
            await client.disconnect()
        except:
            pass
        print("✅ Worker stopped and disconnected")


async def start_workflow():
    """Start a news ingestion workflow."""
    print("\n" + "=" * 50)
    print("🎬 Starting News Ingestion Workflow")
    print("=" * 50)
    
    # Create Temporal configuration
    temporal_config = TemporalConfig(
        server_url="localhost:7233",
        namespace="default",
        task_queue="news-ingestion"
    )
    
    # Create Temporal client
    client = TemporalClient(temporal_config)
    
    try:
        print("🔌 Connecting to Temporal server...")
        await client.connect()
        
        # Create RSS configuration
        rss_config = await create_rss_config()
        print(f"📰 RSS Feed: {rss_config.url}")
        print(f"⏱️  Polling Interval: {rss_config.polling_interval}")
        
        # Start workflow
        temporal_client = client.get_client()
        workflow_handle = await temporal_client.start_workflow(
            NewsIngestionWorkflow.run,
            rss_config.to_dict(),  # Convert to dict for JSON serialization
            id=f"news-ingestion-{rss_config.worker_id}",
            task_queue=temporal_config.task_queue
        )
        
        print(f"🎬 Started workflow: {workflow_handle.id}")
        print("✅ Workflow is now running!")
        print("💡 The workflow will continue running until manually terminated.")
        
    except Exception as e:
        print(f"❌ Error starting workflow: {e}")
        raise
    finally:
        await client.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Temporal worker for news ingestion")
    parser.add_argument(
        "--mode", 
        choices=["worker", "workflow", "both"], 
        default="both",
        help="Mode to run: worker only, workflow only, or both (default: both)"
    )
    
    args = parser.parse_args()
    
    async def main():
        if args.mode in ["worker", "both"]:
            # Start worker in background if running both
            if args.mode == "both":
                worker_task = asyncio.create_task(run_temporal_worker())
                await asyncio.sleep(2)  # Give worker time to start
                
                # Start workflow
                await start_workflow()
                
                # Wait for worker
                await worker_task
            else:
                await run_temporal_worker()
        elif args.mode == "workflow":
            await start_workflow()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)