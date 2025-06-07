"""Event models for the News Feeder Service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from .news_item import NewsItem


class EventType(Enum):
    """Types of events in the system."""
    NEWS_ITEM_RECEIVED = "news_item_received"
    NEWS_ITEM_PROCESSED = "news_item_processed"
    NEWS_ITEM_DUPLICATE = "news_item_duplicate"
    NEWS_ITEM_ERROR = "news_item_error"
    SOURCE_STARTED = "source_started"
    SOURCE_STOPPED = "source_stopped"
    SOURCE_ERROR = "source_error"
    SOURCE_HEALTH_CHECK = "source_health_check"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"


@dataclass
class BaseEvent:
    """Base event class."""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate event ID if not provided."""
        if not self.event_id:
            import uuid
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "metadata": self.metadata,
        }


@dataclass
class NewsEvent:
    """Event related to news item processing."""
    event_type: EventType
    news_item: NewsItem
    source_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Generate event ID if not provided."""
        if not self.event_id:
            import uuid
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "metadata": self.metadata,
            "news_item": self.news_item.to_dict(),
            "source_name": self.source_name,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
        }


@dataclass
class SourceEvent:
    """Event related to source operations."""
    event_type: EventType
    source_name: str
    source_type: str
    source_url: str
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_healthy: bool = True
    error_message: Optional[str] = None
    items_processed: int = 0
    
    def __post_init__(self):
        """Generate event ID if not provided."""
        if not self.event_id:
            import uuid
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "metadata": self.metadata,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "is_healthy": self.is_healthy,
            "error_message": self.error_message,
            "items_processed": self.items_processed,
        }


@dataclass
class WorkflowEvent:
    """Event related to Temporal workflow operations."""
    event_type: EventType
    workflow_id: str
    workflow_type: str
    news_item_hash: str
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Generate event ID if not provided."""
        if not self.event_id:
            import uuid
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "metadata": self.metadata,
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "news_item_hash": self.news_item_hash,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
        }


@dataclass
class SystemEvent:
    """Event related to system operations."""
    event_type: EventType
    component: str
    operation: str
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate event ID if not provided."""
        if not self.event_id:
            import uuid
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "metadata": self.metadata,
            "component": self.component,
            "operation": self.operation,
            "success": self.success,
            "error_message": self.error_message,
            "performance_metrics": self.performance_metrics,
        }


# Event factory functions for common events
def create_news_received_event(
    news_item: NewsItem, 
    source_name: str,
    processing_time_ms: Optional[float] = None
) -> NewsEvent:
    """Create a news item received event."""
    return NewsEvent(
        event_type=EventType.NEWS_ITEM_RECEIVED,
        news_item=news_item,
        source_name=source_name,
        processing_time_ms=processing_time_ms,
    )


def create_news_processed_event(
    news_item: NewsItem, 
    source_name: str,
    processing_time_ms: Optional[float] = None
) -> NewsEvent:
    """Create a news item processed event."""
    return NewsEvent(
        event_type=EventType.NEWS_ITEM_PROCESSED,
        news_item=news_item,
        source_name=source_name,
        processing_time_ms=processing_time_ms,
    )


def create_news_duplicate_event(
    news_item: NewsItem, 
    source_name: str
) -> NewsEvent:
    """Create a news item duplicate event."""
    return NewsEvent(
        event_type=EventType.NEWS_ITEM_DUPLICATE,
        news_item=news_item,
        source_name=source_name,
    )


def create_news_error_event(
    news_item: NewsItem, 
    source_name: str,
    error_message: str
) -> NewsEvent:
    """Create a news item error event."""
    return NewsEvent(
        event_type=EventType.NEWS_ITEM_ERROR,
        news_item=news_item,
        source_name=source_name,
        error_message=error_message,
    )


def create_source_started_event(
    source_name: str,
    source_type: str,
    source_url: str
) -> SourceEvent:
    """Create a source started event."""
    return SourceEvent(
        event_type=EventType.SOURCE_STARTED,
        source_name=source_name,
        source_type=source_type,
        source_url=source_url,
        is_healthy=True,
    )


def create_source_stopped_event(
    source_name: str,
    source_type: str,
    source_url: str
) -> SourceEvent:
    """Create a source stopped event."""
    return SourceEvent(
        event_type=EventType.SOURCE_STOPPED,
        source_name=source_name,
        source_type=source_type,
        source_url=source_url,
        is_healthy=False,
    )


def create_source_error_event(
    source_name: str,
    source_type: str,
    source_url: str,
    error_message: str
) -> SourceEvent:
    """Create a source error event."""
    return SourceEvent(
        event_type=EventType.SOURCE_ERROR,
        source_name=source_name,
        source_type=source_type,
        source_url=source_url,
        is_healthy=False,
        error_message=error_message,
    )


def create_workflow_started_event(
    workflow_id: str,
    workflow_type: str,
    news_item_hash: str
) -> WorkflowEvent:
    """Create a workflow started event."""
    return WorkflowEvent(
        event_type=EventType.WORKFLOW_STARTED,
        workflow_id=workflow_id,
        workflow_type=workflow_type,
        news_item_hash=news_item_hash,
    )


def create_workflow_completed_event(
    workflow_id: str,
    workflow_type: str,
    news_item_hash: str,
    execution_time_ms: Optional[float] = None
) -> WorkflowEvent:
    """Create a workflow completed event."""
    return WorkflowEvent(
        event_type=EventType.WORKFLOW_COMPLETED,
        workflow_id=workflow_id,
        workflow_type=workflow_type,
        news_item_hash=news_item_hash,
        execution_time_ms=execution_time_ms,
    )


def create_workflow_failed_event(
    workflow_id: str,
    workflow_type: str,
    news_item_hash: str,
    error_message: str,
    execution_time_ms: Optional[float] = None
) -> WorkflowEvent:
    """Create a workflow failed event."""
    return WorkflowEvent(
        event_type=EventType.WORKFLOW_FAILED,
        workflow_id=workflow_id,
        workflow_type=workflow_type,
        news_item_hash=news_item_hash,
        error_message=error_message,
        execution_time_ms=execution_time_ms,
    )