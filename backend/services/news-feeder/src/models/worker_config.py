"""Worker configuration models."""

import re
from typing import Dict, Any
from urllib.parse import urlparse


class WorkerConfig:
    """Base configuration for all worker types."""

    VALID_WORKER_TYPES = ["rss"]

    def __init__(
        self,
        name: str,
        type: str,
        worker_id: str,
        enabled: bool = True
    ):
        """Initialize a WorkerConfig.
        
        Args:
            name: Human-readable name for the worker
            type: Type of worker (rss, telegram, etc.)
            worker_id: Unique identifier for the worker instance
            enabled: Whether the worker is enabled
        """
        self.name = self._validate_name(name)
        self.type = self._validate_type(type)
        self.worker_id = self._validate_worker_id(worker_id)
        self.enabled = enabled

    def _validate_name(self, name: str) -> str:
        """Validate the name field."""
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        return name.strip()

    def _validate_type(self, worker_type: str) -> str:
        """Validate the worker type."""
        if worker_type not in self.VALID_WORKER_TYPES:
            raise ValueError(f"Invalid worker type: {worker_type}. Valid types: {self.VALID_WORKER_TYPES}")
        return worker_type

    def _validate_worker_id(self, worker_id: str) -> str:
        """Validate the worker ID."""
        if not worker_id or not worker_id.strip():
            raise ValueError("Worker ID cannot be empty")
        return worker_id.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the WorkerConfig to a dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "worker_id": self.worker_id,
            "enabled": self.enabled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkerConfig":
        """Create a WorkerConfig from a dictionary."""
        return cls(
            name=data["name"],
            type=data["type"],
            worker_id=data["worker_id"],
            enabled=data.get("enabled", True)
        )

    def __repr__(self) -> str:
        """String representation of the WorkerConfig."""
        return f"WorkerConfig(name='{self.name}', type='{self.type}', worker_id='{self.worker_id}')"


class RSSWorkerConfig(WorkerConfig):
    """Configuration specific to RSS workers."""

    def __init__(
        self,
        name: str,
        worker_id: str,
        url: str,
        polling_interval: str,
        timeout: str = "30s",
        max_retries: int = 3,
        enabled: bool = True
    ):
        """Initialize an RSSWorkerConfig.
        
        Args:
            name: Human-readable name for the worker
            worker_id: Unique identifier for the worker instance
            url: RSS feed URL
            polling_interval: How often to poll the feed (e.g., "5m", "1h")
            timeout: Request timeout (e.g., "30s", "1m")
            max_retries: Maximum number of retries for failed requests
            enabled: Whether the worker is enabled
        """
        super().__init__(name=name, type="rss", worker_id=worker_id, enabled=enabled)
        self.url = self._validate_url(url)
        self.polling_interval = self._validate_time_duration(polling_interval, "polling interval")
        self.timeout = self._validate_time_duration(timeout, "timeout")
        self.max_retries = self._validate_max_retries(max_retries)

    def _validate_url(self, url: str) -> str:
        """Validate the RSS feed URL."""
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        url = url.strip()
        parsed = urlparse(url)
        
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        return url

    def _validate_time_duration(self, duration: str, field_name: str) -> str:
        """Validate time duration format (e.g., '5m', '1h', '30s')."""
        if not duration or not duration.strip():
            raise ValueError(f"Invalid {field_name} format: cannot be empty")
        
        duration = duration.strip()
        
        # Pattern for time duration: number followed by unit (s, m, h, d)
        pattern = r'^\d+[smhd]$'
        if not re.match(pattern, duration):
            raise ValueError(f"Invalid {field_name} format: {duration}. Expected format: number + unit (s/m/h/d)")
        
        return duration

    def _validate_max_retries(self, max_retries: int) -> int:
        """Validate max_retries value."""
        if max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        return max_retries

    def to_dict(self) -> Dict[str, Any]:
        """Convert the RSSWorkerConfig to a dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "url": self.url,
            "polling_interval": self.polling_interval,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RSSWorkerConfig":
        """Create an RSSWorkerConfig from a dictionary."""
        return cls(
            name=data["name"],
            worker_id=data["worker_id"],
            url=data["url"],
            polling_interval=data["polling_interval"],
            timeout=data.get("timeout", "30s"),
            max_retries=data.get("max_retries", 3),
            enabled=data.get("enabled", True)
        )

    def __repr__(self) -> str:
        """String representation of the RSSWorkerConfig."""
        return f"RSSWorkerConfig(name='{self.name}', worker_id='{self.worker_id}', url='{self.url}')"