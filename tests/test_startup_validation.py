"""Tests for Nova Sonic startup validation.

This module tests the startup validation logic that checks Nova Sonic
connectivity when the server starts.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO


class TestStartupValidation:
    """Test suite for startup validation functionality."""
    
    def test_validation_passes_in_dev_mode(self):
        """Test that validation passes when dev mode is enabled."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            # Import the validation function
            from run import validate_nova_sonic_on_startup
            
            # Capture stdout
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                result = validate_nova_sonic_on_startup()
            
            assert result is True
            output = captured_output.getvalue()
            assert "Development mode enabled" in output
            assert "mock audio" in output
    
    def test_validation_passes_when_nova_sonic_available(self):
        """Test that validation passes when Nova Sonic is available."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "false"}):
            # Mock NovaSonicClient at the import location
            with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client.validate_model_availability.return_value = True
                mock_client.get_model_id.return_value = "amazon.nova-sonic-v1:0"
                mock_client.get_region.return_value = "us-east-1"
                mock_client_class.return_value = mock_client
                
                from run import validate_nova_sonic_on_startup
                
                # Capture stdout
                captured_output = StringIO()
                with patch('sys.stdout', captured_output):
                    result = validate_nova_sonic_on_startup()
                
                assert result is True
                output = captured_output.getvalue()
                assert "Nova Sonic is available" in output
                assert "amazon.nova-sonic-v1:0" in output
                assert "us-east-1" in output
    
    def test_validation_fails_when_nova_sonic_unavailable(self):
        """Test that validation fails when Nova Sonic is unavailable."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "false"}):
            # Mock NovaSonicClient at the import location
            with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client.validate_model_availability.return_value = False
                mock_client_class.return_value = mock_client
                
                from run import validate_nova_sonic_on_startup
                
                # Capture stdout
                captured_output = StringIO()
                with patch('sys.stdout', captured_output):
                    result = validate_nova_sonic_on_startup()
                
                assert result is False
                output = captured_output.getvalue()
                assert "ERROR: Nova Sonic is not available" in output
                assert "Possible causes:" in output
                assert "To fix this:" in output
    
    def test_validation_fails_on_exception(self):
        """Test that validation fails gracefully on exception."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "false"}):
            # Mock NovaSonicClient to raise exception
            with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
                mock_client_class.side_effect = Exception("Connection error")
                
                from run import validate_nova_sonic_on_startup
                
                # Capture stdout
                captured_output = StringIO()
                with patch('sys.stdout', captured_output):
                    result = validate_nova_sonic_on_startup()
                
                assert result is False
                output = captured_output.getvalue()
                assert "ERROR: Failed to validate Nova Sonic connectivity" in output
                assert "Connection error" in output
    
    def test_validation_shows_helpful_error_messages(self):
        """Test that validation shows helpful error messages."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "false"}):
            # Mock NovaSonicClient
            with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client.validate_model_availability.return_value = False
                mock_client_class.return_value = mock_client
                
                from run import validate_nova_sonic_on_startup
                
                # Capture stdout
                captured_output = StringIO()
                with patch('sys.stdout', captured_output):
                    result = validate_nova_sonic_on_startup()
                
                output = captured_output.getvalue()
                # Check for helpful suggestions
                assert "AWS_REGION" in output
                assert "AWS credentials" in output
                assert "bedrock:InvokeModel" in output
                assert "ENABLE_DEV_MODE=true" in output


class TestAppStartupEvent:
    """Test suite for FastAPI app startup event."""
    
    @pytest.mark.asyncio
    async def test_startup_event_logs_in_dev_mode(self, caplog):
        """Test that startup event logs correctly in dev mode."""
        import logging
        caplog.set_level(logging.INFO)
        
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            # Import and trigger startup event
            from app import validate_nova_sonic_on_startup
            
            await validate_nova_sonic_on_startup()
            
            # Check logs
            assert any("Development mode enabled" in record.message for record in caplog.records)
            assert any("mock audio" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_startup_event_logs_success(self, caplog):
        """Test that startup event logs success when Nova Sonic is available."""
        import logging
        caplog.set_level(logging.INFO)
        
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "false"}):
            # Mock NovaSonicClient at the import location
            with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client.validate_model_availability.return_value = True
                mock_client.get_model_id.return_value = "amazon.nova-sonic-v1:0"
                mock_client.get_region.return_value = "us-east-1"
                mock_client_class.return_value = mock_client
                
                from app import validate_nova_sonic_on_startup
                
                await validate_nova_sonic_on_startup()
                
                # Check logs
                assert any("Nova Sonic is available" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_startup_event_logs_error(self, caplog):
        """Test that startup event logs error when Nova Sonic is unavailable."""
        import logging
        caplog.set_level(logging.ERROR)
        
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "false"}):
            # Mock NovaSonicClient at the import location
            with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client.validate_model_availability.return_value = False
                mock_client_class.return_value = mock_client
                
                from app import validate_nova_sonic_on_startup
                
                await validate_nova_sonic_on_startup()
                
                # Check logs
                assert any("Nova Sonic is not available" in record.message for record in caplog.records)
                assert any("degraded" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_startup_event_handles_exception(self, caplog):
        """Test that startup event handles exceptions gracefully."""
        import logging
        caplog.set_level(logging.ERROR)
        
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "false"}):
            # Mock NovaSonicClient to raise exception
            with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
                mock_client_class.side_effect = Exception("Connection error")
                
                from app import validate_nova_sonic_on_startup
                
                await validate_nova_sonic_on_startup()
                
                # Check logs
                assert any("Failed to validate Nova Sonic connectivity" in record.message for record in caplog.records)
                assert any("Connection error" in record.message for record in caplog.records)


class TestProductionModeValidation:
    """Test suite for production mode validation behavior."""
    
    def test_production_mode_prevents_startup_on_failure(self):
        """Test that production mode prevents server startup when validation fails."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "false"}):
            # Mock NovaSonicClient at the import location
            with patch('mock_interview_coach.voice_interface.NovaSonicClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client.validate_model_availability.return_value = False
                mock_client_class.return_value = mock_client
                
                from run import validate_nova_sonic_on_startup
                
                result = validate_nova_sonic_on_startup()
                
                # In production mode, validation failure should return False
                assert result is False
    
    def test_dev_mode_allows_startup_regardless(self):
        """Test that dev mode allows server startup regardless of Nova Sonic availability."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            # Don't even mock NovaSonicClient - it shouldn't be called
            from run import validate_nova_sonic_on_startup
            
            result = validate_nova_sonic_on_startup()
            
            # In dev mode, validation should always pass
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
