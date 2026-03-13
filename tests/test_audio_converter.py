"""Unit tests for AudioConverter."""

import pytest
import io
import wave
import struct

from mock_interview_coach.voice_interface import (
    AudioConverter,
    AudioFormat,
    AudioProperties
)


def create_test_wav(sample_rate=16000, duration_seconds=1, channels=1):
    """Helper function to create a valid WAV file for testing."""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Generate silence
        num_samples = int(sample_rate * duration_seconds * channels)
        audio_data = struct.pack('<' + 'h' * num_samples, *([0] * num_samples))
        wav_file.writeframes(audio_data)
    
    return buffer.getvalue()


class TestAudioConverterInitialization:
    """Test AudioConverter initialization."""
    
    def test_init_success(self):
        """Test successful initialization when pydub is available."""
        converter = AudioConverter()
        assert converter is not None


class TestValidateFormat:
    """Test validate_format method."""
    
    def test_validate_wav_format(self):
        """Test detection of WAV format."""
        converter = AudioConverter()
        wav_data = b'RIFF' + b'\x00' * 4 + b'WAVE' + b'\x00' * 100
        result = converter.validate_format(wav_data)
        assert result == AudioFormat.WAV
    
    def test_validate_mp3_format_with_id3(self):
        """Test detection of MP3 format with ID3 tag."""
        converter = AudioConverter()
        mp3_data = b'ID3' + b'\x00' * 100
        result = converter.validate_format(mp3_data)
        assert result == AudioFormat.MP3
    
    def test_validate_mp3_format_with_sync_word(self):
        """Test detection of MP3 format with sync word."""
        converter = AudioConverter()
        mp3_data = b'\xFF\xFB' + b'\x00' * 100
        result = converter.validate_format(mp3_data)
        assert result == AudioFormat.MP3
    
    def test_validate_opus_format(self):
        """Test detection of Opus format."""
        converter = AudioConverter()
        opus_data = b'OggS' + b'\x00' * 20 + b'OpusHead' + b'\x00' * 100
        result = converter.validate_format(opus_data)
        assert result == AudioFormat.OPUS
    
    def test_validate_webm_format(self):
        """Test detection of WebM format."""
        converter = AudioConverter()
        webm_data = b'\x1a\x45\xdf\xa3' + b'\x00' * 100
        result = converter.validate_format(webm_data)
        assert result == AudioFormat.WEBM
    
    def test_validate_pcm_format_fallback(self):
        """Test that unknown format defaults to PCM."""
        converter = AudioConverter()
        unknown_data = b'\x12\x34\x56\x78' + b'\x00' * 100
        result = converter.validate_format(unknown_data)
        assert result == AudioFormat.PCM
    
    def test_validate_empty_data(self):
        """Test validation of empty data."""
        converter = AudioConverter()
        result = converter.validate_format(b'')
        assert result == AudioFormat.UNKNOWN
    
    def test_validate_too_short_data(self):
        """Test validation of data that's too short."""
        converter = AudioConverter()
        result = converter.validate_format(b'\x00' * 10)
        assert result == AudioFormat.UNKNOWN


class TestConvertToPCM:
    """Test convert_to_pcm method."""
    
    def test_convert_pcm_to_pcm_returns_same(self):
        """Test that PCM to PCM conversion returns the same data."""
        converter = AudioConverter()
        pcm_data = b'\x00\x01' * 1000
        result = converter.convert_to_pcm(pcm_data, 'pcm')
        assert result == pcm_data
    
    def test_convert_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        converter = AudioConverter()
        with pytest.raises(ValueError, match="Audio data cannot be empty"):
            converter.convert_to_pcm(b'', 'wav')
    
    def test_convert_unsupported_format_raises_error(self):
        """Test that unsupported format raises ValueError."""
        converter = AudioConverter()
        with pytest.raises(ValueError, match="Unsupported source format"):
            converter.convert_to_pcm(b'\x00' * 100, 'flac')
    
    def test_convert_wav_to_pcm(self):
        """Test conversion from WAV to PCM."""
        converter = AudioConverter()
        wav_data = create_test_wav(sample_rate=16000, duration_seconds=0.1)
        result = converter.convert_to_pcm(wav_data, 'wav')
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert len(result) == 3200  # 16000 * 0.1 * 2 bytes


