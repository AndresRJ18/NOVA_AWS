"""Integration tests for NovaSonicClient with AWS Bedrock.

These tests require valid AWS credentials and will make actual API calls.
They are skipped if credentials are not available or if running in CI.
"""

import pytest
import os
from mock_interview_coach.voice_interface import NovaSonicClient
from mock_interview_coach.models import Language


# Skip all tests in this module if AWS credentials are not available
pytestmark = pytest.mark.skipif(
    not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'),
    reason="AWS credentials not available"
)


class TestNovaSonicIntegration:
    """Integration tests with actual AWS Bedrock API."""
    
    def test_validate_model_availability_real(self):
        """Test model availability validation with real AWS API."""
        client = NovaSonicClient()
        result = client.validate_model_availability()
        
        # This should return True if the model is available in the region
        # or False if not available
        assert isinstance(result, bool)
        print(f"Model {client.get_model_id()} availability: {result}")
    
    @pytest.mark.asyncio
    async def test_health_check_real(self):
        """Test health check with real AWS API."""
        client = NovaSonicClient()
        result = await client.health_check()
        
        # This should return True if the service is healthy
        assert isinstance(result, bool)
        print(f"Nova Sonic health check: {'healthy' if result else 'unhealthy'}")
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires actual audio data and makes real API calls")
    async def test_transcribe_audio_real(self):
        """Test real audio transcription (skipped by default)."""
        # This test is skipped by default to avoid API costs
        # Uncomment and provide real audio data to test
        client = NovaSonicClient()
        
        # You would need to provide actual audio data here
        # audio_data = load_test_audio_file()
        # result = await client.transcribe_audio(audio_data, 'pcm')
        # assert isinstance(result, str)
        # assert len(result) > 0
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Makes real API calls and incurs costs")
    async def test_synthesize_speech_real(self):
        """Test real speech synthesis (skipped by default)."""
        # This test is skipped by default to avoid API costs
        # Uncomment to test with real API
        client = NovaSonicClient()
        
        # result = await client.synthesize_speech(
        #     "Hello, this is a test.",
        #     Language.ENGLISH
        # )
        # assert isinstance(result, bytes)
        # assert len(result) > 0
        pass
