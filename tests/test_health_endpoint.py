"""Unit tests for health check endpoint."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check_healthy_status(client):
    """Test healthy status when Nova Sonic is available."""
    with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
        # Mock the client instance and health_check method
        mock_client = MagicMock()
        mock_client.health_check = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["nova_sonic_status"] == "available"
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z")


def test_health_check_degraded_status(client):
    """Test degraded status when Nova Sonic is unavailable."""
    with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
        # Mock the client instance and health_check method
        mock_client = MagicMock()
        mock_client.health_check = AsyncMock(return_value=False)
        mock_client_class.return_value = mock_client
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["nova_sonic_status"] == "unavailable"
        assert "timestamp" in data


def test_health_check_unhealthy_status_on_exception(client):
    """Test unhealthy status when exception occurs."""
    with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
        # Mock the client to raise an exception
        mock_client_class.side_effect = Exception("Connection failed")
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["nova_sonic_status"] == "error"
        assert "error" in data
        assert "Connection failed" in data["error"]
        assert "timestamp" in data


def test_health_check_timestamp_format(client):
    """Test that timestamp is in ISO format with Z suffix."""
    with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client.health_check = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify timestamp format
        timestamp = data["timestamp"]
        assert timestamp.endswith("Z")
        # Should be parseable as ISO format
        from datetime import datetime
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None


def test_health_check_includes_all_required_fields(client):
    """Test that response includes all required fields."""
    with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client.health_check = AsyncMock(return_value=True)
        mock_client_class.return_value = mock_client
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields are present
        assert "status" in data
        assert "nova_sonic_status" in data
        assert "timestamp" in data
        
        # Verify status values are valid
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert data["nova_sonic_status"] in ["available", "unavailable", "error"]
