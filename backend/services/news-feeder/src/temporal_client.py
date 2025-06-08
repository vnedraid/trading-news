"""Temporal client setup and configuration."""

from typing import Optional, List, Any
from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker


class TemporalConfig:
    """Configuration for Temporal client connection."""

    def __init__(
        self,
        server_url: str = "localhost:7233",
        namespace: str = "news-feeder",
        task_queue: str = "news-ingestion",
        tls_enabled: bool = False,
        tls_cert_path: Optional[str] = None,
        tls_key_path: Optional[str] = None
    ):
        """Initialize Temporal configuration.
        
        Args:
            server_url: Temporal server URL
            namespace: Temporal namespace
            task_queue: Default task queue name
            tls_enabled: Whether to use TLS
            tls_cert_path: Path to TLS certificate file
            tls_key_path: Path to TLS private key file
        """
        self.server_url = self._validate_server_url(server_url)
        self.namespace = self._validate_namespace(namespace)
        self.task_queue = self._validate_task_queue(task_queue)
        self.tls_enabled = tls_enabled
        self.tls_cert_path = tls_cert_path
        self.tls_key_path = tls_key_path
        
        self._validate_tls_config()

    def _validate_server_url(self, server_url: str) -> str:
        """Validate server URL."""
        if not server_url or not server_url.strip():
            raise ValueError("Server URL cannot be empty")
        return server_url.strip()

    def _validate_namespace(self, namespace: str) -> str:
        """Validate namespace."""
        if not namespace or not namespace.strip():
            raise ValueError("Namespace cannot be empty")
        return namespace.strip()

    def _validate_task_queue(self, task_queue: str) -> str:
        """Validate task queue."""
        if not task_queue or not task_queue.strip():
            raise ValueError("Task queue cannot be empty")
        return task_queue.strip()

    def _validate_tls_config(self) -> None:
        """Validate TLS configuration."""
        if self.tls_enabled:
            if bool(self.tls_cert_path) != bool(self.tls_key_path):
                raise ValueError("Both TLS cert and key paths must be provided when TLS is enabled")


class TemporalClient:
    """Temporal client wrapper for managing connections and workers."""

    def __init__(self, config: TemporalConfig):
        """Initialize Temporal client.
        
        Args:
            config: Temporal configuration
        """
        self.config = config
        self._client: Optional[Client] = None
        self._worker: Optional[Worker] = None

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to Temporal server."""
        return self._client is not None

    async def connect(self) -> None:
        """Connect to Temporal server."""
        try:
            if self.config.tls_enabled:
                tls_config = TLSConfig(
                    client_cert_path=self.config.tls_cert_path,
                    client_private_key_path=self.config.tls_key_path
                )
                self._client = await Client.connect(
                    self.config.server_url,
                    tls=tls_config
                )
            else:
                self._client = await Client.connect(self.config.server_url)
        except Exception as e:
            self._client = None
            raise e

    async def disconnect(self) -> None:
        """Disconnect from Temporal server."""
        if self._client:
            # Temporal client doesn't have a close method, just set to None
            self._client = None

    def create_worker(
        self,
        workflows: List[Any],
        activities: List[Any],
        task_queue: Optional[str] = None
    ) -> Worker:
        """Create a Temporal worker.
        
        Args:
            workflows: List of workflow classes
            activities: List of activity functions
            task_queue: Task queue name (uses default if not provided)
            
        Returns:
            Configured Temporal worker
            
        Raises:
            RuntimeError: If client is not connected
        """
        if not self.is_connected:
            raise RuntimeError("Client is not connected. Call connect() first.")
        
        queue_name = task_queue or self.config.task_queue
        
        self._worker = Worker(
            self._client,
            task_queue=queue_name,
            workflows=workflows,
            activities=activities
        )
        
        return self._worker

    async def start_worker(self) -> None:
        """Start the Temporal worker.
        
        Raises:
            RuntimeError: If worker is not created
        """
        if not self._worker:
            raise RuntimeError("Worker is not created. Call create_worker() first.")
        
        await self._worker.run()

    async def stop_worker(self) -> None:
        """Stop the Temporal worker."""
        if self._worker:
            await self._worker.shutdown()

    def get_client(self) -> Client:
        """Get the Temporal client instance.
        
        Returns:
            Temporal client instance
            
        Raises:
            RuntimeError: If client is not connected
        """
        if not self.is_connected:
            raise RuntimeError("Client is not connected. Call connect() first.")
        
        return self._client