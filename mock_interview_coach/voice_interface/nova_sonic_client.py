"""Nova Sonic Client for AWS Bedrock integration.

This module provides the NovaSonicClient class for interfacing with Amazon Nova Sonic
models on AWS Bedrock for speech-to-text and text-to-speech operations.
"""

import os
import base64
import json
import logging
import asyncio
from typing import Optional, Dict, Any, Callable, TypeVar
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv

from mock_interview_coach.models import Language
from mock_interview_coach.voice_interface.mock_audio_generator import MockAudioGenerator

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

T = TypeVar('T')


class VoiceErrorCode(Enum):
    """Voice-specific error codes."""
    # API errors
    NOVA_SONIC_UNAVAILABLE = "nova_sonic_unavailable"
    NOVA_SONIC_TIMEOUT = "nova_sonic_timeout"
    NOVA_SONIC_ERROR = "nova_sonic_error"
    TRANSCRIPTION_EMPTY = "transcription_empty"
    MODEL_NOT_AVAILABLE = "model_not_available"

    # Configuration errors
    INVALID_CONFIGURATION = "invalid_configuration"
    MISSING_CREDENTIALS = "missing_credentials"
    
    # Network errors
    CONNECTION_ERROR = "connection_error"
    RETRY_EXHAUSTED = "retry_exhausted"



@dataclass
class NovaSonicConfig:
    """Configuration for Nova Sonic client."""
    model_id: str = "amazon.nova-sonic-v1:0"
    region: str = "us-east-1"
    max_retries: int = 2
    timeout_seconds: int = 30
    input_sample_rate: int = 16000
    output_format: str = "mp3"  # or "opus"


