# Voice Interface Module

This module provides voice input/output capabilities for the Mock Interview Coach system using Amazon Nova Sonic on AWS Bedrock.

## Components

### NovaSonicClient

The `NovaSonicClient` class provides a high-level interface for interacting with Amazon Nova Sonic models on AWS Bedrock.

#### Features

- **Speech-to-Text (STT)**: Transcribe audio to text
- **Text-to-Speech (TTS)**: Synthesize speech from text
- **Model Validation**: Check if Nova Sonic models are available
- **Health Monitoring**: Verify service availability
- **Multi-Model Support**: Works with both `amazon.nova-sonic-v1:0` and `amazon.nova-2-sonic-v1:0`
- **Configurable**: Customize region, retries, timeouts, and output formats

#### Quick Start

```python
from mock_interview_coach.voice_interface import NovaSonicClient
from mock_interview_coach.models import Language

# Initialize client
client = NovaSonicClient()

# Validate model availability
if client.validate_model_availability():
    print("Model is available!")

# Text-to-Speech
audio_data = await client.synthesize_speech(
    "Hello, welcome to the interview!",
    Language.ENGLISH
)

# Speech-to-Text
transcription = await client.transcribe_audio(
    audio_data,
    audio_format="pcm"
)
```

#### Configuration

The client can be configured via environment variables or programmatically:

**Environment Variables:**

```bash
# Required
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Optional
NOVA_SONIC_MODEL_ID=amazon.nova-sonic-v1:0
NOVA_SONIC_MAX_RETRIES=2
NOVA_SONIC_TIMEOUT=30
NOVA_SONIC_OUTPUT_FORMAT=mp3
```

**Programmatic Configuration:**

```python
from mock_interview_coach.voice_interface import NovaSonicClient, NovaSonicConfig

# Using constructor parameters
client = NovaSonicClient(
    model_id="amazon.nova-2-sonic-v1:0",
    region="us-west-2"
)

# Using config object
config = NovaSonicConfig(
    model_id="amazon.nova-2-sonic-v1:0",
    region="us-west-2",
    max_retries=3,
    timeout_seconds=30,
    output_format="opus"
)
client = NovaSonicClient(config=config)
```

#### API Reference

##### `__init__(model_id=None, region=None, config=None)`

Initialize the Nova Sonic client.

**Parameters:**
- `model_id` (str, optional): Nova Sonic model ID
- `region` (str, optional): AWS region
- `config` (NovaSonicConfig, optional): Complete configuration object

**Raises:**
- `ValueError`: If AWS credentials are not configured

##### `async transcribe_audio(audio_data, audio_format="pcm")`

Transcribe audio to text.

**Parameters:**
- `audio_data` (bytes): Raw audio data
- `audio_format` (str): Audio format (pcm, opus, mp3)

**Returns:**
- `str`: Transcribed text

**Raises:**
- `RuntimeError`: If transcription fails or returns empty text

##### `async synthesize_speech(text, language, output_format=None)`

Synthesize speech from text.

**Parameters:**
- `text` (str): Text to synthesize
- `language` (Language): Language for speech synthesis
- `output_format` (str, optional): Audio output format (mp3, opus)

**Returns:**
- `bytes`: Audio data

**Raises:**
- `ValueError`: If text is empty
- `RuntimeError`: If synthesis fails

##### `validate_model_availability()`

Validate that the configured Nova Sonic model is available.

**Returns:**
- `bool`: True if model is available, False otherwise

##### `async health_check()`

Check if Nova Sonic service is healthy and accessible.

**Returns:**
- `bool`: True if service is healthy, False otherwise

##### `get_model_id()`

Get the currently configured model ID.

**Returns:**
- `str`: Model ID

##### `get_region()`

Get the currently configured AWS region.

**Returns:**
- `str`: AWS region

#### Error Handling

The client uses `VoiceErrorCode` enum for specific error types:

```python
from mock_interview_coach.voice_interface import VoiceErrorCode

# Error codes
VoiceErrorCode.NOVA_SONIC_UNAVAILABLE  # Service unavailable
VoiceErrorCode.NOVA_SONIC_TIMEOUT      # Request timeout
VoiceErrorCode.NOVA_SONIC_ERROR        # API error
VoiceErrorCode.TRANSCRIPTION_EMPTY     # Empty transcription
VoiceErrorCode.MODEL_NOT_AVAILABLE     # Model not available
VoiceErrorCode.INVALID_CONFIGURATION   # Invalid config
VoiceErrorCode.MISSING_CREDENTIALS     # Missing AWS credentials
```

Errors are raised as `RuntimeError` with descriptive messages including the error code.

#### Supported Models

- `amazon.nova-sonic-v1:0` (default)
- `amazon.nova-2-sonic-v1:0`

#### Supported Audio Formats

**Input (Speech-to-Text):**
- PCM (16-bit, 16kHz+, mono)
- Opus
- MP3

**Output (Text-to-Speech):**
- MP3 (default)
- Opus

#### Best Practices

1. **Validate Model Availability**: Always check model availability on startup
2. **Health Checks**: Implement periodic health checks for monitoring
3. **Error Handling**: Catch and handle `RuntimeError` exceptions
4. **Audio Format**: Use PCM for input, MP3 for output for best compatibility
5. **Credentials**: Store AWS credentials securely in environment variables
6. **Retries**: Configure appropriate retry counts for your use case

#### Examples

See `examples/nova_sonic_example.py` for complete usage examples.

#### Testing

Run unit tests:
```bash
pytest tests/test_nova_sonic_client.py -v
```

Run integration tests (requires AWS credentials):
```bash
pytest tests/test_nova_sonic_integration.py -v
```

## VoiceInterface

The `VoiceInterface` class provides a higher-level abstraction for voice interactions in the interview system. It uses `NovaSonicClient` internally.

See `voice_interface.py` for implementation details.

## Requirements

- Python 3.8+
- boto3 >= 1.34.0
- python-dotenv >= 1.0.0
- AWS account with Bedrock access
- Access to Amazon Nova Sonic models

## License

See project LICENSE file.
