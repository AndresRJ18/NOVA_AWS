# Development Mode with Mock Audio

## Overview

Development mode allows you to run the Mock Interview Coach locally without requiring AWS credentials or making actual calls to the Nova Sonic API. This is useful for:

- Local development and testing
- Frontend development without backend dependencies
- CI/CD pipelines that don't have AWS access
- Reducing API costs during development

## How It Works

When `ENABLE_DEV_MODE=true` is set, the `NovaSonicClient` uses the `MockAudioGenerator` to provide mock responses instead of calling AWS Bedrock:

- **Speech-to-Text**: Returns pre-defined mock transcriptions based on audio input hash
- **Text-to-Speech**: Returns mock audio files (silent MP3s) for common phrases or generates them dynamically
- **Health Checks**: Always return healthy status
- **Model Validation**: Always returns available

## Enabling Development Mode

### Option 1: Environment Variable

Set the `ENABLE_DEV_MODE` environment variable to `true`:

```bash
# Linux/Mac
export ENABLE_DEV_MODE=true

# Windows (PowerShell)
$env:ENABLE_DEV_MODE="true"

# Windows (CMD)
set ENABLE_DEV_MODE=true
```

### Option 2: .env File

Add to your `.env` file:

```env
ENABLE_DEV_MODE=true
```

### Option 3: Vercel Environment Variables

For Vercel deployments, set via CLI or dashboard:

```bash
vercel env add ENABLE_DEV_MODE development
# Enter value: true
```

## Mock Audio Files

The `MockAudioGenerator` creates mock audio files for common phrases in the `mock_audio/` directory:

- `hello.mp3` - Welcome message
- `question.mp3` - Interview question
- `feedback.mp3` - Feedback response
- `goodbye.mp3` - Closing message
- `error.mp3` - Error message
- `thinking.mp3` - Processing indicator
- `next.mp3` - Transition message
- `complete.mp3` - Completion message

These files are minimal valid MP3 files (silent audio) that can be played by browsers.

## Mock Transcriptions

When transcribing audio in dev mode, the system returns one of these mock transcriptions:

1. "This is a mock transcription for development mode."
2. "I have experience with Python, JavaScript, and cloud technologies."
3. "In my previous role, I led a team of five developers."
4. "I'm passionate about solving complex technical challenges."
5. "My approach involves breaking down problems into smaller components."

The selection is deterministic based on the audio data hash, so the same audio input always produces the same transcription.

## Logging

When dev mode is active, the system logs clear indicators:

```
[INFO] 🔧 Development mode enabled - using mock audio instead of Nova Sonic API
[INFO] 📁 Mock audio directory: /path/to/mock_audio
[INFO] 📝 Available mock audio files: 8
[DEBUG] 🔧 Dev mode: Generating mock transcription for 1024 bytes
[INFO] 🔧 Dev mode: Mock transcription: This is a mock transcription...
[DEBUG] 🔧 Dev mode: Generating mock audio for text: Hello, this is a test...
[INFO] 🔧 Dev mode: Generated mock audio (1234 bytes)
```

The 🔧 emoji makes it easy to identify dev mode operations in logs.

## Testing with Dev Mode

Run tests with dev mode enabled:

```bash
# Set environment variable
export ENABLE_DEV_MODE=true

# Run tests
python -m pytest tests/test_dev_mode.py -v
```

Or use pytest's environment variable injection:

```bash
ENABLE_DEV_MODE=true python -m pytest tests/test_dev_mode.py -v
```

## Health Check Endpoint

The health check endpoint (`/api/health`) returns different responses based on mode:

**Development Mode:**
```json
{
  "status": "healthy",
  "mode": "development",
  "nova_sonic": "mocked",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Production Mode:**
```json
{
  "status": "healthy",
  "mode": "production",
  "nova_sonic": "available",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Switching Between Modes

You can switch between development and production modes by changing the environment variable:

```bash
# Enable dev mode
export ENABLE_DEV_MODE=true
python app.py

# Disable dev mode (use real API)
export ENABLE_DEV_MODE=false
python app.py
```

No code changes are required - the system automatically detects the mode on startup.

## Limitations

Development mode has some limitations:

1. **No Real Audio**: Mock audio is silent MP3 files, not actual speech
2. **Fixed Transcriptions**: Only 5 pre-defined transcriptions available
3. **No Language Support**: Language parameter is ignored in mock mode
4. **No Quality Variation**: All mock audio has the same quality
5. **No Latency Simulation**: Responses are instant (no network delay)

These limitations are acceptable for development but mean dev mode should not be used for production or realistic testing.

## Production Deployment

**Important**: Always set `ENABLE_DEV_MODE=false` (or omit it) in production deployments.

Development mode should only be used for:
- Local development
- CI/CD testing
- Preview deployments (optional)

Never use dev mode in production as it will not provide real voice functionality.

## Troubleshooting

### Dev mode not activating

Check that the environment variable is set correctly:

```bash
# Linux/Mac
echo $ENABLE_DEV_MODE

# Windows (PowerShell)
echo $env:ENABLE_DEV_MODE
```

The value must be exactly `true` (case-insensitive).

### Mock audio files not found

The `MockAudioGenerator` automatically creates mock audio files on first initialization. If files are missing:

1. Check that the application has write permissions to the `mock_audio/` directory
2. Delete the `mock_audio/` directory and restart the application
3. Check logs for any errors during initialization

### Still seeing AWS credential errors

If you see AWS credential errors in dev mode:

1. Verify `ENABLE_DEV_MODE=true` is set before importing `NovaSonicClient`
2. Check that the environment variable is loaded (use `python-dotenv` or similar)
3. Restart the application after setting the variable

## Example Usage

```python
import os
from mock_interview_coach.voice_interface import NovaSonicClient
from mock_interview_coach.models import Language

# Enable dev mode
os.environ['ENABLE_DEV_MODE'] = 'true'

# Create client (no AWS credentials required)
client = NovaSonicClient()

# Transcribe audio (returns mock transcription)
audio_data = b"user_speaking_audio_data"
transcription = await client.transcribe_audio(audio_data, "pcm")
print(transcription)  # "This is a mock transcription for development mode."

# Synthesize speech (returns mock audio)
text = "Hello, welcome to the interview."
audio_output = await client.synthesize_speech(text, Language.ENGLISH)
print(f"Generated {len(audio_output)} bytes of audio")

# Health check (always returns True)
is_healthy = await client.health_check()
print(f"Service healthy: {is_healthy}")  # True
```

## Related Files

- `mock_interview_coach/voice_interface/mock_audio_generator.py` - Mock audio generation logic
- `mock_interview_coach/voice_interface/nova_sonic_client.py` - Client with dev mode support
- `tests/test_dev_mode.py` - Dev mode tests
- `api/health.py` - Health check endpoint with dev mode support
- `.env.example` - Environment variable documentation

## Requirements

This feature implements **Requirement 12.5**:

> THE System SHALL provide a mode of development local that use archivos de audio de prueba en lugar de Nova Sonic

(The system shall provide a local development mode that uses test audio files instead of Nova Sonic)

