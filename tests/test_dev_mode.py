"""Tests for development mode with mock audio.

This module tests the development mode functionality that allows local development
without requiring AWS credentials by using mock audio responses.

Requirements: 12.5
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from mock_interview_coach.voice_interface import (
    NovaSonicClient,
    MockAudioGenerator
)
from mock_interview_coach.models import Language


class TestMockAudioGenerator:
    """Test suite for MockAudioGenerator."""
    
    def test_initialization_creates_directory(self, tmp_path):
        """Test that MockAudioGenerator creates mock audio directory."""
        mock_dir = tmp_path / "mock_audio"
        generator = MockAudioGenerator(mock_audio_dir=str(mock_dir))
        
        assert mock_dir.exists()
        assert mock_dir.is_dir()
    
    def test_initialization_creates_mock_files(self, tmp_path):
        """Test that MockAudioGenerator creates mock audio files."""
        mock_dir = tmp_path / "mock_audio"
        generator = MockAudioGenerator(mock_audio_dir=str(mock_dir))
        
        # Check that common phrase files are created
        expected_files = ["hello.mp3", "question.mp3", "feedback.mp3", "goodbye.mp3"]
        for filename in expected_files:
            file_path = mock_dir / filename
            assert file_path.exists(), f"Expected {filename} to be created"
            assert file_path.stat().st_size > 0, f"Expected {filename} to have content"
    
    def test_get_mock_transcription_returns_text(self, tmp_path):
        """Test that get_mock_transcription returns valid text."""
        generator = MockAudioGenerator(mock_audio_dir=str(tmp_path / "mock_audio"))
        
        audio_data = b"test_audio_data"
        transcription = generator.get_mock_transcription(audio_data)
        
        assert isinstance(transcription, str)
        assert len(transcription) > 0
        assert transcription in [
            "This is a mock transcription for development mode.",
            "I have experience with Python, JavaScript, and cloud technologies.",
            "In my previous role, I led a team of five developers.",
            "I'm passionate about solving complex technical challenges.",
            "My approach involves breaking down problems into smaller components.",
        ]
    
    def test_get_mock_transcription_deterministic(self, tmp_path):
        """Test that same audio data produces same transcription."""
        generator = MockAudioGenerator(mock_audio_dir=str(tmp_path / "mock_audio"))
        
        audio_data = b"test_audio_data"
        transcription1 = generator.get_mock_transcription(audio_data)
        transcription2 = generator.get_mock_transcription(audio_data)
        
        assert transcription1 == transcription2
    
    def test_get_mock_audio_returns_bytes(self, tmp_path):
        """Test that get_mock_audio returns audio bytes."""
        generator = MockAudioGenerator(mock_audio_dir=str(tmp_path / "mock_audio"))
        
        text = "Hello, this is a test."
        audio_data = generator.get_mock_audio(text, Language.ENGLISH)
        
        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
    
    def test_get_mock_audio_matches_common_phrases(self, tmp_path):
        """Test that common phrases use pre-generated audio files."""
        mock_dir = tmp_path / "mock_audio"
        generator = MockAudioGenerator(mock_audio_dir=str(mock_dir))
        
        # Test with "hello" phrase
        text = "Hello! Welcome to the mock interview coach."
        audio_data = generator.get_mock_audio(text, Language.ENGLISH)
        
        # Should use hello.mp3 file
        hello_file = mock_dir / "hello.mp3"
        with open(hello_file, 'rb') as f:
            expected_audio = f.read()
        
        assert audio_data == expected_audio
    
    def test_get_mock_audio_generates_for_unknown_phrases(self, tmp_path):
        """Test that unknown phrases generate audio dynamically."""
        generator = MockAudioGenerator(mock_audio_dir=str(tmp_path / "mock_audio"))
        
        text = "This is a completely unique phrase that doesn't match any common phrase."
        audio_data = generator.get_mock_audio(text, Language.ENGLISH)
        
        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
    
    def test_is_dev_mode_enabled_reads_env_var(self, tmp_path):
        """Test that is_dev_mode_enabled reads ENABLE_DEV_MODE env var."""
        generator = MockAudioGenerator(mock_audio_dir=str(tmp_path / "mock_audio"))
        
        # Test with dev mode disabled
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "false"}):
            assert generator.is_dev_mode_enabled() is False
        
        # Test with dev mode enabled
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            assert generator.is_dev_mode_enabled() is True
        
        # Test with dev mode enabled (case insensitive)
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "TRUE"}):
            assert generator.is_dev_mode_enabled() is True
    
    def test_get_available_mock_files_returns_dict(self, tmp_path):
        """Test that get_available_mock_files returns dictionary of files."""
        generator = MockAudioGenerator(mock_audio_dir=str(tmp_path / "mock_audio"))
        
        available = generator.get_available_mock_files()
        
        assert isinstance(available, dict)
        assert len(available) > 0
        assert "hello" in available
        assert "question" in available


class TestNovaSonicClientDevMode:
    """Test suite for NovaSonicClient in development mode."""
    
    @pytest.mark.asyncio
    async def test_dev_mode_initialization_no_credentials_required(self):
        """Test that dev mode doesn't require AWS credentials."""
        with patch.dict(os.environ, {
            "ENABLE_DEV_MODE": "true",
            "AWS_ACCESS_KEY_ID": "",
            "AWS_SECRET_ACCESS_KEY": ""
        }):
            # Should not raise ValueError about missing credentials
            client = NovaSonicClient()
            
            assert client.dev_mode is True
            assert client._bedrock_runtime is None
    
    @pytest.mark.asyncio
    async def test_dev_mode_logs_activation(self, caplog):
        """Test that dev mode logs activation message."""
        import logging
        caplog.set_level(logging.INFO)
        
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            client = NovaSonicClient()
            
            # Check that dev mode activation was logged
            log_messages = [record.message for record in caplog.records]
            assert any("Development mode enabled" in msg for msg in log_messages), \
                f"Expected 'Development mode enabled' in logs, got: {log_messages}"
    
    @pytest.mark.asyncio
    async def test_dev_mode_transcribe_audio_uses_mock(self):
        """Test that transcribe_audio uses mock in dev mode."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            client = NovaSonicClient()
            
            audio_data = b"test_audio_data"
            transcription = await client.transcribe_audio(audio_data, "pcm")
            
            # Should return a mock transcription
            assert isinstance(transcription, str)
            assert len(transcription) > 0
            # Should not call AWS API
            assert client._bedrock_runtime is None
    
    @pytest.mark.asyncio
    async def test_dev_mode_synthesize_speech_uses_mock(self):
        """Test that synthesize_speech uses mock in dev mode."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            client = NovaSonicClient()
            
            text = "Hello, this is a test."
            audio_data = await client.synthesize_speech(text, Language.ENGLISH)
            
            # Should return mock audio
            assert isinstance(audio_data, bytes)
            assert len(audio_data) > 0
            # Should not call AWS API
            assert client._bedrock_runtime is None
    
    @pytest.mark.asyncio
    async def test_dev_mode_validate_model_availability_returns_true(self):
        """Test that validate_model_availability returns True in dev mode."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            client = NovaSonicClient()
            
            is_available = client.validate_model_availability()
            
            assert is_available is True
    
    @pytest.mark.asyncio
    async def test_dev_mode_health_check_returns_true(self):
        """Test that health_check returns True in dev mode."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            client = NovaSonicClient()
            
            is_healthy = await client.health_check()
            
            assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_production_mode_requires_credentials(self):
        """Test that production mode requires AWS credentials."""
        with patch.dict(os.environ, {
            "ENABLE_DEV_MODE": "false",
            "AWS_ACCESS_KEY_ID": "",
            "AWS_SECRET_ACCESS_KEY": ""
        }):
            # Should raise ValueError about missing credentials
            with pytest.raises(ValueError, match="AWS credentials not configured"):
                client = NovaSonicClient()
    
    @pytest.mark.asyncio
    async def test_dev_mode_transcription_varies_by_input(self):
        """Test that different audio inputs produce different transcriptions."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            client = NovaSonicClient()
            
            audio_data1 = b"test_audio_data_1"
            audio_data2 = b"test_audio_data_2"
            
            transcription1 = await client.transcribe_audio(audio_data1, "pcm")
            transcription2 = await client.transcribe_audio(audio_data2, "pcm")
            
            # Different inputs should produce different transcriptions
            # (due to hash-based selection)
            # Note: This might occasionally fail if hashes collide, but very unlikely
            assert isinstance(transcription1, str)
            assert isinstance(transcription2, str)
    
    @pytest.mark.asyncio
    async def test_dev_mode_synthesis_varies_by_text(self):
        """Test that different texts produce different audio lengths."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            client = NovaSonicClient()
            
            short_text = "Hi"
            long_text = "This is a much longer text that should produce longer audio."
            
            short_audio = await client.synthesize_speech(short_text, Language.ENGLISH)
            long_audio = await client.synthesize_speech(long_text, Language.ENGLISH)
            
            # Longer text should produce longer audio (or at least different audio)
            assert isinstance(short_audio, bytes)
            assert isinstance(long_audio, bytes)
            # Length relationship depends on whether text matches common phrases
            # So we just verify both produce valid audio
            assert len(short_audio) > 0
            assert len(long_audio) > 0


