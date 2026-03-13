"""Mock audio generator for development mode.

This module provides mock audio responses for common phrases when ENABLE_DEV_MODE
is set to true, allowing local development without requiring AWS credentials.

Requirements: 12.5
"""

import os
import logging
import hashlib
from typing import Dict, Optional
from pathlib import Path

from mock_interview_coach.models import Language

logger = logging.getLogger(__name__)


class MockAudioGenerator:
    """Generate mock audio for development mode.
    
    This class provides pre-generated mock audio files for common phrases,
    allowing development and testing without calling the Nova Sonic API.
    """
    
    def __init__(self, mock_audio_dir: Optional[str] = None):
        """Initialize the mock audio generator.
        
        Args:
            mock_audio_dir: Directory containing mock audio files.
                           Defaults to mock_audio/ in the voice_interface directory.
        """
        if mock_audio_dir:
            self.mock_audio_dir = Path(mock_audio_dir)
        else:
            # Default to mock_audio directory in the same directory as this file
            self.mock_audio_dir = Path(__file__).parent / "mock_audio"
        
        # Create directory if it doesn't exist
        self.mock_audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Common phrases for mock audio
        self.common_phrases = {
            "hello": "Hello! Welcome to the mock interview coach.",
            "question": "Tell me about a time when you faced a challenging problem.",
            "feedback": "Great answer! You demonstrated strong problem-solving skills.",
            "goodbye": "Thank you for practicing with us today. Good luck!",
            "error": "I'm sorry, I didn't catch that. Could you please repeat?",
            "thinking": "Let me think about that for a moment...",
            "next": "Let's move on to the next question.",
            "complete": "You've completed the interview. Well done!",
        }
        
        # Initialize mock audio files
        self._initialize_mock_audio()
    
    def _initialize_mock_audio(self):
        """Initialize mock audio files for common phrases.
        
        Creates simple mock audio files (silent MP3s with metadata) if they don't exist.
        """
        for phrase_key, phrase_text in self.common_phrases.items():
            audio_file = self.mock_audio_dir / f"{phrase_key}.mp3"
            
            if not audio_file.exists():
                # Create a minimal valid MP3 file (silent audio)
                # This is a minimal MP3 header + frame for ~1 second of silence
                mock_audio_data = self._generate_silent_mp3(duration_ms=1000)
                
                with open(audio_file, 'wb') as f:
                    f.write(mock_audio_data)
                
                logger.debug(f"Created mock audio file: {audio_file}")
    
    def _generate_silent_mp3(self, duration_ms: int = 1000) -> bytes:
        """Generate a minimal silent MP3 file.
        
        Args:
            duration_ms: Duration in milliseconds
            
        Returns:
            Bytes representing a minimal valid MP3 file
        """
        # Minimal MP3 header (ID3v2.3)
        id3_header = b'ID3\x03\x00\x00\x00\x00\x00\x00'
        
        # MP3 frame header for 44.1kHz, 128kbps, mono
        # This is a simplified frame - in production you'd use a proper audio library
        mp3_frame = b'\xff\xfb\x90\x00' + b'\x00' * 417  # ~1 frame (~26ms)
        
        # Calculate number of frames needed for desired duration
        frames_needed = max(1, duration_ms // 26)
        
        # Combine header and frames
        return id3_header + (mp3_frame * frames_needed)
    
    def get_mock_transcription(self, audio_data: bytes) -> str:
        """Get a mock transcription for audio data.
        
        In dev mode, we return a generic transcription based on audio length.
        
        Args:
            audio_data: Audio data bytes (ignored in mock mode)
            
        Returns:
            Mock transcription text
        """
        # Generate a deterministic but varied response based on audio length
        audio_hash = hashlib.md5(audio_data).hexdigest()[:8]
        
        mock_responses = [
            "This is a mock transcription for development mode.",
            "I have experience with Python, JavaScript, and cloud technologies.",
            "In my previous role, I led a team of five developers.",
            "I'm passionate about solving complex technical challenges.",
            "My approach involves breaking down problems into smaller components.",
        ]
        
        # Use hash to select a response deterministically
        index = int(audio_hash, 16) % len(mock_responses)
        response = mock_responses[index]
        
        logger.debug(f"Mock transcription generated: {response[:50]}...")
        return response
    
    def get_mock_audio(self, text: str, language: Language) -> bytes:
        """Get mock audio for text synthesis.
        
        Args:
            text: Text to synthesize (used to select appropriate mock audio)
            language: Language for synthesis (currently ignored in mock mode)
            
        Returns:
            Mock audio data as bytes
        """
        # Normalize text for matching
        text_lower = text.lower().strip()
        
        # Try to match common phrases
        for phrase_key, phrase_text in self.common_phrases.items():
            if phrase_key in text_lower or phrase_text.lower() in text_lower:
                audio_file = self.mock_audio_dir / f"{phrase_key}.mp3"
                
                if audio_file.exists():
                    with open(audio_file, 'rb') as f:
                        audio_data = f.read()
                    
                    logger.debug(f"Using mock audio file: {phrase_key}.mp3")
                    return audio_data
        
        # If no match, generate a generic mock audio based on text length
        # Longer text = longer audio
        duration_ms = min(5000, max(1000, len(text) * 50))  # 50ms per character, max 5s
        mock_audio = self._generate_silent_mp3(duration_ms)
        
        logger.debug(f"Generated generic mock audio ({duration_ms}ms) for text: {text[:50]}...")
        return mock_audio
    
    def is_dev_mode_enabled(self) -> bool:
        """Check if development mode is enabled.
        
        Returns:
            True if ENABLE_DEV_MODE environment variable is set to true
        """
        return os.getenv("ENABLE_DEV_MODE", "false").lower() == "true"
    
    def get_available_mock_files(self) -> Dict[str, str]:
        """Get list of available mock audio files.
        
        Returns:
            Dictionary mapping phrase keys to file paths
        """
        available = {}
        
        for phrase_key in self.common_phrases.keys():
            audio_file = self.mock_audio_dir / f"{phrase_key}.mp3"
            if audio_file.exists():
                available[phrase_key] = str(audio_file)
        
        return available

