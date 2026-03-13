"""Unit tests for WebSocketHandler.

Tests the WebSocket handler for message routing, connection management,
and heartbeat monitoring.
"""

import pytest
import asyncio
import json
import base64
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from mock_interview_coach.voice_interface.websocket_handler import (
    WebSocketHandler,
    MessageType
)
from mock_interview_coach.voice_interface.audio_quality_validator import (
    ValidationResult,
    AudioIssue
)
from mock_interview_coach.models import Language


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


@pytest.fixture
def mock_nova_client():
    """Create a mock Nova Sonic client."""
    client = AsyncMock()
    client.transcribe_audio = AsyncMock(return_value="Test transcription")
    client.synthesize_speech = AsyncMock(return_value=b"test_audio_data")
    return client


@pytest.fixture
def mock_audio_converter():
    """Create a mock audio converter."""
    converter = Mock()
    converter.convert_to_pcm = Mock(return_value=b"converted_pcm_data")
    return converter


@pytest.fixture
def mock_audio_validator():
    """Create a mock audio quality validator."""
    validator = Mock()
    validator.validate = Mock(return_value=ValidationResult(
        is_valid=True,
        issues=[],
        suggestions=[]
    ))
    return validator


@pytest.fixture
def websocket_handler(
    mock_websocket,
    mock_nova_client,
    mock_audio_converter,
    mock_audio_validator
):
    """Create a WebSocketHandler instance with mocked dependencies."""
    return WebSocketHandler(
        websocket=mock_websocket,
        session_id="test_session_123",
        nova_client=mock_nova_client,
        audio_converter=mock_audio_converter,
        audio_validator=mock_audio_validator,
        heartbeat_interval=1,  # Short interval for testing
        heartbeat_timeout=1
    )


class TestWebSocketHandlerInitialization:
    """Tests for WebSocketHandler initialization."""
    
    def test_initialization_with_all_parameters(
        self,
        mock_websocket,
        mock_nova_client,
        mock_audio_converter,
        mock_audio_validator
    ):
        """Test handler initializes correctly with all parameters."""
        handler = WebSocketHandler(
            websocket=mock_websocket,
            session_id="test_session",
            nova_client=mock_nova_client,
            audio_converter=mock_audio_converter,
            audio_validator=mock_audio_validator,
            heartbeat_interval=30,
            heartbeat_timeout=10
        )
        
        assert handler.websocket == mock_websocket
        assert handler.session_id == "test_session"
        assert handler.nova_client == mock_nova_client
        assert handler.audio_converter == mock_audio_converter
        assert handler.audio_validator == mock_audio_validator
        assert handler.heartbeat_interval == 30
        assert handler.heartbeat_timeout == 10
        assert handler.is_connected_flag is False
        assert handler.heartbeat_task is None
    
    def test_initialization_creates_default_clients(self, mock_websocket):
        """Test handler creates default clients when not provided."""
        with patch('mock_interview_coach.voice_interface.websocket_handler.NovaSonicClient'), \
             patch('mock_interview_coach.voice_interface.websocket_handler.AudioConverter'), \
             patch('mock_interview_coach.voice_interface.websocket_handler.AudioQualityValidator'):
            
            handler = WebSocketHandler(
                websocket=mock_websocket,
                session_id="test_session"
            )
            
            assert handler.nova_client is not None
            assert handler.audio_converter is not None
            assert handler.audio_validator is not None


class TestConnectionManagement:
    """Tests for WebSocket connection management."""
    
    @pytest.mark.asyncio
    async def test_is_connected_returns_false_initially(self, websocket_handler):
        """Test is_connected returns False before connection."""
        assert websocket_handler.is_connected() is False
    
    @pytest.mark.asyncio
    async def test_connection_accepts_websocket(self, websocket_handler, mock_websocket):
        """Test handle_connection accepts the WebSocket."""
        # Simulate immediate disconnect to exit the loop
        mock_websocket.receive_text.side_effect = asyncio.CancelledError()
        
        try:
            await websocket_handler.handle_connection()
        except asyncio.CancelledError:
            pass
        
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_sets_connected_flag(self, websocket_handler, mock_websocket):
        """Test handle_connection sets is_connected flag."""
        # Simulate immediate disconnect
        mock_websocket.receive_text.side_effect = asyncio.CancelledError()
        
        try:
            await websocket_handler.handle_connection()
        except asyncio.CancelledError:
            pass
        
        # Flag should be False after connection closes
        assert websocket_handler.is_connected() is False


