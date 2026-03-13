"""Unit tests for NovaSonicClient."""

import pytest
import os
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError

from mock_interview_coach.voice_interface import (
    NovaSonicClient,
    NovaSonicConfig,
    VoiceErrorCode
)
from mock_interview_coach.models import Language


class TestNovaSonicClientInitialization:
    """Test NovaSonicClient initialization."""
    
    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret',
            'AWS_REGION': 'us-east-1'
        }):
            with patch('boto3.client'):
                client = NovaSonicClient()
                assert client.config.model_id == 'amazon.nova-sonic-v1:0'
                assert client.config.region == 'us-east-1'
                assert client.config.max_retries == 2
    
    def test_init_with_custom_model_id(self):
        """Test initialization with custom model ID."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client'):
                client = NovaSonicClient(model_id='amazon.nova-2-sonic-v1:0')
                assert client.config.model_id == 'amazon.nova-2-sonic-v1:0'
    
    def test_init_with_env_var_model_id(self):
        """Test initialization with model ID from environment variable."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret',
            'NOVA_SONIC_MODEL_ID': 'amazon.nova-2-sonic-v1:0'
        }):
            with patch('boto3.client'):
                client = NovaSonicClient()
                assert client.config.model_id == 'amazon.nova-2-sonic-v1:0'
    
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration object."""
        config = NovaSonicConfig(
            model_id='amazon.nova-2-sonic-v1:0',
            region='us-west-2',
            max_retries=3
        )
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client'):
                client = NovaSonicClient(config=config)
                assert client.config.model_id == 'amazon.nova-2-sonic-v1:0'
                assert client.config.region == 'us-west-2'
                assert client.config.max_retries == 3
    
    def test_init_without_credentials_raises_error(self):
        """Test that initialization without credentials raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="AWS credentials not configured"):
                NovaSonicClient()
    
    def test_init_with_partial_credentials_raises_error(self):
        """Test that initialization with only access key raises ValueError."""
        with patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'test_key'}, clear=True):
            with pytest.raises(ValueError, match="AWS credentials not configured"):
                NovaSonicClient()


class TestTranscribeAudio:
    """Test transcribe_audio method."""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self):
        """Test successful audio transcription."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                # Setup mock response
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {
                        'text': 'Hello world'
                    }
                }).encode('utf-8')
                
                mock_runtime.invoke_model.return_value = mock_response
                
                # Test transcription
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                result = await client.transcribe_audio(audio_data, 'pcm')
                
                assert result == 'Hello world'
                
                # Verify API call
                mock_runtime.invoke_model.assert_called_once()
                call_args = mock_runtime.invoke_model.call_args
                assert call_args[1]['modelId'] == 'amazon.nova-sonic-v1:0'
                
                # Verify request body
                body = json.loads(call_args[1]['body'])
                assert body['inputModality'] == 'SPEECH'
                assert body['outputModality'] == 'TEXT'
                assert 'audioInput' in body
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_empty_result_raises_error(self):
        """Test that empty transcription raises RuntimeError."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {
                        'text': ''
                    }
                }).encode('utf-8')
                
                mock_runtime.invoke_model.return_value = mock_response
                
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                
                with pytest.raises(RuntimeError, match="Transcription returned empty text"):
                    await client.transcribe_audio(audio_data, 'pcm')
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_client_error(self):
        """Test handling of AWS ClientError."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                error_response = {
                    'Error': {
                        'Code': 'ValidationException',
                        'Message': 'Invalid model'
                    }
                }
                mock_runtime.invoke_model.side_effect = ClientError(
                    error_response, 'InvokeModel'
                )
                
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                
                with pytest.raises(RuntimeError, match="Nova Sonic API error"):
                    await client.transcribe_audio(audio_data, 'pcm')
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_connection_error(self):
        """Test handling of connection errors with retry."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                # All attempts fail with connection error
                mock_runtime.invoke_model.side_effect = BotoCoreError()
                
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                
                # Should fail after retries with retry_exhausted error
                with pytest.raises(RuntimeError, match="failed after 3 attempts"):
                    await client.transcribe_audio(audio_data, 'pcm')
                
                # Verify it was retried (3 attempts total)
                assert mock_runtime.invoke_model.call_count == 3


