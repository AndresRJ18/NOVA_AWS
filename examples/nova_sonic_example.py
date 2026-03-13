"""Example usage of NovaSonicClient.

This script demonstrates how to use the NovaSonicClient for speech-to-text
and text-to-speech operations with AWS Bedrock Nova Sonic.

Requirements:
- AWS credentials configured in .env file
- Access to Amazon Nova Sonic models in AWS Bedrock
"""

import asyncio
import os
from pathlib import Path

# Add parent directory to path to import from mock_interview_coach
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mock_interview_coach.voice_interface import NovaSonicClient, NovaSonicConfig
from mock_interview_coach.models import Language


async def main():
    """Main example function."""
    print("=" * 60)
    print("Nova Sonic Client Example")
    print("=" * 60)
    
    # Initialize client with default configuration
    print("\n1. Initializing Nova Sonic Client...")
    try:
        client = NovaSonicClient()
        print(f"   ✓ Client initialized")
        print(f"   Model: {client.get_model_id()}")
        print(f"   Region: {client.get_region()}")
    except ValueError as e:
        print(f"   ✗ Failed to initialize client: {e}")
        print("\n   Please ensure AWS credentials are configured in .env file:")
        print("   - AWS_ACCESS_KEY_ID")
        print("   - AWS_SECRET_ACCESS_KEY")
        print("   - AWS_REGION")
        return
    
    # Validate model availability
    print("\n2. Validating model availability...")
    is_available = client.validate_model_availability()
    if is_available:
        print(f"   ✓ Model {client.get_model_id()} is available")
    else:
        print(f"   ✗ Model {client.get_model_id()} is not available in {client.get_region()}")
        print("   Please check:")
        print("   - Model ID is correct")
        print("   - Model is available in your AWS region")
        print("   - Your AWS account has access to the model")
        return
    
    # Health check
    print("\n3. Performing health check...")
    is_healthy = await client.health_check()
    if is_healthy:
        print("   ✓ Nova Sonic service is healthy")
    else:
        print("   ✗ Nova Sonic service is not responding")
        return
    
    # Text-to-Speech example
    print("\n4. Text-to-Speech Example")
    print("   Converting text to speech...")
    
    test_texts = [
        ("Hello, welcome to the Mock Interview Coach!", Language.ENGLISH),
        ("¡Hola! Bienvenido al entrenador de entrevistas.", Language.SPANISH)
    ]
    
    for text, language in test_texts:
        try:
            print(f"\n   Text ({language.value}): {text}")
            audio_data = await client.synthesize_speech(text, language)
            print(f"   ✓ Generated {len(audio_data)} bytes of audio")
            
            # Optionally save to file
            output_file = f"output_{language.value}.mp3"
            with open(output_file, 'wb') as f:
                f.write(audio_data)
            print(f"   ✓ Saved to {output_file}")
            
        except Exception as e:
            print(f"   ✗ Failed: {e}")
    
    # Speech-to-Text example (requires audio file)
    print("\n5. Speech-to-Text Example")
    print("   Note: This requires an audio file to transcribe")
    print("   Skipping for this demo (no audio file provided)")
    
    # Example of how to use transcribe_audio:
    # try:
    #     with open('sample_audio.pcm', 'rb') as f:
    #         audio_data = f.read()
    #     
    #     transcription = await client.transcribe_audio(audio_data, 'pcm')
    #     print(f"   Transcription: {transcription}")
    # except Exception as e:
    #     print(f"   Failed: {e}")
    
    # Using custom configuration
    print("\n6. Custom Configuration Example")
    custom_config = NovaSonicConfig(
        model_id="amazon.nova-2-sonic-v1:0",  # Using Nova 2
        region="us-east-1",
        max_retries=3,
        output_format="opus"
    )
    
    try:
        custom_client = NovaSonicClient(config=custom_config)
        print(f"   ✓ Custom client created")
        print(f"   Model: {custom_client.get_model_id()}")
        print(f"   Max retries: {custom_client.config.max_retries}")
        print(f"   Output format: {custom_client.config.output_format}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
