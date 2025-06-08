"""Temporal client integration for the News Feeder Service."""

from .workflow_starter import WorkflowStarter, get_temporal_client

__all__ = [
    "WorkflowStarter",
    "get_temporal_client",
]