class TestSynthesizeSpeech:
    """Test synthesize_speech method."""
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self):
        """Test successful speech synthesis."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                # Create fake audio data
                fake_audio = b'fake_audio_bytes'
                audio_base64 = base64.b64encode(fake_audio).decode('utf-8')
                
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {
                        'audio': {
                            'data': audio_base64
                        }
                    }
                }).encode('utf-8')
                
                mock_runtime.invoke_model.return_value = mock_response
                
                # Test synthesis
                client = NovaSonicClient()
                result = await client.synthesize_speech(
                    'Hello world',
                    Language.ENGLISH
                )
                
                assert result == fake_audio
                
                # Verify API call
                mock_runtime.invoke_model.assert_called_once()
                call_args = mock_runtime.invoke_model.call_args
                
                # Verify request body
                body = json.loads(call_args[1]['body'])
                assert body['inputModality'] == 'TEXT'
                assert body['outputModality'] == 'SPEECH'
                assert body['textInput']['text'] == 'Hello world'
                assert body['textInput']['language'] == 'en'
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client'):
                client = NovaSonicClient()
                
                with pytest.raises(ValueError, match="Text cannot be empty"):
                    await client.synthesize_speech('', Language.ENGLISH)
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_with_custom_format(self):
        """Test speech synthesis with custom output format."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                fake_audio = b'fake_audio_bytes'
                audio_base64 = base64.b64encode(fake_audio).decode('utf-8')
                
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {
                        'audio': {
                            'data': audio_base64
                        }
                    }
                }).encode('utf-8')
                
                mock_runtime.invoke_model.return_value = mock_response
                
                client = NovaSonicClient()
                result = await client.synthesize_speech(
                    'Hello',
                    Language.ENGLISH,
                    output_format='opus'
                )
                
                assert result == fake_audio
                
                # Verify format in request
                call_args = mock_runtime.invoke_model.call_args
                body = json.loads(call_args[1]['body'])
                assert body['audioOutput']['format'] == 'OPUS'
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_no_audio_in_response(self):
        """Test handling of response without audio data."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {}
                }).encode('utf-8')
                
                mock_runtime.invoke_model.return_value = mock_response
                
                client = NovaSonicClient()
                
                with pytest.raises(RuntimeError, match="No audio data in response"):
                    await client.synthesize_speech('Hello', Language.ENGLISH)


class TestValidateModelAvailability:
    """Test validate_model_availability method."""
    
    def test_validate_model_in_list(self):
        """Test validation when model is in the available models list."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                # Mock bedrock-runtime client
                mock_runtime = Mock()
                
                # Mock bedrock client for list_foundation_models
                mock_bedrock = Mock()
                mock_bedrock.list_foundation_models.return_value = {
                    'modelSummaries': [
                        {'modelId': 'amazon.nova-sonic-v1:0'},
                        {'modelId': 'amazon.nova-2-sonic-v1:0'}
                    ]
                }
                
                # Return different mocks based on service name
                def client_factory(service_name, **kwargs):
                    if service_name == 'bedrock-runtime':
                        return mock_runtime
                    elif service_name == 'bedrock':
                        return mock_bedrock
                    return Mock()
                
                mock_boto.side_effect = client_factory
                
                client = NovaSonicClient()
                result = client.validate_model_availability()
                
                assert result is True
    
    def test_validate_model_not_in_list_but_invocation_succeeds(self):
        """Test validation when model not in list but test invocation succeeds."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_bedrock = Mock()
                
                # Model not in list
                mock_bedrock.list_foundation_models.return_value = {
                    'modelSummaries': []
                }
                
                # But test invocation succeeds
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {'text': 'test'}
                }).encode('utf-8')
                mock_runtime.invoke_model.return_value = mock_response
                
                def client_factory(service_name, **kwargs):
                    if service_name == 'bedrock-runtime':
                        return mock_runtime
                    elif service_name == 'bedrock':
                        return mock_bedrock
                    return Mock()
                
                mock_boto.side_effect = client_factory
                
                client = NovaSonicClient()
                result = client.validate_model_availability()
                
                assert result is True
    
    def test_validate_model_not_available(self):
        """Test validation when model is not available."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_bedrock = Mock()
                
                # Model not in list
                mock_bedrock.list_foundation_models.return_value = {
                    'modelSummaries': []
                }
                
                # Test invocation fails with validation error
                error_response = {
                    'Error': {
                        'Code': 'ValidationException',
                        'Message': 'Model not found'
                    }
                }
                mock_runtime.invoke_model.side_effect = ClientError(
                    error_response, 'InvokeModel'
                )
                
                def client_factory(service_name, **kwargs):
                    if service_name == 'bedrock-runtime':
                        return mock_runtime
                    elif service_name == 'bedrock':
                        return mock_bedrock
                    return Mock()
                
                mock_boto.side_effect = client_factory
                
                client = NovaSonicClient()
                result = client.validate_model_availability()
                
                assert result is False


