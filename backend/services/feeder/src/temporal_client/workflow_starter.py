"""Temporal workflow starter for news processing."""

import asyncio
import logging
from datetime import timedelta
from typing import Optional, Dict, Any
from temporalio import client
from temporalio.client import WorkflowHandle
from temporalio.common import RetryPolicy

from ..models.news_item import NewsItem
from ..models.source_config import TemporalConfig
from ..models.events import (
    create_workflow_started_event,
    create_workflow_completed_event,
    create_workflow_failed_event,
    WorkflowEvent,
)


class WorkflowStarter:
    """Manages starting Temporal workflows for news processing."""
    
    def __init__(self, config: TemporalConfig):
        """Initialize the workflow starter with Temporal configuration."""
        self.config = config
        self.logger = logging.getLogger("workflow_starter")
        self._client: Optional[client.Client] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Temporal server."""
        if self._connected:
            return
        
        try:
            self._client = await client.Client.connect(
                f"{self.config.host}:{self.config.port}",
                namespace=self.config.namespace,
            )
            self._connected = True
            self.logger.info(f"Connected to Temporal at {self.config.host}:{self.config.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Temporal: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Temporal server."""
        if self._client:
            # Temporal client doesn't have explicit disconnect
            self._client = None
            self._connected = False
            self.logger.info("Disconnected from Temporal")
    
    async def start_news_processing_workflow(
        self, 
        news_item: NewsItem,
        workflow_type: str = "NewsProcessingWorkflow"
    ) -> WorkflowEvent:
        """Start a news processing workflow for a news item."""
        if not self._connected:
            await self.connect()
        
        if not self._client:
            raise RuntimeError("Not connected to Temporal")
        
        # Generate workflow ID based on news item hash
        workflow_id = f"news-{news_item.content_hash}"
        
        try:
            # Create workflow input
            workflow_input = {
                "news_item": news_item.to_dict(),
                "source_name": news_item.source_name,
                "source_type": news_item.source_type,
            }
            
            # Create retry policy
            retry_policy = RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(minutes=5),
                maximum_attempts=3,
                non_retryable_error_types=["ValueError", "TypeError"],
            )
            
            # Start the workflow
            handle: WorkflowHandle = await self._client.start_workflow(
                workflow_type,
                workflow_input,
                id=workflow_id,
                task_queue=self.config.task_queue,
                execution_timeout=timedelta(seconds=self.config.workflow_timeout_seconds),
                retry_policy=retry_policy,
            )
            
            self.logger.info(f"Started workflow {workflow_id} for news item: {news_item.title[:50]}...")
            
            # Create and return workflow started event
            return create_workflow_started_event(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                news_item_hash=news_item.content_hash,
            )
            
        except Exception as e:
            error_msg = f"Failed to start workflow for news item {news_item.content_hash}: {e}"
            self.logger.error(error_msg)
            
            # Create and return workflow failed event
            return create_workflow_failed_event(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                news_item_hash=news_item.content_hash,
                error_message=error_msg,
            )
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow."""
        if not self._connected:
            await self.connect()
        
        if not self._client:
            raise RuntimeError("Not connected to Temporal")
        
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            result = await handle.describe()
            
            return {
                "workflow_id": workflow_id,
                "status": result.status.name,
                "start_time": result.start_time,
                "execution_time": result.execution_time,
                "close_time": result.close_time,
                "task_queue": result.task_queue_name,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get workflow status for {workflow_id}: {e}")
            raise
    
    async def cancel_workflow(self, workflow_id: str, reason: str = "Cancelled by feeder") -> None:
        """Cancel a running workflow."""
        if not self._connected:
            await self.connect()
        
        if not self._client:
            raise RuntimeError("Not connected to Temporal")
        
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            await handle.cancel()
            
            self.logger.info(f"Cancelled workflow {workflow_id}: {reason}")
            
        except Exception as e:
            self.logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
            raise
    
    async def wait_for_workflow_completion(
        self, 
        workflow_id: str, 
        timeout_seconds: Optional[int] = None
    ) -> WorkflowEvent:
        """Wait for a workflow to complete and return the result event."""
        if not self._connected:
            await self.connect()
        
        if not self._client:
            raise RuntimeError("Not connected to Temporal")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            
            # Wait for completion with timeout
            if timeout_seconds:
                result = await asyncio.wait_for(
                    handle.result(),
                    timeout=timeout_seconds
                )
            else:
                result = await handle.result()
            
            end_time = asyncio.get_event_loop().time()
            execution_time_ms = (end_time - start_time) * 1000
            
            self.logger.info(f"Workflow {workflow_id} completed successfully")
            
            return create_workflow_completed_event(
                workflow_id=workflow_id,
                workflow_type="NewsProcessingWorkflow",  # Default type
                news_item_hash="",  # Would need to be passed in
                execution_time_ms=execution_time_ms,
            )
            
        except asyncio.TimeoutError:
            error_msg = f"Workflow {workflow_id} timed out after {timeout_seconds} seconds"
            self.logger.error(error_msg)
            
            return create_workflow_failed_event(
                workflow_id=workflow_id,
                workflow_type="NewsProcessingWorkflow",
                news_item_hash="",
                error_message=error_msg,
            )
            
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            execution_time_ms = (end_time - start_time) * 1000
            error_msg = f"Workflow {workflow_id} failed: {e}"
            
            self.logger.error(error_msg)
            
            return create_workflow_failed_event(
                workflow_id=workflow_id,
                workflow_type="NewsProcessingWorkflow",
                news_item_hash="",
                error_message=error_msg,
                execution_time_ms=execution_time_ms,
            )
    
    def is_connected(self) -> bool:
        """Check if connected to Temporal."""
        return self._connected and self._client is not None
    
    async def health_check(self) -> bool:
        """Perform a health check on the Temporal connection."""
        try:
            if not self._connected:
                await self.connect()
            
            if not self._client:
                return False
            
            # Try to list workflows as a health check
            async for _ in self._client.list_workflows():
                break  # Just check if we can start listing
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Temporal health check failed: {e}")
            return False


# Global workflow starter instance
_workflow_starter: Optional[WorkflowStarter] = None


async def get_temporal_client(config: TemporalConfig) -> WorkflowStarter:
    """Get or create the global workflow starter instance."""
    global _workflow_starter
    
    if _workflow_starter is None:
        _workflow_starter = WorkflowStarter(config)
        await _workflow_starter.connect()
    
    return _workflow_starter


async def cleanup_temporal_client() -> None:
    """Cleanup the global workflow starter instance."""
    global _workflow_starter
    
    if _workflow_starter:
        await _workflow_starter.disconnect()
        _workflow_starter = None