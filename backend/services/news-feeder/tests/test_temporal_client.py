"""Tests for Temporal client setup."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from temporal_client import TemporalClient, TemporalConfig


class TestTemporalConfig:
    """Test cases for TemporalConfig."""

    def test_temporal_config_creation_with_defaults(self):
        """Test creating TemporalConfig with default values."""
        config = TemporalConfig()
        
        assert config.server_url == "localhost:7233"
        assert config.namespace == "news-feeder"
        assert config.task_queue == "news-ingestion"
        assert config.tls_enabled is False
        assert config.tls_cert_path is None
        assert config.tls_key_path is None

    def test_temporal_config_creation_with_custom_values(self):
        """Test creating TemporalConfig with custom values."""
        config = TemporalConfig(
            server_url="temporal.example.com:7233",
            namespace="custom-namespace",
            task_queue="custom-queue",
            tls_enabled=True,
            tls_cert_path="/path/to/cert.pem",
            tls_key_path="/path/to/key.pem"
        )
        
        assert config.server_url == "temporal.example.com:7233"
        assert config.namespace == "custom-namespace"
        assert config.task_queue == "custom-queue"
        assert config.tls_enabled is True
        assert config.tls_cert_path == "/path/to/cert.pem"
        assert config.tls_key_path == "/path/to/key.pem"

    def test_temporal_config_validation_empty_server_url(self):
        """Test that empty server URL raises validation error."""
        with pytest.raises(ValueError, match="Server URL cannot be empty"):
            TemporalConfig(server_url="")

    def test_temporal_config_validation_empty_namespace(self):
        """Test that empty namespace raises validation error."""
        with pytest.raises(ValueError, match="Namespace cannot be empty"):
            TemporalConfig(namespace="")

    def test_temporal_config_validation_empty_task_queue(self):
        """Test that empty task queue raises validation error."""
        with pytest.raises(ValueError, match="Task queue cannot be empty"):
            TemporalConfig(task_queue="")

    def test_temporal_config_validation_tls_cert_without_key(self):
        """Test that TLS cert without key raises validation error."""
        with pytest.raises(ValueError, match="Both TLS cert and key paths must be provided"):
            TemporalConfig(
                tls_enabled=True,
                tls_cert_path="/path/to/cert.pem"
            )

    def test_temporal_config_validation_tls_key_without_cert(self):
        """Test that TLS key without cert raises validation error."""
        with pytest.raises(ValueError, match="Both TLS cert and key paths must be provided"):
            TemporalConfig(
                tls_enabled=True,
                tls_key_path="/path/to/key.pem"
            )


class TestTemporalClient:
    """Test cases for TemporalClient."""

    def test_temporal_client_creation(self):
        """Test creating a TemporalClient."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        assert client.config == config
        assert client._client is None
        assert client._worker is None

    @pytest.mark.asyncio
    async def test_temporal_client_connect_success(self):
        """Test successful connection to Temporal server."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        mock_temporal_client = AsyncMock()
        
        with patch('temporal_client.Client.connect', return_value=mock_temporal_client) as mock_connect:
            await client.connect()
            
            mock_connect.assert_called_once_with(config.server_url)
            assert client._client == mock_temporal_client
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_temporal_client_connect_with_tls(self):
        """Test connection with TLS configuration."""
        config = TemporalConfig(
            tls_enabled=True,
            tls_cert_path="/path/to/cert.pem",
            tls_key_path="/path/to/key.pem"
        )
        client = TemporalClient(config)
        
        mock_temporal_client = AsyncMock()
        mock_tls_config = Mock()
        
        with patch('temporal_client.Client.connect', return_value=mock_temporal_client) as mock_connect, \
             patch('temporal_client.TLSConfig', return_value=mock_tls_config) as mock_tls:
            
            await client.connect()
            
            mock_tls.assert_called_once_with(
                client_cert_path=config.tls_cert_path,
                client_private_key_path=config.tls_key_path
            )
            mock_connect.assert_called_once_with(
                config.server_url,
                tls=mock_tls_config
            )

    @pytest.mark.asyncio
    async def test_temporal_client_connect_failure(self):
        """Test connection failure handling."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        with patch('temporal_client.Client.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await client.connect()
            
            assert client._client is None
            assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_temporal_client_disconnect(self):
        """Test disconnecting from Temporal server."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        # Mock a connected client
        mock_temporal_client = AsyncMock()
        client._client = mock_temporal_client
        
        await client.disconnect()
        
        mock_temporal_client.close.assert_called_once()
        assert client._client is None
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_temporal_client_disconnect_when_not_connected(self):
        """Test disconnecting when not connected."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        # Should not raise an exception
        await client.disconnect()
        assert client._client is None

    def test_temporal_client_create_worker_not_connected(self):
        """Test creating worker when not connected raises error."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        with pytest.raises(RuntimeError, match="Client is not connected"):
            client.create_worker([], [])

    @pytest.mark.asyncio
    async def test_temporal_client_create_worker_success(self):
        """Test successful worker creation."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        # Mock connected client
        mock_temporal_client = AsyncMock()
        client._client = mock_temporal_client
        
        mock_worker = Mock()
        workflows = [Mock()]
        activities = [Mock()]
        
        with patch('temporal_client.Worker', return_value=mock_worker) as mock_worker_class:
            worker = client.create_worker(workflows, activities)
            
            mock_worker_class.assert_called_once_with(
                mock_temporal_client,
                task_queue=config.task_queue,
                workflows=workflows,
                activities=activities
            )
            assert worker == mock_worker
            assert client._worker == mock_worker

    @pytest.mark.asyncio
    async def test_temporal_client_start_worker_not_created(self):
        """Test starting worker when not created raises error."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        with pytest.raises(RuntimeError, match="Worker is not created"):
            await client.start_worker()

    @pytest.mark.asyncio
    async def test_temporal_client_start_worker_success(self):
        """Test successful worker start."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        # Mock worker
        mock_worker = AsyncMock()
        client._worker = mock_worker
        
        await client.start_worker()
        
        mock_worker.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_temporal_client_stop_worker(self):
        """Test stopping worker."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        # Mock worker
        mock_worker = AsyncMock()
        client._worker = mock_worker
        
        await client.stop_worker()
        
        mock_worker.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_temporal_client_stop_worker_when_not_created(self):
        """Test stopping worker when not created."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        # Should not raise an exception
        await client.stop_worker()

    def test_temporal_client_get_client_not_connected(self):
        """Test getting client when not connected raises error."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        with pytest.raises(RuntimeError, match="Client is not connected"):
            client.get_client()

    @pytest.mark.asyncio
    async def test_temporal_client_get_client_success(self):
        """Test getting client when connected."""
        config = TemporalConfig()
        client = TemporalClient(config)
        
        # Mock connected client
        mock_temporal_client = AsyncMock()
        client._client = mock_temporal_client
        
        result = client.get_client()
        assert result == mock_temporal_client