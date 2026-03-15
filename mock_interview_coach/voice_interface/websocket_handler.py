"""WebSocket handler for server-side message routing.

This module provides the WebSocketHandler class for managing WebSocket connections
and routing messages between the client and the voice processing pipeline.
"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect

from mock_interview_coach.voice_interface.nova_sonic_client import NovaSonicClient
from mock_interview_coach.voice_interface.audio_converter import AudioConverter
from mock_interview_coach.voice_interface.audio_quality_validator import AudioQualityValidator
from mock_interview_coach.voice_interface.latency_tracker import LatencyTracker
from mock_interview_coach.models import Language, VoiceSession, AudioState

# Configure logger
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    # Client -> Server
    AUDIO = "audio"
    TEXT = "text"
    PING = "ping"
    
    # Server -> Client
    TRANSCRIPT = "transcript"
    AUDIO_RESPONSE = "audio"
    ERROR = "error"
    PONG = "pong"


class WebSocketHandler:
    """Handler for WebSocket connections and message routing.
    
    This class manages WebSocket connections, routes incoming messages to appropriate
    handlers (audio → transcription, text → evaluation), and sends responses back
    to the client. It also implements heartbeat/ping-pong for connection health monitoring.
    
    Attributes:
        websocket: The WebSocket connection
        session_id: Unique session identifier
        nova_client: Nova Sonic client for STT/TTS
        audio_converter: Audio format converter
        audio_validator: Audio quality validator
        is_connected_flag: Connection state flag
        heartbeat_task: Background task for heartbeat monitoring
        heartbeat_interval: Interval in seconds for heartbeat checks
        heartbeat_timeout: Timeout in seconds for heartbeat response
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        session_id: str,
        nova_client: Optional[NovaSonicClient] = None,
        audio_converter: Optional[AudioConverter] = None,
        audio_validator: Optional[AudioQualityValidator] = None,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 10
    ):
        """Initialize WebSocket handler.
        
        Args:
            websocket: FastAPI WebSocket connection
            session_id: Unique session identifier
            nova_client: Nova Sonic client (creates new if None)
            audio_converter: Audio converter (creates new if None)
            audio_validator: Audio validator (creates new if None)
            heartbeat_interval: Seconds between heartbeat checks (default: 30)
            heartbeat_timeout: Seconds to wait for heartbeat response (default: 10)
        """
        self.websocket = websocket
        self.session_id = session_id
        self.nova_client = nova_client or NovaSonicClient()
        self.audio_converter = audio_converter or AudioConverter()
        self.audio_validator = audio_validator or AudioQualityValidator()
        
        self.is_connected_flag = False
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.last_pong_time: Optional[datetime] = None
        
        # Initialize latency tracker
        self.latency_tracker = LatencyTracker(session_id=session_id)
        
        # Initialize voice session (will be populated when connection is established)
        self.voice_session: Optional[VoiceSession] = None
        
        # Message handlers registry
        self._message_handlers: Dict[str, Callable] = {
            MessageType.AUDIO.value: self.handle_audio_message,
            MessageType.TEXT.value: self.handle_text_message,
            MessageType.PING.value: self._handle_ping,
        }
        
        logger.info(
            f"WebSocketHandler initialized for session {session_id}",
            extra={"session_id": session_id}
        )
    
    async def handle_connection(self) -> None:
        """Handle WebSocket connection lifecycle.
        
        This method accepts the connection, starts the heartbeat monitor,
        and processes incoming messages until the connection is closed.
        
        Raises:
            WebSocketDisconnect: When the client disconnects
        """
        try:
            # Accept the WebSocket connection
            await self.websocket.accept()
            self.is_connected_flag = True
            self.last_pong_time = datetime.utcnow()
            
            # Initialize voice session
            self.voice_session = VoiceSession(
                session_id=self.session_id,
                websocket_id=str(id(self.websocket)),
                audio_state=AudioState.IDLE,
                language=Language.SPANISH,  # Default, should be set by client
                model_id=self.nova_client.get_model_id(),
                is_text_fallback=False,
                created_at=datetime.utcnow()
            )
            
            logger.info(
                f"WebSocket connection accepted for session {self.session_id}",
                extra={"session_id": self.session_id}
            )
            
            # Start heartbeat monitoring
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
            # Process messages
            while self.is_connected_flag:
                try:
                    # Receive message from client
                    data = await self.websocket.receive_text()
                    
                    # Parse message
                    try:
                        message = json.loads(data)
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Invalid JSON received: {e}",
                            extra={"session_id": self.session_id, "data": data[:100]}
                        )
                        await self.send_error(
                            "Invalid message format",
                            "invalid_json"
                        )
                        continue
                    
                    # Validate message structure
                    if not isinstance(message, dict) or "type" not in message:
                        logger.error(
                            "Message missing 'type' field",
                            extra={"session_id": self.session_id, "message_data": str(message)}
                        )
                        await self.send_error(
                            "Message must have 'type' field",
                            "invalid_message"
                        )
                        continue
                    
                    # Route message to appropriate handler
                    message_type = message["type"]
                    handler = self._message_handlers.get(message_type)
                    
                    if handler:
                        await handler(message)
                    else:
                        logger.warning(
                            f"Unknown message type: {message_type}",
                            extra={"session_id": self.session_id, "message_type": message_type}
                        )
                        await self.send_error(
                            f"Unknown message type: {message_type}",
                            "unknown_message_type"
                        )
                
                except WebSocketDisconnect:
                    logger.info(
                        f"WebSocket disconnected for session {self.session_id}",
                        extra={"session_id": self.session_id}
                    )
                    raise
                
                except Exception as e:
                    logger.error(
                        f"Error processing message: {e}",
                        extra={
                            "session_id": self.session_id,
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                    )
                    await self.send_error(
                        "Internal server error",
                        "internal_error"
                    )
        
        except WebSocketDisconnect:
            # Normal disconnection
            pass
        
        finally:
            # Cleanup
            self.is_connected_flag = False
            
            # Cancel heartbeat task
            if self.heartbeat_task and not self.heartbeat_task.done():
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            logger.info(
                f"WebSocket connection closed for session {self.session_id}",
                extra={"session_id": self.session_id}
            )
    
    async def handle_audio_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming audio message for transcription.
        
        This method processes audio data from the client, validates quality,
        converts format if needed, and sends to Nova Sonic for transcription.
        
        Args:
            message: Message dict with 'data' (base64 audio) and 'format' fields
        """
        try:
            # Extract audio data and format
            audio_data_b64 = message.get("data")
            audio_format = message.get("format", "pcm").lower()
            
            if not audio_data_b64:
                await self.send_error("Audio data missing", "missing_audio_data")
                return
            
            # Decode base64 audio data
            import base64
            try:
                audio_data = base64.b64decode(audio_data_b64)
            except Exception as e:
                logger.error(
                    f"Failed to decode base64 audio: {e}",
                    extra={"session_id": self.session_id}
                )
                await self.send_error("Invalid audio data encoding", "invalid_encoding")
                return
            
            logger.info(
                f"Received audio message: format={audio_format}, size={len(audio_data)} bytes",
                extra={"session_id": self.session_id, "format": audio_format, "size": len(audio_data)}
            )
            
            # Validate audio quality
            validation_result = self.audio_validator.validate(audio_data)
            
            if not validation_result.is_valid:
                # Send quality issues back to client
                issues_str = ", ".join([issue.value for issue in validation_result.issues])
                suggestions_str = "; ".join(validation_result.suggestions)
                
                logger.warning(
                    f"Audio quality validation failed: {issues_str}",
                    extra={
                        "session_id": self.session_id,
                        "issues": issues_str,
                        "suggestions": suggestions_str
                    }
                )
                
                await self.send_error(
                    f"Audio quality issues: {issues_str}. {suggestions_str}",
                    "audio_quality_failed",
                    recoverable=True
                )
                return
            
            # Convert audio format if needed (Nova Sonic expects PCM or Opus)
            if audio_format not in ["pcm", "opus"]:
                try:
                    logger.info(
                        f"Converting audio from {audio_format} to PCM",
                        extra={"session_id": self.session_id, "source_format": audio_format}
                    )
                    audio_data = self.audio_converter.convert_to_pcm(audio_data, audio_format)
                    audio_format = "pcm"
                except Exception as e:
                    logger.error(
                        f"Audio conversion failed: {e}",
                        extra={"session_id": self.session_id, "error": str(e)}
                    )
                    await self.send_error(
                        "Failed to convert audio format",
                        "conversion_failed"
                    )
                    return
            
            # Transcribe audio using Nova Sonic
            try:
                # Measure STT latency
                with self.latency_tracker.measure("stt") as metric:
                    transcription = await self.nova_client.transcribe_audio(
                        audio_data=audio_data,
                        audio_format=audio_format,
                        session_id=self.session_id
                    )
                
                # Store metric in voice session
                if self.voice_session:
                    self.voice_session.latency_metrics.append(metric)
                
                logger.info(
                    f"Transcription completed: latency={metric.latency_ms}ms, text_length={len(transcription)}",
                    extra={
                        "session_id": self.session_id,
                        "latency_ms": metric.latency_ms,
                        "text_length": len(transcription)
                    }
                )
                
                # Send transcription to client
                await self.send_transcript(transcription)
            
            except Exception as e:
                logger.error(
                    f"Transcription failed: {e}",
                    extra={
                        "session_id": self.session_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                
                # Determine if this is a Nova Sonic unavailability error
                error_code = "transcription_failed"
                if "ServiceUnavailable" in str(type(e).__name__) or "ThrottlingException" in str(type(e).__name__):
                    error_code = "nova_sonic_unavailable"
                
                await self.send_error(
                    "Failed to transcribe audio. Please try again or switch to text mode.",
                    error_code,
                    recoverable=True
                )
        
        except Exception as e:
            logger.error(
                f"Error handling audio message: {e}",
                extra={
                    "session_id": self.session_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            await self.send_error("Internal error processing audio", "internal_error")
    
    async def send_question_audio(self, question_text: str, language: str = "en") -> None:
        """Synthesize TTS for a question and send audio to client.

        Args:
            question_text: The question text to synthesize
            language: Language code ('en' or 'es')
        """
        try:
            audio_data = await self.nova_client.synthesize_speech(
                text=question_text,
                language=language,
                session_id=self.session_id
            )
            if audio_data:
                await self.send_audio(audio_data, audio_format="mp3")
                logger.info(
                    f"Sent question audio: length={len(audio_data)} bytes",
                    extra={"session_id": self.session_id}
                )
        except Exception as e:
            # TTS failure is non-fatal — client can read the text
            logger.warning(
                f"Question TTS synthesis failed (non-fatal): {e}",
                extra={"session_id": self.session_id, "error": str(e)}
            )

    async def handle_text_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming text message for evaluation.

        This method processes text input from the client (text fallback mode)
        and echoes it back as a transcript for evaluation pipeline.

        Args:
            message: Message dict with 'text' field
        """
        try:
            text = message.get("text", "").strip()

            if not text:
                await self.send_error("Text cannot be empty", "empty_text")
                return

            logger.info(
                f"Received text message: length={len(text)}",
                extra={"session_id": self.session_id, "text_length": len(text)}
            )

            # In text mode, we just echo back the text as a transcript
            # The evaluation pipeline will handle it the same way
            await self.send_transcript(text)
        
        except Exception as e:
            logger.error(
                f"Error handling text message: {e}",
                extra={
                    "session_id": self.session_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            await self.send_error("Internal error processing text", "internal_error")
    
    async def send_transcript(self, text: str) -> None:
        """Send transcription result to client.
        
        Args:
            text: Transcribed text to send
        """
        try:
            message = {
                "type": MessageType.TRANSCRIPT.value,
                "text": text,
                "timestamp": int(datetime.utcnow().timestamp() * 1000)
            }
            
            await self.websocket.send_json(message)
            
            logger.debug(
                f"Sent transcript: length={len(text)}",
                extra={"session_id": self.session_id, "text_length": len(text)}
            )
        
        except Exception as e:
            logger.error(
                f"Failed to send transcript: {e}",
                extra={"session_id": self.session_id, "error": str(e)}
            )
            raise
    
    async def send_audio(self, audio_data: bytes, audio_format: str = "mp3") -> None:
        """Send audio response to client.
        
        Args:
            audio_data: Audio data bytes
            audio_format: Audio format (mp3, opus)
        """
        try:
            import base64
            
            # Encode audio data to base64
            audio_data_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            message = {
                "type": MessageType.AUDIO_RESPONSE.value,
                "data": audio_data_b64,
                "format": audio_format,
                "timestamp": int(datetime.utcnow().timestamp() * 1000)
            }
            
            await self.websocket.send_json(message)
            
            logger.debug(
                f"Sent audio: format={audio_format}, size={len(audio_data)} bytes",
                extra={
                    "session_id": self.session_id,
                    "format": audio_format,
                    "size": len(audio_data)
                }
            )
        
        except Exception as e:
            logger.error(
                f"Failed to send audio: {e}",
                extra={"session_id": self.session_id, "error": str(e)}
            )
            raise
    
    async def send_error(
        self,
        message: str,
        code: str,
        recoverable: bool = False
    ) -> None:
        """Send error message to client.
        
        Args:
            message: Human-readable error message
            code: Error code for client-side handling
            recoverable: Whether the error is recoverable (client can retry)
        """
        try:
            error_message = {
                "type": MessageType.ERROR.value,
                "message": message,
                "code": code,
                "recoverable": recoverable,
                "timestamp": int(datetime.utcnow().timestamp() * 1000)
            }
            
            await self.websocket.send_json(error_message)
            
            logger.debug(
                f"Sent error: code={code}, message={message}",
                extra={
                    "session_id": self.session_id,
                    "error_code": code,
                    "error_message": message,
                    "recoverable": recoverable
                }
            )
        
        except Exception as e:
            logger.error(
                f"Failed to send error message: {e}",
                extra={"session_id": self.session_id, "error": str(e)}
            )
            # Don't raise here, as we're already handling an error
    
    def is_connected(self) -> bool:
        """Check if WebSocket connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        return self.is_connected_flag
    
    def get_latency_metrics(self):
        """Get all collected latency metrics.
        
        Returns:
            List of LatencyMetric objects
        """
        return self.latency_tracker.get_metrics()
    
    def get_voice_session(self) -> Optional[VoiceSession]:
        """Get the current voice session with metrics.
        
        Returns:
            VoiceSession object or None if not initialized
        """
        return self.voice_session
    
    async def _handle_ping(self, message: Dict[str, Any]) -> None:
        """Handle ping message from client.
        
        Args:
            message: Ping message (ignored)
        """
        try:
            # Update last pong time
            self.last_pong_time = datetime.utcnow()
            
            # Send pong response
            pong_message = {
                "type": MessageType.PONG.value,
                "timestamp": int(datetime.utcnow().timestamp() * 1000)
            }
            
            await self.websocket.send_json(pong_message)
            
            logger.debug(
                "Sent pong response",
                extra={"session_id": self.session_id}
            )
        
        except Exception as e:
            logger.error(
                f"Failed to send pong: {e}",
                extra={"session_id": self.session_id, "error": str(e)}
            )
    
    async def _heartbeat_monitor(self) -> None:
        """Monitor connection health with periodic heartbeat checks.
        
        This background task sends periodic ping messages and checks for
        pong responses. If no pong is received within the timeout period,
        the connection is considered dead and will be closed.
        """
        try:
            while self.is_connected_flag:
                # Wait for heartbeat interval
                await asyncio.sleep(self.heartbeat_interval)
                
                # Check if we received a pong recently
                if self.last_pong_time:
                    time_since_pong = (datetime.utcnow() - self.last_pong_time).total_seconds()
                    
                    if time_since_pong > (self.heartbeat_interval + self.heartbeat_timeout):
                        logger.warning(
                            f"Heartbeat timeout: no pong received for {time_since_pong:.1f}s",
                            extra={
                                "session_id": self.session_id,
                                "time_since_pong": time_since_pong
                            }
                        )
                        
                        # Close connection due to timeout
                        self.is_connected_flag = False
                        await self.websocket.close(code=1000, reason="Heartbeat timeout")
                        break
                
                # Send ping to client
                try:
                    ping_message = {
                        "type": MessageType.PING.value,
                        "timestamp": int(datetime.utcnow().timestamp() * 1000)
                    }
                    
                    await self.websocket.send_json(ping_message)
                    
                    logger.debug(
                        "Sent heartbeat ping",
                        extra={"session_id": self.session_id}
                    )
                
                except Exception as e:
                    logger.error(
                        f"Failed to send heartbeat ping: {e}",
                        extra={"session_id": self.session_id, "error": str(e)}
                    )
                    # Connection is likely dead
                    self.is_connected_flag = False
                    break
        
        except asyncio.CancelledError:
            logger.debug(
                "Heartbeat monitor cancelled",
                extra={"session_id": self.session_id}
            )
            raise
        
        except Exception as e:
            logger.error(
                f"Heartbeat monitor error: {e}",
                extra={
                    "session_id": self.session_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