class NovaSonicClient:
    """Client for interfacing with AWS Bedrock Nova Sonic API.
    
    This client handles both speech-to-text (transcription) and text-to-speech
    (synthesis) operations using Amazon Nova Sonic models.
    
    Attributes:
        config: Configuration for the Nova Sonic client
        _bedrock_runtime: AWS Bedrock Runtime client
    """
    
    def __init__(
        self,
        model_id: Optional[str] = None,
        region: Optional[str] = None,
        config: Optional[NovaSonicConfig] = None
    ):
        """Initialize the Nova Sonic client.
        
        Args:
            model_id: Nova Sonic model ID (overrides config and env var)
            region: AWS region (overrides config and env var)
            config: Complete configuration object (optional)
            
        Raises:
            ValueError: If AWS credentials are not configured (unless dev mode is enabled)
        """
        # Check if development mode is enabled
        self.dev_mode = os.getenv('ENABLE_DEV_MODE', 'false').lower() == 'true'
        
        # Initialize configuration
        if config:
            self.config = config
        else:
            self.config = NovaSonicConfig(
                model_id=model_id or os.getenv('NOVA_SONIC_MODEL_ID', 'amazon.nova-sonic-v1:0'),
                region=region or os.getenv('AWS_REGION', 'us-east-1'),
                max_retries=int(os.getenv('NOVA_SONIC_MAX_RETRIES', '2')),
                timeout_seconds=int(os.getenv('NOVA_SONIC_TIMEOUT', '30')),
                output_format=os.getenv('NOVA_SONIC_OUTPUT_FORMAT', 'mp3')
            )
        
        # Initialize mock audio generator if in dev mode
        if self.dev_mode:
            self.mock_audio_generator = MockAudioGenerator()
            logger.info("🔧 Development mode enabled - using mock audio instead of Nova Sonic API")
            logger.info(f"📁 Mock audio directory: {self.mock_audio_generator.mock_audio_dir}")
            
            # Log available mock files
            available_mocks = self.mock_audio_generator.get_available_mock_files()
            logger.info(f"📝 Available mock audio files: {len(available_mocks)}")
            for phrase_key in available_mocks.keys():
                logger.debug(f"  - {phrase_key}.mp3")
            
            # Skip AWS credential validation in dev mode
            self._bedrock_runtime = None
            return
        
        # Validate credentials (only in production mode)
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if not aws_access_key or not aws_secret_key:
            raise ValueError(
                "AWS credentials not configured. Please set AWS_ACCESS_KEY_ID "
                "and AWS_SECRET_ACCESS_KEY environment variables."
            )
        
        # Initialize AWS Bedrock Runtime client
        try:
            self._bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=self.config.region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize AWS Bedrock client: {str(e)}")
    
    async def _call_with_retry(
        self,
        operation: Callable[[], T],
        operation_name: str,
        session_id: Optional[str] = None
    ) -> T:
        """Call an operation with exponential backoff retry logic.
        
        This method wraps API calls to Nova Sonic with automatic retry logic
        for transient errors like timeouts and connection errors.
        
        Args:
            operation: The operation to execute (should be a callable)
            operation_name: Name of the operation for logging (e.g., "transcribe_audio")
            session_id: Optional session ID for context logging
            
        Returns:
            The result of the operation
            
        Raises:
            RuntimeError: If all retry attempts are exhausted
        """
        max_attempts = self.config.max_retries + 1  # +1 for initial attempt
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                # Log attempt
                context = {
                    "operation": operation_name,
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                    "timestamp": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
                }
                if session_id:
                    context["session_id"] = session_id
                
                if attempt > 0:
                    logger.info(f"Retrying {operation_name} (attempt {attempt + 1}/{max_attempts})", extra=context)
                
                # Execute operation
                result = operation()
                
                # Log success if this was a retry
                if attempt > 0:
                    logger.info(f"{operation_name} succeeded on attempt {attempt + 1}", extra=context)
                
                return result
                
            except (ClientError, BotoCoreError) as e:
                last_exception = e
                
                # Determine if error is retryable
                is_timeout = False
                is_connection_error = False
                
                if isinstance(e, ClientError):
                    error_code = e.response.get('Error', {}).get('Code', '')
                    is_timeout = 'Timeout' in error_code or 'RequestTimeout' in error_code
                    is_connection_error = 'ServiceUnavailable' in error_code or 'ThrottlingException' in error_code
                elif isinstance(e, BotoCoreError):
                    is_connection_error = True
                
                # Log error with context
                error_context = {
                    **context,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "is_timeout": is_timeout,
                    "is_connection_error": is_connection_error,
                }
                logger.error(f"{operation_name} failed on attempt {attempt + 1}", extra=error_context)
                
                # Only retry for timeout and connection errors
                if not (is_timeout or is_connection_error):
                    logger.warning(f"{operation_name} failed with non-retryable error", extra=error_context)
                    raise
                
                # If this was the last attempt, raise
                if attempt >= max_attempts - 1:
                    logger.error(
                        f"{operation_name} exhausted all {max_attempts} retry attempts",
                        extra=error_context
                    )
                    raise RuntimeError(
                        f"{operation_name} failed after {max_attempts} attempts. "
                        f"Last error: {str(e)}. "
                        f"Error code: {VoiceErrorCode.RETRY_EXHAUSTED.value}"
                    )
                
                # Calculate exponential backoff delay: 1s, 2s
                delay = 2 ** attempt  # 2^0=1s, 2^1=2s
                logger.info(f"Waiting {delay}s before retry", extra=error_context)
                await asyncio.sleep(delay)
            
            except Exception as e:
                # Non-retryable exception, log and re-raise immediately
                error_context = {
                    **context,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
                logger.error(f"{operation_name} failed with unexpected error", extra=error_context)
                raise
        
        # This should never be reached, but just in case
        raise RuntimeError(
            f"{operation_name} failed after {max_attempts} attempts. "
            f"Last error: {str(last_exception)}. "
            f"Error code: {VoiceErrorCode.RETRY_EXHAUSTED.value}"
        )
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "pcm",
        session_id: Optional[str] = None
    ) -> str:
        """Transcribe audio to text using Nova Sonic.
        
        Args:
            audio_data: Raw audio data bytes
            audio_format: Audio format (pcm, opus, mp3)
            session_id: Optional session ID for context logging
            
        Returns:
            Transcribed text
            
        Raises:
            RuntimeError: If transcription fails or returns empty text
        """
        # Use mock transcription in dev mode
        if self.dev_mode:
            logger.debug(f"🔧 Dev mode: Generating mock transcription for {len(audio_data)} bytes")
            transcription = self.mock_audio_generator.get_mock_transcription(audio_data)
            logger.info(f"🔧 Dev mode: Mock transcription: {transcription[:50]}...")
            return transcription
        
        def _transcribe() -> str:
            """Inner function to perform the actual transcription."""
            # Encode audio data to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare request body for speech-to-text
            request_body = {
                "inputModality": "SPEECH",
                "outputModality": "TEXT",
                "audioInput": {
                    "format": audio_format.upper(),
                    "data": audio_base64
                }
            }
            
            # Call Nova Sonic API (let exceptions propagate to retry wrapper)
            response = self._bedrock_runtime.invoke_model(
                modelId=self.config.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract transcription
            transcription = response_body.get('output', {}).get('text', '')
            
            # Validate transcription is not empty
            if not transcription or not transcription.strip():
                raise RuntimeError(
                    f"Transcription returned empty text. Error code: {VoiceErrorCode.TRANSCRIPTION_EMPTY.value}"
                )
            
            return transcription.strip()
        
        # Use retry wrapper - it will catch ClientError and BotoCoreError
        try:
            return await self._call_with_retry(
                operation=_transcribe,
                operation_name="transcribe_audio",
                session_id=session_id
            )
        except (ClientError, BotoCoreError) as e:
            # Convert boto exceptions to RuntimeError with proper error codes
            if isinstance(e, ClientError):
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                raise RuntimeError(
                    f"Nova Sonic API error ({error_code}): {error_message}. "
                    f"Error code: {VoiceErrorCode.NOVA_SONIC_ERROR.value}"
                )
            else:  # BotoCoreError
                raise RuntimeError(
                    f"AWS connection error: {str(e)}. "
                    f"Error code: {VoiceErrorCode.NOVA_SONIC_UNAVAILABLE.value}"
                )
    
    async def synthesize_speech(
        self,
        text: str,
        language: Language,
        output_format: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bytes:
        """Synthesize speech from text using Nova Sonic.
        
        Args:
            text: Text to synthesize
            language: Language for speech synthesis
            output_format: Audio output format (mp3, opus), defaults to config
            session_id: Optional session ID for context logging
            
        Returns:
            Audio data as bytes
            
        Raises:
            RuntimeError: If synthesis fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Use mock audio in dev mode
        if self.dev_mode:
            logger.debug(f"🔧 Dev mode: Generating mock audio for text: {text[:50]}...")
            audio_data = self.mock_audio_generator.get_mock_audio(text, language)
            logger.info(f"🔧 Dev mode: Generated mock audio ({len(audio_data)} bytes)")
            return audio_data
        
        format_to_use = output_format or self.config.output_format
        
        def _synthesize() -> bytes:
            """Inner function to perform the actual synthesis."""
            # Prepare request body for text-to-speech
            request_body = {
                "inputModality": "TEXT",
                "outputModality": "SPEECH",
                "textInput": {
                    "text": text,
                    "language": language.value
                },
                "audioOutput": {
                    "format": format_to_use.upper()
                }
            }
            
            # Call Nova Sonic API (let exceptions propagate to retry wrapper)
            response = self._bedrock_runtime.invoke_model(
                modelId=self.config.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract audio data
            audio_base64 = response_body.get('output', {}).get('audio', {}).get('data', '')
            
            if not audio_base64:
                raise RuntimeError("No audio data in response")
            
            # Decode base64 audio
            audio_data = base64.b64decode(audio_base64)
            
            return audio_data
        
        # Use retry wrapper - it will catch ClientError and BotoCoreError
        try:
            return await self._call_with_retry(
                operation=_synthesize,
                operation_name="synthesize_speech",
                session_id=session_id
            )
        except (ClientError, BotoCoreError) as e:
            # Convert boto exceptions to RuntimeError with proper error codes
            if isinstance(e, ClientError):
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                raise RuntimeError(
                    f"Nova Sonic API error ({error_code}): {error_message}. "
                    f"Error code: {VoiceErrorCode.NOVA_SONIC_ERROR.value}"
                )
            else:  # BotoCoreError
                raise RuntimeError(
                    f"AWS connection error: {str(e)}. "
                    f"Error code: {VoiceErrorCode.NOVA_SONIC_UNAVAILABLE.value}"
                )
    
    def validate_model_availability(self) -> bool:
        """Validate that the configured Nova Sonic model is available.
        
        This method checks if the model is accessible in the configured region
        by attempting to list available models or making a test call.
        
        Returns:
            True if model is available, False otherwise
        """
        # In dev mode, always return True
        if self.dev_mode:
            logger.debug("🔧 Dev mode: Skipping model availability validation")
            return True
        
        try:
            # Try to get model information
            bedrock_client = boto3.client(
                'bedrock',
                region_name=self.config.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            # List foundation models and check if our model is available
            response = bedrock_client.list_foundation_models()
            available_models = [
                model['modelId'] 
                for model in response.get('modelSummaries', [])
            ]
            
            # Check if our model is in the list
            if self.config.model_id in available_models:
                return True
            
            # If not in list, try a test invocation with minimal data
            # This is a fallback check in case the model list is incomplete
            try:
                test_body = {
                    "inputModality": "TEXT",
                    "outputModality": "TEXT",
                    "textInput": {
                        "text": "test",
                        "language": "en"
                    }
                }
                
                self._bedrock_runtime.invoke_model(
                    modelId=self.config.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(test_body)
                )
                return True
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                # If we get a validation error about the model, it's not available
                if 'ValidationException' in error_code or 'ResourceNotFoundException' in error_code:
                    return False
                # Other errors might be transient, so we consider the model available
                return True
                
        except Exception:
            # If we can't validate, assume unavailable
            return False
    
    async def health_check(self) -> bool:
        """Check if Nova Sonic service is healthy and accessible.
        
        This method performs a lightweight check to verify the service is responding.
        
        Returns:
            True if service is healthy, False otherwise
        """
        # In dev mode, always return True
        if self.dev_mode:
            logger.debug("🔧 Dev mode: Skipping health check (always healthy)")
            return True
        
        try:
            # Perform a minimal test call
            test_text = "health check"
            test_body = {
                "inputModality": "TEXT",
                "outputModality": "TEXT",
                "textInput": {
                    "text": test_text,
                    "language": "en"
                }
            }
            
            response = self._bedrock_runtime.invoke_model(
                modelId=self.config.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(test_body)
            )
            
            # If we get a response, service is healthy
            response_body = json.loads(response['body'].read())
            return 'output' in response_body
            
        except Exception:
            return False
    
    def get_model_id(self) -> str:
        """Get the currently configured model ID.
        
        Returns:
            Model ID string
        """
        return self.config.model_id
    
    def get_region(self) -> str:
        """Get the currently configured AWS region.
        
        Returns:
            AWS region string
        """
        return self.config.region
