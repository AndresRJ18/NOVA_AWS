"""Unit tests for AudioQualityValidator."""

import pytest
import struct

from mock_interview_coach.voice_interface import (
    AudioQualityValidator,
    AudioIssue,
    ValidationResult
)


def create_pcm_audio(
    duration_seconds: float = 1.0,
    sample_rate: int = 16000,
    amplitude: float = 0.5,
    clipping_percentage: float = 0.0
) -> bytes:
    """Helper function to create PCM audio data for testing.
    
    Args:
        duration_seconds: Duration of audio in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude as fraction of max (0.0 to 1.0)
        clipping_percentage: Percentage of samples to set at max amplitude (0.0 to 1.0)
    
    Returns:
        PCM audio data as bytes (16-bit signed little-endian)
    """
    num_samples = int(sample_rate * duration_seconds)
    max_amplitude = 32767
    
    samples = []
    num_clipped = int(num_samples * clipping_percentage)
    
    for i in range(num_samples):
        if i < num_clipped:
            # Create clipped samples
            sample = max_amplitude if i % 2 == 0 else -max_amplitude
        else:
            # Create normal samples with specified amplitude
            sample = int(max_amplitude * amplitude * (1 if i % 2 == 0 else -1))
        samples.append(sample)
    
    # Pack as signed 16-bit little-endian
    return struct.pack(f'<{num_samples}h', *samples)