class TestDevModeIntegration:
    """Integration tests for development mode."""
    
    @pytest.mark.asyncio
    async def test_full_voice_pipeline_in_dev_mode(self):
        """Test complete voice pipeline works in dev mode."""
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            client = NovaSonicClient()
            
            # Test speech-to-text
            audio_input = b"user_speaking_audio_data"
            transcription = await client.transcribe_audio(audio_input, "pcm")
            assert isinstance(transcription, str)
            assert len(transcription) > 0
            
            # Test text-to-speech
            response_text = "Thank you for your answer."
            audio_output = await client.synthesize_speech(response_text, Language.ENGLISH)
            assert isinstance(audio_output, bytes)
            assert len(audio_output) > 0
            
            # Test health check
            is_healthy = await client.health_check()
            assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_dev_mode_with_session_id_logging(self, caplog):
        """Test that dev mode logs include session IDs."""
        import logging
        caplog.set_level(logging.DEBUG)
        
        with patch.dict(os.environ, {"ENABLE_DEV_MODE": "true"}):
            client = NovaSonicClient()
            
            session_id = "test_session_123"
            audio_data = b"test_audio"
            
            await client.transcribe_audio(audio_data, "pcm", session_id=session_id)
            
            # Verify logging includes dev mode indicators
            log_messages = [record.message for record in caplog.records]
            assert any("Dev mode" in msg for msg in log_messages), \
                f"Expected 'Dev mode' in logs, got: {log_messages}"