class TestMessageRouting:
    """Tests for message routing to appropriate handlers."""
    
    @pytest.mark.asyncio
    async def test_routes_audio_message_to_handler(
        self,
        websocket_handler,
        mock_websocket,
        mock_nova_client
    ):
        """Test audio messages are routed to handle_audio_message."""
        # Create test audio message
        audio_data = b"test_audio_data"
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "audio",
            "data": audio_b64,
            "format": "pcm"
        }
        
        # Simulate receiving one message then disconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps(message),
            asyncio.CancelledError()
        ]
        
        try:
            await websocket_handler.handle_connection()
        except asyncio.CancelledError:
            pass
        
        # Verify transcription was called
        mock_nova_client.transcribe_audio.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_routes_text_message_to_handler(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test text messages are routed to handle_text_message."""
        message = {
            "type": "text",
            "text": "Test text input"
        }
        
        # Simulate receiving one message then disconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps(message),
            asyncio.CancelledError()
        ]
        
        try:
            await websocket_handler.handle_connection()
        except asyncio.CancelledError:
            pass
        
        # Verify transcript was sent back
        assert mock_websocket.send_json.call_count >= 1
        # Find the transcript message
        calls = [call[0][0] for call in mock_websocket.send_json.call_args_list]
        transcript_calls = [c for c in calls if c.get("type") == "transcript"]
        assert len(transcript_calls) == 1
        assert transcript_calls[0]["text"] == "Test text input"
    
    @pytest.mark.asyncio
    async def test_routes_ping_message_to_handler(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test ping messages are routed to ping handler."""
        message = {"type": "ping"}
        
        # Simulate receiving one message then disconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps(message),
            asyncio.CancelledError()
        ]
        
        try:
            await websocket_handler.handle_connection()
        except asyncio.CancelledError:
            pass
        
        # Verify pong was sent
        assert mock_websocket.send_json.call_count >= 1
        # Find the pong message
        calls = [call[0][0] for call in mock_websocket.send_json.call_args_list]
        pong_calls = [c for c in calls if c.get("type") == "pong"]
        assert len(pong_calls) == 1
    
    @pytest.mark.asyncio
    async def test_handles_unknown_message_type(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test unknown message types send error response."""
        message = {"type": "unknown_type"}
        
        # Simulate receiving one message then disconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps(message),
            asyncio.CancelledError()
        ]
        
        try:
            await websocket_handler.handle_connection()
        except asyncio.CancelledError:
            pass
        
        # Verify error was sent
        assert mock_websocket.send_json.call_count >= 1
        # Find the error message
        calls = [call[0][0] for call in mock_websocket.send_json.call_args_list]
        error_calls = [c for c in calls if c.get("type") == "error"]
        assert len(error_calls) == 1
        assert "unknown_message_type" in error_calls[0]["code"]
    
    @pytest.mark.asyncio
    async def test_handles_invalid_json(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test invalid JSON sends error response."""
        # Simulate receiving invalid JSON then disconnect
        mock_websocket.receive_text.side_effect = [
            "invalid json {",
            asyncio.CancelledError()
        ]
        
        try:
            await websocket_handler.handle_connection()
        except asyncio.CancelledError:
            pass
        
        # Verify error was sent
        assert mock_websocket.send_json.call_count >= 1
        # Find the error message
        calls = [call[0][0] for call in mock_websocket.send_json.call_args_list]
        error_calls = [c for c in calls if c.get("type") == "error"]
        assert len(error_calls) == 1
        assert "invalid_json" in error_calls[0]["code"]
    
    @pytest.mark.asyncio
    async def test_handles_message_without_type_field(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test messages without 'type' field send error response."""
        message = {"data": "some data"}
        
        # Simulate receiving message without type then disconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps(message),
            asyncio.CancelledError()
        ]
        
        try:
            await websocket_handler.handle_connection()
        except asyncio.CancelledError:
            pass
        
        # Verify error was sent
        assert mock_websocket.send_json.call_count >= 1
        # Find the error message
        calls = [call[0][0] for call in mock_websocket.send_json.call_args_list]
        error_calls = [c for c in calls if c.get("type") == "error"]
        assert len(error_calls) == 1
        assert "invalid_message" in error_calls[0]["code"]


class TestAudioMessageHandling:
    """Tests for audio message handling."""
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_transcribes_audio(
        self,
        websocket_handler,
        mock_nova_client
    ):
        """Test audio message triggers transcription."""
        audio_data = b"test_audio_data"
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "audio",
            "data": audio_b64,
            "format": "pcm"
        }
        
        await websocket_handler.handle_audio_message(message)
        
        mock_nova_client.transcribe_audio.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_validates_quality(
        self,
        websocket_handler,
        mock_audio_validator
    ):
        """Test audio message validates audio quality."""
        audio_data = b"test_audio_data"
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "audio",
            "data": audio_b64,
            "format": "pcm"
        }
        
        await websocket_handler.handle_audio_message(message)
        
        mock_audio_validator.validate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_rejects_poor_quality(
        self,
        websocket_handler,
        mock_audio_validator,
        mock_websocket,
        mock_nova_client
    ):
        """Test poor quality audio is rejected with error."""
        # Configure validator to return invalid result
        mock_audio_validator.validate.return_value = ValidationResult(
            is_valid=False,
            issues=[AudioIssue.SILENT],
            suggestions=["Speak louder"]
        )
        
        audio_data = b"test_audio_data"
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "audio",
            "data": audio_b64,
            "format": "pcm"
        }
        
        await websocket_handler.handle_audio_message(message)
        
        # Verify error was sent
        mock_websocket.send_json.assert_called()
        error_call = mock_websocket.send_json.call_args[0][0]
        assert error_call["type"] == "error"
        assert "audio_quality_failed" in error_call["code"]
        
        # Verify transcription was NOT called
        mock_nova_client.transcribe_audio.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_converts_format(
        self,
        websocket_handler,
        mock_audio_converter,
        mock_nova_client
    ):
        """Test audio format conversion for non-PCM formats."""
        audio_data = b"test_audio_data"
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "audio",
            "data": audio_b64,
            "format": "mp3"  # Non-PCM format
        }
        
        await websocket_handler.handle_audio_message(message)
        
        # Verify conversion was called
        mock_audio_converter.convert_to_pcm.assert_called_once()
        
        # Verify transcription was called with converted data
        mock_nova_client.transcribe_audio.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_sends_transcript(
        self,
        websocket_handler,
        mock_websocket,
        mock_nova_client
    ):
        """Test successful transcription sends transcript to client."""
        mock_nova_client.transcribe_audio.return_value = "Test transcription"
        
        audio_data = b"test_audio_data"
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "audio",
            "data": audio_b64,
            "format": "pcm"
        }
        
        await websocket_handler.handle_audio_message(message)
        
        # Verify transcript was sent
        mock_websocket.send_json.assert_called()
        transcript_call = mock_websocket.send_json.call_args[0][0]
        assert transcript_call["type"] == "transcript"
        assert transcript_call["text"] == "Test transcription"
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_handles_missing_data(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test missing audio data sends error."""
        message = {
            "type": "audio",
            "format": "pcm"
            # Missing 'data' field
        }
        
        await websocket_handler.handle_audio_message(message)
        
        # Verify error was sent
        mock_websocket.send_json.assert_called()
        error_call = mock_websocket.send_json.call_args[0][0]
        assert error_call["type"] == "error"
        assert "missing_audio_data" in error_call["code"]
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_handles_invalid_base64(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test invalid base64 encoding sends error."""
        message = {
            "type": "audio",
            "data": "invalid_base64!!!",
            "format": "pcm"
        }
        
        await websocket_handler.handle_audio_message(message)
        
        # Verify error was sent
        mock_websocket.send_json.assert_called()
        error_call = mock_websocket.send_json.call_args[0][0]
        assert error_call["type"] == "error"
        assert "invalid_encoding" in error_call["code"]


class TestTextMessageHandling:
    """Tests for text message handling."""
    
    @pytest.mark.asyncio
    async def test_handle_text_message_sends_transcript(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test text message sends transcript back."""
        message = {
            "type": "text",
            "text": "Test text input"
        }
        
        await websocket_handler.handle_text_message(message)
        
        # Verify transcript was sent
        mock_websocket.send_json.assert_called()
        transcript_call = mock_websocket.send_json.call_args[0][0]
        assert transcript_call["type"] == "transcript"
        assert transcript_call["text"] == "Test text input"
    
    @pytest.mark.asyncio
    async def test_handle_text_message_handles_empty_text(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test empty text sends error."""
        message = {
            "type": "text",
            "text": ""
        }
        
        await websocket_handler.handle_text_message(message)
        
        # Verify error was sent
        mock_websocket.send_json.assert_called()
        error_call = mock_websocket.send_json.call_args[0][0]
        assert error_call["type"] == "error"
        assert "empty_text" in error_call["code"]
    
    @pytest.mark.asyncio
    async def test_handle_text_message_strips_whitespace(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test text message strips leading/trailing whitespace."""
        message = {
            "type": "text",
            "text": "  Test text  "
        }
        
        await websocket_handler.handle_text_message(message)
        
        # Verify transcript was sent with stripped text
        mock_websocket.send_json.assert_called()
        transcript_call = mock_websocket.send_json.call_args[0][0]
        assert transcript_call["text"] == "Test text"


class TestResponseMethods:
    """Tests for response sending methods."""
    
    @pytest.mark.asyncio
    async def test_send_transcript(self, websocket_handler, mock_websocket):
        """Test send_transcript sends correct message format."""
        await websocket_handler.send_transcript("Test transcription")
        
        mock_websocket.send_json.assert_called_once()
        message = mock_websocket.send_json.call_args[0][0]
        
        assert message["type"] == "transcript"
        assert message["text"] == "Test transcription"
        assert "timestamp" in message
    
    @pytest.mark.asyncio
    async def test_send_audio(self, websocket_handler, mock_websocket):
        """Test send_audio sends correct message format."""
        audio_data = b"test_audio_data"
        
        await websocket_handler.send_audio(audio_data, "mp3")
        
        mock_websocket.send_json.assert_called_once()
        message = mock_websocket.send_json.call_args[0][0]
        
        assert message["type"] == "audio"
        assert message["format"] == "mp3"
        assert "data" in message
        assert "timestamp" in message
        
        # Verify audio data is base64 encoded
        decoded_audio = base64.b64decode(message["data"])
        assert decoded_audio == audio_data
    
    @pytest.mark.asyncio
    async def test_send_error(self, websocket_handler, mock_websocket):
        """Test send_error sends correct message format."""
        await websocket_handler.send_error(
            "Test error message",
            "test_error_code",
            recoverable=True
        )
        
        mock_websocket.send_json.assert_called_once()
        message = mock_websocket.send_json.call_args[0][0]
        
        assert message["type"] == "error"
        assert message["message"] == "Test error message"
        assert message["code"] == "test_error_code"
        assert message["recoverable"] is True
        assert "timestamp" in message
    
    @pytest.mark.asyncio
    async def test_send_error_defaults_to_non_recoverable(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test send_error defaults recoverable to False."""
        await websocket_handler.send_error("Error", "code")
        
        message = mock_websocket.send_json.call_args[0][0]
        assert message["recoverable"] is False


class TestHeartbeatMonitoring:
    """Tests for heartbeat/ping-pong monitoring."""
    
    @pytest.mark.asyncio
    async def test_heartbeat_monitor_sends_periodic_pings(
        self,
        websocket_handler,
        mock_websocket
    ):
        """Test heartbeat monitor sends periodic ping messages."""
        # Start heartbeat monitor
        websocket_handler.is_connected_flag = True
        websocket_handler.last_pong_time = datetime.utcnow()
        
        # Run monitor for a short time
        monitor_task = asyncio.create_task(websocket_handler._heartbeat_monitor())
        
        # Wait for at least one ping
        await asyncio.sleep(1.5)
        
        # Cancel monitor
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        
        # Verify at least one ping was sent
        assert mock_websocket.send_json.call_count >= 1
        # Find ping messages
        calls = [call[0][0] for call in mock_websocket.send_json.call_args_list]
        ping_calls = [c for c in calls if c.get("type") == "ping"]
        assert len(ping_calls) >= 1
    
    @pytest.mark.asyncio
    async def test_handle_ping_updates_pong_time(self, websocket_handler):
        """Test handling ping updates last_pong_time."""
        # Initialize last_pong_time
        websocket_handler.last_pong_time = datetime.utcnow()
        initial_time = websocket_handler.last_pong_time
        
        await asyncio.sleep(0.1)
        
        await websocket_handler._handle_ping({})
        
        assert websocket_handler.last_pong_time > initial_time
    
    @pytest.mark.asyncio
    async def test_handle_ping_sends_pong(self, websocket_handler, mock_websocket):
        """Test handling ping sends pong response."""
        await websocket_handler._handle_ping({})
        
        mock_websocket.send_json.assert_called_once()
        message = mock_websocket.send_json.call_args[0][0]
        
        assert message["type"] == "pong"
        assert "timestamp" in message


class TestConnectionState:
    """Tests for connection state tracking."""
    
    def test_is_connected_returns_current_state(self, websocket_handler):
        """Test is_connected returns current connection state."""
        assert websocket_handler.is_connected() is False
        
        websocket_handler.is_connected_flag = True
        assert websocket_handler.is_connected() is True
        
        websocket_handler.is_connected_flag = False
        assert websocket_handler.is_connected() is False
