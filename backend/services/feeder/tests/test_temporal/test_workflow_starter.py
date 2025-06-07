"""Tests for the Temporal workflow starter."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.temporal_client.workflow_starter import WorkflowStarter, get_temporal_client
from src.models.source_config import TemporalConfig
from src.models.news_item import NewsItem
from src.models.events import EventType


@pytest.fixture
def temporal_config():
    """Create a test Temporal configuration."""
    return TemporalConfig(
        host="10.10.157.2",
        port=7233,
        namespace="test",
        task_queue="test-news-processing",
        workflow_timeout_seconds=300,
        activity_timeout_seconds=60,
    )


@pytest.fixture
def sample_news_item():
    """Create a sample news item for testing."""
    return NewsItem(
        title="Test News Article",
        description="This is a test news article",
        link="https://example.com/news/test",
        publication_date=datetime(2024, 1, 1, 12, 0, 0),
        source_name="Test Source",
        source_type="rss",
    )


class TestWorkflowStarter:
    """Test cases for WorkflowStarter."""
    
    def test_workflow_starter_initialization(self, temporal_config):
        """Test WorkflowStarter initialization."""
        starter = WorkflowStarter(temporal_config)
        
        assert starter.config == temporal_config
        assert starter._client is None
        assert starter._connected is False
        assert not starter.is_connected()
    
    @pytest.mark.asyncio
    async def test_connect_success(self, temporal_config):
        """Test successful connection to Temporal."""
        starter = WorkflowStarter(temporal_config)
        
        # Mock the Temporal client
        mock_client = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client) as mock_connect:
            await starter.connect()
            
            # Verify connection was attempted with correct parameters
            mock_connect.assert_called_once_with(
                "10.10.157.2:7233",
                namespace="test"
            )
            
            assert starter._client == mock_client
            assert starter._connected is True
            assert starter.is_connected()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, temporal_config):
        """Test connection failure to Temporal."""
        starter = WorkflowStarter(temporal_config)
        
        with patch('temporalio.client.Client.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await starter.connect()
            
            assert starter._client is None
            assert starter._connected is False
            assert not starter.is_connected()
    
    @pytest.mark.asyncio
    async def test_connect_idempotent(self, temporal_config):
        """Test that multiple connect calls are idempotent."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client) as mock_connect:
            # Connect twice
            await starter.connect()
            await starter.connect()
            
            # Should only connect once
            mock_connect.assert_called_once()
            assert starter.is_connected()
    
    @pytest.mark.asyncio
    async def test_disconnect(self, temporal_config):
        """Test disconnection from Temporal."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            await starter.connect()
            assert starter.is_connected()
            
            await starter.disconnect()
            
            assert starter._client is None
            assert starter._connected is False
            assert not starter.is_connected()
    
    @pytest.mark.asyncio
    async def test_start_news_processing_workflow_success(self, temporal_config, sample_news_item):
        """Test successful workflow start."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        mock_handle = MagicMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            mock_client.start_workflow.return_value = mock_handle
            
            event = await starter.start_news_processing_workflow(sample_news_item)
            
            # Verify workflow was started with correct parameters
            mock_client.start_workflow.assert_called_once()
            call_args = mock_client.start_workflow.call_args
            
            assert call_args[0][0] == "NewsProcessingWorkflow"  # workflow_type
            assert call_args[1]["id"] == f"news-{sample_news_item.content_hash}"
            assert call_args[1]["task_queue"] == "test-news-processing"
            
            # Verify event
            assert event.event_type == EventType.WORKFLOW_STARTED
            assert event.workflow_id == f"news-{sample_news_item.content_hash}"
            assert event.workflow_type == "NewsProcessingWorkflow"
            assert event.news_item_hash == sample_news_item.content_hash
    
    @pytest.mark.asyncio
    async def test_start_news_processing_workflow_failure(self, temporal_config, sample_news_item):
        """Test workflow start failure."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            mock_client.start_workflow.side_effect = Exception("Workflow start failed")
            
            event = await starter.start_news_processing_workflow(sample_news_item)
            
            # Verify failure event
            assert event.event_type == EventType.WORKFLOW_FAILED
            assert event.workflow_id == f"news-{sample_news_item.content_hash}"
            assert "Workflow start failed" in event.error_message
    
    @pytest.mark.asyncio
    async def test_start_workflow_auto_connect(self, temporal_config, sample_news_item):
        """Test that workflow start auto-connects if not connected."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        mock_handle = MagicMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client) as mock_connect:
            mock_client.start_workflow.return_value = mock_handle
            
            # Start workflow without explicit connect
            event = await starter.start_news_processing_workflow(sample_news_item)
            
            # Should have auto-connected
            mock_connect.assert_called_once()
            assert starter.is_connected()
            assert event.event_type == EventType.WORKFLOW_STARTED
    
    @pytest.mark.asyncio
    async def test_get_workflow_status_success(self, temporal_config):
        """Test successful workflow status retrieval."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        mock_handle = MagicMock()
        mock_result = MagicMock()
        
        # Setup mock result
        mock_result.status.name = "COMPLETED"
        mock_result.start_time = datetime.now()
        mock_result.execution_time = timedelta(seconds=30)
        mock_result.close_time = datetime.now()
        mock_result.task_queue_name = "test-queue"
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            # Configure get_workflow_handle to return the mock handle directly
            mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
            # Configure describe to return the mock result directly (not as a coroutine)
            mock_handle.describe = AsyncMock(return_value=mock_result)
            
            status = await starter.get_workflow_status("test-workflow-id")
            
            assert status["workflow_id"] == "test-workflow-id"
            assert status["status"] == "COMPLETED"
            assert status["task_queue"] == "test-queue"
            
            mock_client.get_workflow_handle.assert_called_once_with("test-workflow-id")
            mock_handle.describe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_workflow_status_failure(self, temporal_config):
        """Test workflow status retrieval failure."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            mock_client.get_workflow_handle = MagicMock(side_effect=Exception("Workflow not found"))
            
            with pytest.raises(Exception, match="Workflow not found"):
                await starter.get_workflow_status("non-existent-workflow")
    
    @pytest.mark.asyncio
    async def test_cancel_workflow_success(self, temporal_config):
        """Test successful workflow cancellation."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        mock_handle = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
            # Configure cancel to be an AsyncMock
            mock_handle.cancel = AsyncMock()
            
            await starter.cancel_workflow("test-workflow-id", "Test cancellation")
            
            mock_client.get_workflow_handle.assert_called_once_with("test-workflow-id")
            mock_handle.cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_workflow_failure(self, temporal_config):
        """Test workflow cancellation failure."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            mock_client.get_workflow_handle = MagicMock(side_effect=Exception("Cancellation failed"))
            
            with pytest.raises(Exception, match="Cancellation failed"):
                await starter.cancel_workflow("test-workflow-id")
    
    @pytest.mark.asyncio
    async def test_wait_for_workflow_completion_success(self, temporal_config):
        """Test successful workflow completion waiting."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        mock_handle = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
            # Configure result to be an AsyncMock
            mock_handle.result = AsyncMock(return_value={"status": "completed"})
            
            event = await starter.wait_for_workflow_completion("test-workflow-id")
            
            assert event.event_type == EventType.WORKFLOW_COMPLETED
            assert event.workflow_id == "test-workflow-id"
            assert event.execution_time_ms is not None
            
            mock_handle.result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_wait_for_workflow_completion_timeout(self, temporal_config):
        """Test workflow completion waiting with timeout."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        mock_handle = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
            # Configure result to be an AsyncMock that raises TimeoutError
            mock_handle.result = AsyncMock(side_effect=asyncio.TimeoutError())
            
            with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                event = await starter.wait_for_workflow_completion("test-workflow-id", timeout_seconds=1)
            
            assert event.event_type == EventType.WORKFLOW_FAILED
            assert "timed out" in event.error_message
    
    @pytest.mark.asyncio
    async def test_wait_for_workflow_completion_failure(self, temporal_config):
        """Test workflow completion waiting with failure."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        mock_handle = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            mock_client.get_workflow_handle = MagicMock(return_value=mock_handle)
            # Configure result to be an AsyncMock that raises Exception
            mock_handle.result = AsyncMock(side_effect=Exception("Workflow failed"))
            
            event = await starter.wait_for_workflow_completion("test-workflow-id")
            
            assert event.event_type == EventType.WORKFLOW_FAILED
            assert "Workflow failed" in event.error_message
            assert event.execution_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, temporal_config):
        """Test successful health check."""
        starter = WorkflowStarter(temporal_config)
        mock_client = AsyncMock()
        
        # Create a proper async iterator mock
        class MockAsyncIterator:
            def __init__(self):
                self.items = [{"id": "test-workflow"}]
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self.index >= len(self.items):
                    raise StopAsyncIteration
                item = self.items[self.index]
                self.index += 1
                return item
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            # Configure list_workflows to return the async iterator
            mock_client.list_workflows = MagicMock(return_value=MockAsyncIterator())
            
            is_healthy = await starter.health_check()
            
            assert is_healthy is True
            mock_client.list_workflows.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, temporal_config):
        """Test health check failure."""
        starter = WorkflowStarter(temporal_config)
        
        with patch('temporalio.client.Client.connect', side_effect=Exception("Connection failed")):
            is_healthy = await starter.health_check()
            
            assert is_healthy is False


class TestGlobalTemporalClient:
    """Test cases for global Temporal client functions."""
    
    @pytest.mark.asyncio
    async def test_get_temporal_client_creates_instance(self, temporal_config):
        """Test that get_temporal_client creates and connects instance."""
        mock_client = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            # Clear any existing global instance
            from src.temporal_client.workflow_starter import cleanup_temporal_client
            await cleanup_temporal_client()
            
            starter = await get_temporal_client(temporal_config)
            
            assert isinstance(starter, WorkflowStarter)
            assert starter.is_connected()
    
    @pytest.mark.asyncio
    async def test_get_temporal_client_reuses_instance(self, temporal_config):
        """Test that get_temporal_client reuses existing instance."""
        mock_client = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client) as mock_connect:
            # Clear any existing global instance
            from src.temporal_client.workflow_starter import cleanup_temporal_client
            await cleanup_temporal_client()
            
            # Get client twice
            starter1 = await get_temporal_client(temporal_config)
            starter2 = await get_temporal_client(temporal_config)
            
            # Should be the same instance
            assert starter1 is starter2
            # Should only connect once
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_temporal_client(self, temporal_config):
        """Test cleanup of global Temporal client."""
        mock_client = AsyncMock()
        
        with patch('temporalio.client.Client.connect', return_value=mock_client):
            # Create instance
            starter = await get_temporal_client(temporal_config)
            assert starter.is_connected()
            
            # Cleanup
            from src.temporal_client.workflow_starter import cleanup_temporal_client
            await cleanup_temporal_client()
            
            # Should be disconnected
            assert not starter.is_connected()