class TestConvertFromPCM:
    """Test convert_from_pcm method."""
    
    def test_convert_empty_pcm_raises_error(self):
        """Test that empty PCM data raises ValueError."""
        converter = AudioConverter()
        with pytest.raises(ValueError, match="PCM data cannot be empty"):
            converter.convert_from_pcm(b'', 'mp3')
    
    def test_convert_unsupported_target_format_raises_error(self):
        """Test that unsupported target format raises ValueError."""
        converter = AudioConverter()
        with pytest.raises(ValueError, match="Unsupported target format"):
            converter.convert_from_pcm(b'\x00' * 1000, 'flac')
    
    def test_convert_pcm_to_mp3(self):
        """Test conversion from PCM to MP3."""
        converter = AudioConverter()
        pcm_data = b'\x00\x01' * 1600
        result = converter.convert_from_pcm(pcm_data, 'mp3', sample_rate=16000, channels=1)
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:3] == b'ID3' or (result[0] == 0xFF and (result[1] & 0xE0) == 0xE0)
    
    def test_convert_pcm_to_wav(self):
        """Test conversion from PCM to WAV."""
        converter = AudioConverter()
        pcm_data = b'\x00\x01' * 1600
        result = converter.convert_from_pcm(pcm_data, 'wav', sample_rate=16000, channels=1)
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'RIFF'
        assert result[8:12] == b'WAVE'
    
    def test_convert_with_custom_sample_rate(self):
        """Test conversion with custom sample rate."""
        converter = AudioConverter()
        pcm_data = b'\x00\x01' * 4800
        result = converter.convert_from_pcm(pcm_data, 'wav', sample_rate=48000, channels=1)
        assert result[:4] == b'RIFF'
        assert result[8:12] == b'WAVE'


class TestGetAudioProperties:
    """Test get_audio_properties method."""
    
    def test_get_properties_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        converter = AudioConverter()
        with pytest.raises(ValueError, match="Audio data cannot be empty"):
            converter.get_audio_properties(b'')
    
    def test_get_properties_from_wav(self):
        """Test extracting properties from WAV file."""
        converter = AudioConverter()
        wav_data = create_test_wav(sample_rate=16000, duration_seconds=1, channels=1)
        result = converter.get_audio_properties(wav_data)
        assert result.sample_rate == 16000
        assert result.bit_depth == 16
        assert result.channels == 1
        assert 0.9 < result.duration_seconds < 1.1
        assert result.format == 'wav'
    
    def test_get_properties_from_pcm(self):
        """Test extracting properties from raw PCM data."""
        converter = AudioConverter()
        pcm_data = b'\x00\x01' * 16000
        result = converter.get_audio_properties(pcm_data)
        assert result.sample_rate == 16000
        assert result.bit_depth == 16
        assert result.channels == 1
        assert result.duration_seconds == 1.0
        assert result.format == 'pcm'
    
    def test_get_properties_unknown_format_raises_error(self):
        """Test that unknown format raises RuntimeError."""
        converter = AudioConverter()
        unknown_data = b'\x00' * 5
        with pytest.raises(RuntimeError, match="Cannot extract properties from unknown format"):
            converter.get_audio_properties(unknown_data)


class TestAudioPropertiesDataclass:
    """Test AudioProperties dataclass."""
    
    def test_audio_properties_creation(self):
        """Test creating AudioProperties instance."""
        props = AudioProperties(
            sample_rate=16000,
            bit_depth=16,
            channels=1,
            duration_seconds=5.5,
            format='pcm'
        )
        assert props.sample_rate == 16000
        assert props.bit_depth == 16
        assert props.channels == 1
        assert props.duration_seconds == 5.5
        assert props.format == 'pcm'


class TestAudioFormatEnum:
    """Test AudioFormat enum values."""
    
    def test_audio_format_values(self):
        """Test AudioFormat enum values."""
        assert AudioFormat.PCM.value == 'pcm'
        assert AudioFormat.OPUS.value == 'opus'
        assert AudioFormat.MP3.value == 'mp3'
        assert AudioFormat.WEBM.value == 'webm'
        assert AudioFormat.WAV.value == 'wav'
        assert AudioFormat.UNKNOWN.value == 'unknown'


class TestIntegration:
    """Integration tests for complete conversion workflows."""
    
    def test_wav_to_pcm_to_mp3_roundtrip(self):
        """Test converting WAV -> PCM -> MP3."""
        converter = AudioConverter()
        wav_data = create_test_wav(sample_rate=16000, duration_seconds=0.5)
        pcm_data = converter.convert_to_pcm(wav_data, 'wav')
        assert len(pcm_data) > 0
        mp3_data = converter.convert_from_pcm(pcm_data, 'mp3', sample_rate=16000)
        assert len(mp3_data) > 0
        assert mp3_data[:3] == b'ID3' or (mp3_data[0] == 0xFF and (mp3_data[1] & 0xE0) == 0xE0)
    
    def test_format_detection_and_properties(self):
        """Test format detection followed by property extraction."""
        converter = AudioConverter()
        wav_data = create_test_wav(sample_rate=24000, duration_seconds=2)
        detected_format = converter.validate_format(wav_data)
        assert detected_format == AudioFormat.WAV
        props = converter.get_audio_properties(wav_data)
        assert props.sample_rate == 24000
        assert 1.9 < props.duration_seconds < 2.1
        assert props.format == 'wav'
