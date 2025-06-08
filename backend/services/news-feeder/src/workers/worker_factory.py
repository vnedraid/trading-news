"""Factory for creating worker instances."""

from typing import List, Type

from .base_worker import BaseWorker
from .rss_worker import RSSWorker
from models.worker_config import WorkerConfig, RSSWorkerConfig


class WorkerFactory:
    """Factory class for creating worker instances."""

    # Registry of worker types to their corresponding classes
    _WORKER_REGISTRY = {
        "rss": RSSWorker,
    }

    @classmethod
    def create_worker(cls, config: WorkerConfig) -> BaseWorker:
        """Create a worker instance based on configuration.
        
        Args:
            config: Worker configuration
            
        Returns:
            Worker instance
            
        Raises:
            ValueError: If worker type is not supported
        """
        worker_type = config.type
        
        if worker_type not in cls._WORKER_REGISTRY:
            raise ValueError(
                f"Unsupported worker type: {worker_type}. "
                f"Supported types: {list(cls._WORKER_REGISTRY.keys())}"
            )
        
        worker_class = cls._WORKER_REGISTRY[worker_type]
        return worker_class(config)

    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported worker types.
        
        Returns:
            List of supported worker type strings
        """
        return list(cls._WORKER_REGISTRY.keys())

    @classmethod
    def register_worker_type(cls, worker_type: str, worker_class: Type[BaseWorker]) -> None:
        """Register a new worker type.
        
        Args:
            worker_type: String identifier for the worker type
            worker_class: Worker class that extends BaseWorker
        """
        cls._WORKER_REGISTRY[worker_type] = worker_class

    @classmethod
    def unregister_worker_type(cls, worker_type: str) -> None:
        """Unregister a worker type.
        
        Args:
            worker_type: String identifier for the worker type
        """
        if worker_type in cls._WORKER_REGISTRY:
            del cls._WORKER_REGISTRY[worker_type]