class TestHealthCheck:
    """Test health_check method."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {'text': 'health check'}
                }).encode('utf-8')
                
                mock_runtime.invoke_model.return_value = mock_response
                
                client = NovaSonicClient()
                result = await client.health_check()
                
                assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check when service is unavailable."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                mock_runtime.invoke_model.side_effect = Exception("Service unavailable")
                
                client = NovaSonicClient()
                result = await client.health_check()
                
                assert result is False


class TestGetters:
    """Test getter methods."""
    
    def test_get_model_id(self):
        """Test get_model_id returns correct model ID."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client'):
                client = NovaSonicClient(model_id='amazon.nova-2-sonic-v1:0')
                assert client.get_model_id() == 'amazon.nova-2-sonic-v1:0'
    
    def test_get_region(self):
        """Test get_region returns correct region."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client'):
                client = NovaSonicClient(region='us-west-2')
                assert client.get_region() == 'us-west-2'


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_retry_on_timeout(self):
        """Test that transcribe_audio retries on timeout errors."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                # First call fails with timeout, second succeeds
                error_response = {
                    'Error': {
                        'Code': 'RequestTimeout',
                        'Message': 'Request timed out'
                    }
                }
                
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {
                        'text': 'Hello world'
                    }
                }).encode('utf-8')
                
                mock_runtime.invoke_model.side_effect = [
                    ClientError(error_response, 'InvokeModel'),
                    mock_response
                ]
                
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                
                # Should succeed after retry
                result = await client.transcribe_audio(audio_data, 'pcm')
                assert result == 'Hello world'
                
                # Verify it was called twice
                assert mock_runtime.invoke_model.call_count == 2
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_retry_exhausted(self):
        """Test that transcribe_audio fails after max retries."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                # All calls fail with timeout
                error_response = {
                    'Error': {
                        'Code': 'RequestTimeout',
                        'Message': 'Request timed out'
                    }
                }
                
                mock_runtime.invoke_model.side_effect = ClientError(
                    error_response, 'InvokeModel'
                )
                
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                
                # Should fail after 3 attempts (1 initial + 2 retries)
                with pytest.raises(RuntimeError, match="failed after 3 attempts"):
                    await client.transcribe_audio(audio_data, 'pcm')
                
                # Verify it was called 3 times
                assert mock_runtime.invoke_model.call_count == 3
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_retry_on_connection_error(self):
        """Test that transcribe_audio retries on connection errors."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                # First call fails with connection error, second succeeds
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {
                        'text': 'Hello world'
                    }
                }).encode('utf-8')
                
                mock_runtime.invoke_model.side_effect = [
                    BotoCoreError(),
                    mock_response
                ]
                
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                
                # Should succeed after retry
                result = await client.transcribe_audio(audio_data, 'pcm')
                assert result == 'Hello world'
                
                # Verify it was called twice
                assert mock_runtime.invoke_model.call_count == 2
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_no_retry_on_validation_error(self):
        """Test that transcribe_audio does not retry on validation errors."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                # Validation error should not be retried
                error_response = {
                    'Error': {
                        'Code': 'ValidationException',
                        'Message': 'Invalid input'
                    }
                }
                
                mock_runtime.invoke_model.side_effect = ClientError(
                    error_response, 'InvokeModel'
                )
                
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                
                # Should fail immediately without retry
                with pytest.raises(RuntimeError, match="Nova Sonic API error"):
                    await client.transcribe_audio(audio_data, 'pcm')
                
                # Verify it was only called once (no retry)
                assert mock_runtime.invoke_model.call_count == 1
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_retry_on_service_unavailable(self):
        """Test that synthesize_speech retries on ServiceUnavailable errors."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                # First call fails with ServiceUnavailable, second succeeds
                error_response = {
                    'Error': {
                        'Code': 'ServiceUnavailable',
                        'Message': 'Service temporarily unavailable'
                    }
                }
                
                fake_audio = b'fake_audio_bytes'
                audio_base64 = base64.b64encode(fake_audio).decode('utf-8')
                
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {
                        'audio': {
                            'data': audio_base64
                        }
                    }
                }).encode('utf-8')
                
                mock_runtime.invoke_model.side_effect = [
                    ClientError(error_response, 'InvokeModel'),
                    mock_response
                ]
                
                client = NovaSonicClient()
                
                # Should succeed after retry
                result = await client.synthesize_speech('Hello', Language.ENGLISH)
                assert result == fake_audio
                
                # Verify it was called twice
                assert mock_runtime.invoke_model.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_with_session_id_logging(self):
        """Test that retry logic logs session_id when provided."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                # First call fails, second succeeds
                error_response = {
                    'Error': {
                        'Code': 'RequestTimeout',
                        'Message': 'Request timed out'
                    }
                }
                
                mock_response = {
                    'body': Mock()
                }
                mock_response['body'].read.return_value = json.dumps({
                    'output': {
                        'text': 'Hello world'
                    }
                }).encode('utf-8')
                
                mock_runtime.invoke_model.side_effect = [
                    ClientError(error_response, 'InvokeModel'),
                    mock_response
                ]
                
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                
                # Call with session_id
                with patch('mock_interview_coach.voice_interface.nova_sonic_client.logger') as mock_logger:
                    result = await client.transcribe_audio(
                        audio_data, 
                        'pcm',
                        session_id='test-session-123'
                    )
                    
                    assert result == 'Hello world'
                    
                    # Verify logger was called with session_id in context
                    # Check that at least one log call included session_id
                    log_calls = mock_logger.info.call_args_list + mock_logger.error.call_args_list
                    session_logged = any(
                        'extra' in call.kwargs and 
                        call.kwargs.get('extra', {}).get('session_id') == 'test-session-123'
                        for call in log_calls
                    )
                    assert session_logged, "session_id should be logged in retry context"
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that exponential backoff uses correct delays (1s, 2s)."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            with patch('boto3.client') as mock_boto:
                mock_runtime = Mock()
                mock_boto.return_value = mock_runtime
                
                # All calls fail to test all retry delays
                error_response = {
                    'Error': {
                        'Code': 'RequestTimeout',
                        'Message': 'Request timed out'
                    }
                }
                
                mock_runtime.invoke_model.side_effect = ClientError(
                    error_response, 'InvokeModel'
                )
                
                client = NovaSonicClient()
                audio_data = b'fake_audio_data'
                
                # Mock asyncio.sleep to verify delays
                with patch('asyncio.sleep') as mock_sleep:
                    try:
                        await client.transcribe_audio(audio_data, 'pcm')
                    except RuntimeError:
                        pass  # Expected to fail after retries
                    
                    # Verify sleep was called with correct delays: 1s, 2s
                    assert mock_sleep.call_count == 2
                    sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
                    assert sleep_calls == [1, 2], f"Expected delays [1, 2], got {sleep_calls}"