def create_silent_audio(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Create silent PCM audio (all zeros)."""
    num_samples = int(sample_rate * duration_seconds)
    return struct.pack(f'<{num_samples}h', *([0] * num_samples))


class TestAudioQualityValidatorInitialization:
    """Test AudioQualityValidator initialization."""
    
    def test_init_success(self):
        """Test successful initialization."""
        validator = AudioQualityValidator()
        assert validator is not None
        assert validator.SILENCE_THRESHOLD == 0.05
        assert validator.SILENCE_PERCENTAGE_THRESHOLD == 0.95
        assert validator.CLIPPING_PERCENTAGE_THRESHOLD == 0.01
        assert validator.MIN_DURATION_SECONDS == 1.0


class TestValidateEmptyAndCorruptedAudio:
    """Test validation of empty and corrupted audio."""
    
    def test_validate_empty_audio(self):
        """Test validation of empty audio data."""
        validator = AudioQualityValidator()
        result = validator.validate(b'')
        
        assert result.is_valid is False
        assert AudioIssue.CORRUPTED in result.issues
        assert len(result.suggestions) > 0
        assert "empty" in result.suggestions[0].lower()
    
    def test_validate_corrupted_audio(self):
        """Test validation of corrupted audio data."""
        validator = AudioQualityValidator()
        # Create data that can't be parsed as PCM
        corrupted_data = b'\xFF' * 5  # Odd number of bytes
        result = validator.validate(corrupted_data)
        
        assert result.is_valid is False
        assert AudioIssue.CORRUPTED in result.issues or AudioIssue.TOO_SHORT in result.issues


class TestValidateDuration:
    """Test validation of audio duration."""
    
    def test_validate_too_short_audio(self):
        """Test validation of audio shorter than 1 second."""
        validator = AudioQualityValidator()
        short_audio = create_pcm_audio(duration_seconds=0.5, amplitude=0.5)
        result = validator.validate(short_audio)
        
        assert result.is_valid is False
        assert AudioIssue.TOO_SHORT in result.issues
        assert any("too short" in s.lower() for s in result.suggestions)
        assert any("0.5" in s for s in result.suggestions)
    
    def test_validate_minimum_duration_audio(self):
        """Test validation of audio exactly 1 second."""
        validator = AudioQualityValidator()
        audio = create_pcm_audio(duration_seconds=1.0, amplitude=0.5)
        result = validator.validate(audio)
        
        # Should pass duration check (but may fail other checks)
        assert AudioIssue.TOO_SHORT not in result.issues
    
    def test_validate_long_audio(self):
        """Test validation of audio longer than 1 second."""
        validator = AudioQualityValidator()
        long_audio = create_pcm_audio(duration_seconds=5.0, amplitude=0.5)
        result = validator.validate(long_audio)
        
        assert AudioIssue.TOO_SHORT not in result.issues


class TestValidateSilence:
    """Test validation of silent audio."""
    
    def test_validate_completely_silent_audio(self):
        """Test validation of completely silent audio (all zeros)."""
        validator = AudioQualityValidator()
        silent_audio = create_silent_audio(duration_seconds=1.0)
        result = validator.validate(silent_audio)
        
        assert result.is_valid is False
        assert AudioIssue.SILENT in result.issues
        assert any("quiet" in s.lower() or "silent" in s.lower() for s in result.suggestions)
        assert any("microphone" in s.lower() for s in result.suggestions)
    
    def test_validate_very_quiet_audio(self):
        """Test validation of very quiet audio (below 5% amplitude)."""
        validator = AudioQualityValidator()
        quiet_audio = create_pcm_audio(duration_seconds=1.0, amplitude=0.02)
        result = validator.validate(quiet_audio)
        
        assert result.is_valid is False
        assert AudioIssue.SILENT in result.issues
    
    def test_validate_normal_volume_audio(self):
        """Test validation of normal volume audio."""
        validator = AudioQualityValidator()
        normal_audio = create_pcm_audio(duration_seconds=1.0, amplitude=0.5)
        result = validator.validate(normal_audio)
        
        assert AudioIssue.SILENT not in result.issues
    
    def test_validate_96_percent_silent_audio(self):
        """Test validation of audio with 96% silence (above threshold)."""
        validator = AudioQualityValidator()
        # Create audio with 96% silent samples
        num_samples = 16000
        samples = [0] * int(num_samples * 0.96) + [10000] * int(num_samples * 0.04)
        audio_data = struct.pack(f'<{num_samples}h', *samples)
        result = validator.validate(audio_data)
        
        assert result.is_valid is False
        assert AudioIssue.SILENT in result.issues
    
    def test_validate_94_percent_silent_audio(self):
        """Test validation of audio with 94% silence (below threshold)."""
        validator = AudioQualityValidator()
        # Create audio with 94% silent samples
        num_samples = 16000
        samples = [0] * int(num_samples * 0.94) + [10000] * int(num_samples * 0.06)
        audio_data = struct.pack(f'<{num_samples}h', *samples)
        result = validator.validate(audio_data)
        
        assert AudioIssue.SILENT not in result.issues


class TestValidateClipping:
    """Test validation of clipping audio."""
    
    def test_validate_heavily_clipped_audio(self):
        """Test validation of audio with heavy clipping (>1%)."""
        validator = AudioQualityValidator()
        clipped_audio = create_pcm_audio(
            duration_seconds=1.0,
            amplitude=0.5,
            clipping_percentage=0.05  # 5% clipped
        )
        result = validator.validate(clipped_audio)
        
        assert result.is_valid is False
        assert AudioIssue.CLIPPING in result.issues
        assert any("clipping" in s.lower() or "loud" in s.lower() for s in result.suggestions)
        assert any("softer" in s.lower() or "away" in s.lower() for s in result.suggestions)
    
    def test_validate_slightly_clipped_audio(self):
        """Test validation of audio with slight clipping (exactly 1%)."""
        validator = AudioQualityValidator()
        clipped_audio = create_pcm_audio(
            duration_seconds=1.0,
            amplitude=0.5,
            clipping_percentage=0.01  # 1% clipped
        )
        result = validator.validate(clipped_audio)
        
        # At exactly 1%, it should not trigger (threshold is >1%)
        assert AudioIssue.CLIPPING not in result.issues
    
    def test_validate_just_over_clipping_threshold(self):
        """Test validation of audio just over clipping threshold."""
        validator = AudioQualityValidator()
        clipped_audio = create_pcm_audio(
            duration_seconds=1.0,
            amplitude=0.5,
            clipping_percentage=0.011  # 1.1% clipped
        )
        result = validator.validate(clipped_audio)
        
        assert result.is_valid is False
        assert AudioIssue.CLIPPING in result.issues
    
    def test_validate_no_clipping_audio(self):
        """Test validation of audio with no clipping."""
        validator = AudioQualityValidator()
        normal_audio = create_pcm_audio(
            duration_seconds=1.0,
            amplitude=0.5,
            clipping_percentage=0.0
        )
        result = validator.validate(normal_audio)
        
        assert AudioIssue.CLIPPING not in result.issues


class TestValidateMultipleIssues:
    """Test validation of audio with multiple issues."""
    
    def test_validate_short_and_silent_audio(self):
        """Test validation of audio that is both too short and silent."""
        validator = AudioQualityValidator()
        audio = create_silent_audio(duration_seconds=0.5)
        result = validator.validate(audio)
        
        assert result.is_valid is False
        assert AudioIssue.TOO_SHORT in result.issues
        assert AudioIssue.SILENT in result.issues
        assert len(result.suggestions) >= 2
    
    def test_validate_short_and_clipped_audio(self):
        """Test validation of audio that is both too short and clipped."""
        validator = AudioQualityValidator()
        audio = create_pcm_audio(
            duration_seconds=0.5,
            amplitude=0.5,
            clipping_percentage=0.05
        )
        result = validator.validate(audio)
        
        assert result.is_valid is False
        assert AudioIssue.TOO_SHORT in result.issues
        assert AudioIssue.CLIPPING in result.issues


class TestValidateValidAudio:
    """Test validation of valid audio."""
    
    def test_validate_perfect_audio(self):
        """Test validation of perfect quality audio."""
        validator = AudioQualityValidator()
        audio = create_pcm_audio(
            duration_seconds=2.0,
            amplitude=0.5,
            clipping_percentage=0.0
        )
        result = validator.validate(audio)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
        assert len(result.suggestions) == 0
    
    def test_validate_minimum_acceptable_audio(self):
        """Test validation of minimum acceptable audio."""
        validator = AudioQualityValidator()
        # 1 second, 94% silence (below threshold), no clipping
        num_samples = 16000
        samples = [0] * int(num_samples * 0.94) + [10000] * int(num_samples * 0.06)
        audio_data = struct.pack(f'<{num_samples}h', *samples)
        result = validator.validate(audio_data)
        
        assert result.is_valid is True
        assert len(result.issues) == 0


class TestParsePCMSamples:
    """Test _parse_pcm_samples internal method."""
    
    def test_parse_valid_pcm_samples(self):
        """Test parsing valid PCM samples."""
        validator = AudioQualityValidator()
        audio = create_pcm_audio(duration_seconds=0.1, amplitude=0.5)
        samples = validator._parse_pcm_samples(audio)
        
        assert isinstance(samples, list)
        assert len(samples) == 1600  # 16000 * 0.1
        assert all(isinstance(s, int) for s in samples)
    
    def test_parse_pcm_samples_with_odd_bytes(self):
        """Test parsing PCM with odd number of bytes (should truncate)."""
        validator = AudioQualityValidator()
        audio = b'\x00\x01\x02\x03\x04'  # 5 bytes (2.5 samples)
        samples = validator._parse_pcm_samples(audio)
        
        assert len(samples) == 2  # Should parse 2 complete samples


class TestIsSilent:
    """Test _is_silent internal method."""
    
    def test_is_silent_with_all_zeros(self):
        """Test silence detection with all zero samples."""
        validator = AudioQualityValidator()
        samples = [0] * 1000
        assert validator._is_silent(samples) is True
    
    def test_is_silent_with_low_amplitude(self):
        """Test silence detection with low amplitude samples."""
        validator = AudioQualityValidator()
        samples = [100] * 1000  # Below 5% of 32767
        assert validator._is_silent(samples) is True
    
    def test_is_silent_with_normal_amplitude(self):
        """Test silence detection with normal amplitude samples."""
        validator = AudioQualityValidator()
        samples = [10000] * 1000  # Above 5% of 32767
        assert validator._is_silent(samples) is False
    
    def test_is_silent_with_empty_samples(self):
        """Test silence detection with empty sample list."""
        validator = AudioQualityValidator()
        assert validator._is_silent([]) is True


class TestHasClipping:
    """Test _has_clipping internal method."""
    
    def test_has_clipping_with_max_amplitude(self):
        """Test clipping detection with max amplitude samples."""
        validator = AudioQualityValidator()
        samples = [32767] * 200 + [10000] * 800  # 20% at max
        assert validator._has_clipping(samples) is True
    
    def test_has_clipping_with_negative_max_amplitude(self):
        """Test clipping detection with negative max amplitude samples."""
        validator = AudioQualityValidator()
        samples = [-32767] * 200 + [10000] * 800  # 20% at min
        assert validator._has_clipping(samples) is True
    
    def test_has_clipping_below_threshold(self):
        """Test clipping detection below threshold."""
        validator = AudioQualityValidator()
        samples = [32767] * 5 + [10000] * 995  # 0.5% at max
        assert validator._has_clipping(samples) is False
    
    def test_has_clipping_with_normal_amplitude(self):
        """Test clipping detection with normal amplitude samples."""
        validator = AudioQualityValidator()
        samples = [10000] * 1000
        assert validator._has_clipping(samples) is False
    
    def test_has_clipping_with_empty_samples(self):
        """Test clipping detection with empty sample list."""
        validator = AudioQualityValidator()
        assert validator._has_clipping([]) is False


class TestCalculateDuration:
    """Test _calculate_duration internal method."""
    
    def test_calculate_duration_one_second(self):
        """Test duration calculation for 1 second of audio."""
        validator = AudioQualityValidator()
        audio = create_pcm_audio(duration_seconds=1.0)
        duration = validator._calculate_duration(audio)
        assert 0.99 < duration < 1.01
    
    def test_calculate_duration_half_second(self):
        """Test duration calculation for 0.5 seconds of audio."""
        validator = AudioQualityValidator()
        audio = create_pcm_audio(duration_seconds=0.5)
        duration = validator._calculate_duration(audio)
        assert 0.49 < duration < 0.51
    
    def test_calculate_duration_five_seconds(self):
        """Test duration calculation for 5 seconds of audio."""
        validator = AudioQualityValidator()
        audio = create_pcm_audio(duration_seconds=5.0)
        duration = validator._calculate_duration(audio)
        assert 4.99 < duration < 5.01


class TestValidationResultDataclass:
    """Test ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creating ValidationResult instance."""
        result = ValidationResult(
            is_valid=False,
            issues=[AudioIssue.SILENT, AudioIssue.TOO_SHORT],
            suggestions=["Speak louder", "Record longer"]
        )
        assert result.is_valid is False
        assert len(result.issues) == 2
        assert AudioIssue.SILENT in result.issues
        assert AudioIssue.TOO_SHORT in result.issues
        assert len(result.suggestions) == 2


class TestAudioIssueEnum:
    """Test AudioIssue enum values."""
    
    def test_audio_issue_values(self):
        """Test AudioIssue enum values."""
        assert AudioIssue.SILENT.value == "audio_silent"
        assert AudioIssue.TOO_SHORT.value == "audio_too_short"
        assert AudioIssue.CLIPPING.value == "audio_clipping"
        assert AudioIssue.LOW_QUALITY.value == "audio_low_quality"
        assert AudioIssue.CORRUPTED.value == "audio_corrupted"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_validate_exactly_at_silence_threshold(self):
        """Test audio with samples exactly at silence threshold."""
        validator = AudioQualityValidator()
        threshold_amplitude = int(32767 * 0.05)
        num_samples = 16000
        samples = [threshold_amplitude] * num_samples
        audio_data = struct.pack(f'<{num_samples}h', *samples)
        result = validator.validate(audio_data)
        
        # Samples at threshold should not be considered silent
        assert AudioIssue.SILENT not in result.issues
    
    def test_validate_exactly_at_clipping_threshold(self):
        """Test audio with samples exactly at clipping threshold."""
        validator = AudioQualityValidator()
        clipping_threshold = 32767 - 100
        num_samples = 16000
        samples = [clipping_threshold] * num_samples
        audio_data = struct.pack(f'<{num_samples}h', *samples)
        result = validator.validate(audio_data)
        
        # All samples at threshold should trigger clipping
        assert result.is_valid is False
        assert AudioIssue.CLIPPING in result.issues
    
    def test_validate_very_long_audio(self):
        """Test validation of very long audio (10 seconds)."""
        validator = AudioQualityValidator()
        long_audio = create_pcm_audio(duration_seconds=10.0, amplitude=0.5)
        result = validator.validate(long_audio)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
