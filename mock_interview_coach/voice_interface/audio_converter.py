"""Audio format conversion module for Nova Sonic voice integration.

This module provides audio format conversion capabilities between browser audio formats
(PCM, Opus, WebM) and Nova Sonic compatible formats (PCM, MP3, Opus).
"""

import io
import struct
import wave
from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    from pydub import AudioSegment
    from pydub.exceptions import CouldntDecodeError
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class AudioFormat(Enum):
    """Supported audio formats."""
    PCM = "pcm"
    OPUS = "opus"
    MP3 = "mp3"
    WEBM = "webm"
    WAV = "wav"
    UNKNOWN = "unknown"


@dataclass
class AudioProperties:
    """Audio properties extracted from audio data."""
    sample_rate: int
    bit_depth: int
    channels: int
    duration_seconds: float
    format: str


class AudioConverter:
    """Audio format converter using pydub with ffmpeg backend.
    
    Supports conversion between:
    - Input formats: PCM, Opus, WebM, WAV
    - Output formats: PCM, MP3, Opus
    """
    
    def __init__(self):
        """Initialize AudioConverter.

        Does not raise if pydub is unavailable — conversion methods will raise
        only if actually called without pydub present (e.g. dev mode is fine).
        """
        if not PYDUB_AVAILABLE:
            import logging
            logging.getLogger(__name__).warning(
                "pydub not available (Python 3.13+ removed audioop). "
                "Audio format conversion is disabled. "
                "Voice recording in PCM/Opus format will still work."
            )
    
    def convert_to_pcm(self, audio_data: bytes, source_format: str) -> bytes:
        """Convert audio data to PCM format.
        
        Args:
            audio_data: Raw audio data bytes
            source_format: Source format (pcm, opus, webm, mp3, wav)
        
        Returns:
            PCM audio data as bytes (16-bit, mono)
        
        Raises:
            ValueError: If source format is invalid or unsupported
            RuntimeError: If conversion fails
        """
        if not audio_data:
            raise ValueError("Audio data cannot be empty")
        
        source_format = source_format.lower()
        
        # If already PCM, validate and return
        if source_format == "pcm":
            return audio_data
        
        try:
            # Load audio using pydub
            if source_format == "wav":
                audio = AudioSegment.from_wav(io.BytesIO(audio_data))
            elif source_format == "mp3":
                audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
            elif source_format == "opus":
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="opus")
            elif source_format == "webm":
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
            else:
                raise ValueError(f"Unsupported source format: {source_format}")
            
            # Convert to mono, 16-bit PCM
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 2 bytes = 16 bits
            
            # Export as raw PCM
            return audio.raw_data
            
        except CouldntDecodeError as e:
            raise RuntimeError(f"Failed to decode audio: {e}")
        except Exception as e:
            raise RuntimeError(f"Audio conversion failed: {e}")
    
    def convert_from_pcm(
        self,
        pcm_data: bytes,
        target_format: str,
        sample_rate: int = 16000,
        channels: int = 1
    ) -> bytes:
        """Convert PCM audio data to target format.
        
        Args:
            pcm_data: Raw PCM audio data (16-bit)
            target_format: Target format (mp3, opus, wav)
            sample_rate: Sample rate in Hz (default: 16000)
            channels: Number of channels (default: 1 for mono)
        
        Returns:
            Converted audio data as bytes
        
        Raises:
            ValueError: If target format is invalid or unsupported
            RuntimeError: If conversion fails
        """
        if not pcm_data:
            raise ValueError("PCM data cannot be empty")
        
        target_format = target_format.lower()
        
        if target_format not in ["mp3", "opus", "wav"]:
            raise ValueError(
                f"Unsupported target format: {target_format}. "
                "Supported formats: mp3, opus, wav"
            )
        
        try:
            # Create AudioSegment from raw PCM data
            audio = AudioSegment(
                data=pcm_data,
                sample_width=2,  # 16-bit = 2 bytes
                frame_rate=sample_rate,
                channels=channels
            )
            
            # Export to target format
            output_buffer = io.BytesIO()
            
            if target_format == "mp3":
                audio.export(output_buffer, format="mp3", bitrate="64k")
            elif target_format == "opus":
                audio.export(output_buffer, format="opus", bitrate="48k")
            elif target_format == "wav":
                audio.export(output_buffer, format="wav")
            
            return output_buffer.getvalue()
            
        except Exception as e:
            raise RuntimeError(f"Audio conversion failed: {e}")
    
    def validate_format(self, audio_data: bytes) -> AudioFormat:
        """Detect audio format from binary data.
        
        Args:
            audio_data: Raw audio data bytes
        
        Returns:
            Detected AudioFormat enum value
        """
        if not audio_data or len(audio_data) < 12:
            return AudioFormat.UNKNOWN
        
        # Check for WAV format (RIFF header)
        if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
            return AudioFormat.WAV
        
        # Check for MP3 format (ID3 tag or sync word)
        if audio_data[:3] == b'ID3' or (audio_data[0] == 0xFF and (audio_data[1] & 0xE0) == 0xE0):
            return AudioFormat.MP3
        
        # Check for Opus format (OggS header)
        if audio_data[:4] == b'OggS':
            # Check if it contains Opus data
            if b'OpusHead' in audio_data[:100]:
                return AudioFormat.OPUS
        
        # Check for WebM format (EBML header)
        if audio_data[:4] == b'\x1a\x45\xdf\xa3':
            return AudioFormat.WEBM
        
        # If no header matches, assume raw PCM
        return AudioFormat.PCM
    
    def get_audio_properties(self, audio_data: bytes) -> AudioProperties:
        """Extract audio properties from audio data.
        
        Args:
            audio_data: Raw audio data bytes
        
        Returns:
            AudioProperties with sample rate, bit depth, channels, duration, format
        
        Raises:
            RuntimeError: If properties cannot be extracted
        """
        if not audio_data:
            raise ValueError("Audio data cannot be empty")
        
        # Detect format
        audio_format = self.validate_format(audio_data)
        
        try:
            # Try to load with pydub
            if audio_format == AudioFormat.WAV:
                audio = AudioSegment.from_wav(io.BytesIO(audio_data))
            elif audio_format == AudioFormat.MP3:
                audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
            elif audio_format == AudioFormat.OPUS:
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="opus")
            elif audio_format == AudioFormat.WEBM:
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
            elif audio_format == AudioFormat.PCM:
                # For raw PCM, we need to make assumptions
                # Assume 16-bit, mono, 16kHz (common for voice)
                return AudioProperties(
                    sample_rate=16000,
                    bit_depth=16,
                    channels=1,
                    duration_seconds=len(audio_data) / (16000 * 2 * 1),  # bytes / (rate * bytes_per_sample * channels)
                    format="pcm"
                )
            else:
                raise RuntimeError(f"Cannot extract properties from unknown format")
            
            # Extract properties from AudioSegment
            return AudioProperties(
                sample_rate=audio.frame_rate,
                bit_depth=audio.sample_width * 8,  # Convert bytes to bits
                channels=audio.channels,
                duration_seconds=len(audio) / 1000.0,  # pydub uses milliseconds
                format=audio_format.value
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract audio properties: {e}")
