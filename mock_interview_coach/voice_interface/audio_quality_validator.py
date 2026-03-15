"""Audio quality validation module for Nova Sonic voice integration.

This module validates audio quality before sending to Nova Sonic API to avoid
wasting API calls on poor quality audio. It detects common issues like silence,
clipping, and insufficient duration.
"""

import struct
from dataclasses import dataclass
from enum import Enum
from typing import List


class AudioIssue(Enum):
    """Audio quality issues that can be detected."""
    SILENT = "audio_silent"
    TOO_SHORT = "audio_too_short"
    CLIPPING = "audio_clipping"
    LOW_QUALITY = "audio_low_quality"
    CORRUPTED = "audio_corrupted"


@dataclass
class ValidationResult:
    """Result of audio quality validation.
    
    Attributes:
        is_valid: Whether the audio passes quality checks
        issues: List of detected audio issues
        suggestions: List of suggestions to improve audio quality
    """
    is_valid: bool
    issues: List[AudioIssue]
    suggestions: List[str]


class AudioQualityValidator:
    """Validates audio quality before processing.
    
    Detects:
    - Silent audio (>95% samples below threshold)
    - Clipping (>1% samples at max amplitude)
    - Insufficient duration (<1 second)
    """
    
    # Validation thresholds
    # Intentionally permissive: Nova Sonic handles short/quiet audio gracefully.
    # Only block audio that is provably empty or corrupted.
    SILENCE_THRESHOLD = 0.005          # 0.5% of max amplitude (was 5%)
    SILENCE_PERCENTAGE_THRESHOLD = 0.999  # 99.9% silent (was 95%)
    CLIPPING_PERCENTAGE_THRESHOLD = 0.01   # 1% of samples
    MIN_DURATION_SECONDS = 0.25        # 1 AudioWorklet buffer ≈ 256 ms (was 1.0 s)
    
    # Audio format assumptions for PCM
    SAMPLE_RATE = 16000  # Hz
    SAMPLE_WIDTH = 2  # bytes (16-bit)
    CHANNELS = 1  # mono
    
    def validate(self, audio_data: bytes) -> ValidationResult:
        """Validate audio quality.
        
        Args:
            audio_data: Raw audio data bytes (PCM 16-bit format expected)
        
        Returns:
            ValidationResult with validation status, issues, and suggestions
        """
        issues: List[AudioIssue] = []
        suggestions: List[str] = []
        
        # Check if audio data is empty or corrupted
        if not audio_data:
            issues.append(AudioIssue.CORRUPTED)
            suggestions.append("Audio data is empty. Please try recording again.")
            return ValidationResult(is_valid=False, issues=issues, suggestions=suggestions)
        
        # Check minimum size (at least 1 second of audio)
        min_bytes = self.SAMPLE_RATE * self.SAMPLE_WIDTH * self.CHANNELS * self.MIN_DURATION_SECONDS
        if len(audio_data) < min_bytes:
            issues.append(AudioIssue.TOO_SHORT)
            suggestions.append(
                f"Audio is too short ({self._calculate_duration(audio_data):.1f}s). "
                f"Please record for at least {self.MIN_DURATION_SECONDS} second."
            )
        
        # Try to parse audio samples
        try:
            samples = self._parse_pcm_samples(audio_data)
        except Exception as e:
            issues.append(AudioIssue.CORRUPTED)
            suggestions.append(f"Audio data is corrupted or in an unexpected format. Please try recording again.")
            return ValidationResult(is_valid=False, issues=issues, suggestions=suggestions)
        
        if not samples:
            issues.append(AudioIssue.CORRUPTED)
            suggestions.append("No audio samples found. Please try recording again.")
            return ValidationResult(is_valid=False, issues=issues, suggestions=suggestions)
        
        # Check for silence
        if self._is_silent(samples):
            issues.append(AudioIssue.SILENT)
            suggestions.append(
                "Audio is too quiet or silent. Please speak louder or move closer to the microphone."
            )
        
        # Check for clipping
        if self._has_clipping(samples):
            issues.append(AudioIssue.CLIPPING)
            suggestions.append(
                "Audio is clipping (too loud). Please speak softer or move away from the microphone."
            )
        
        # Determine if audio is valid
        is_valid = len(issues) == 0
        
        return ValidationResult(is_valid=is_valid, issues=issues, suggestions=suggestions)
    
    def _parse_pcm_samples(self, audio_data: bytes) -> List[int]:
        """Parse PCM audio data into samples.
        
        Args:
            audio_data: Raw PCM audio data (16-bit little-endian)
        
        Returns:
            List of sample values (signed 16-bit integers)
        
        Raises:
            struct.error: If audio data cannot be parsed
        """
        # PCM 16-bit samples are 2 bytes each
        num_samples = len(audio_data) // self.SAMPLE_WIDTH
        
        # Unpack as signed 16-bit integers (little-endian)
        format_string = f"<{num_samples}h"  # '<' = little-endian, 'h' = signed short (16-bit)
        
        try:
            samples = list(struct.unpack(format_string, audio_data[:num_samples * self.SAMPLE_WIDTH]))
            return samples
        except struct.error as e:
            raise ValueError(f"Failed to parse PCM samples: {e}")
    
    def _is_silent(self, samples: List[int]) -> bool:
        """Check if audio is mostly silent.
        
        Args:
            samples: List of PCM sample values
        
        Returns:
            True if >95% of samples are below silence threshold
        """
        if not samples:
            return True
        
        # Calculate threshold amplitude (5% of max 16-bit value)
        max_amplitude = 32767  # Max value for signed 16-bit
        threshold = int(max_amplitude * self.SILENCE_THRESHOLD)
        
        # Count samples below threshold
        silent_samples = sum(1 for sample in samples if abs(sample) < threshold)
        
        # Check if more than 95% are silent
        silent_percentage = silent_samples / len(samples)
        return silent_percentage > self.SILENCE_PERCENTAGE_THRESHOLD
    
    def _has_clipping(self, samples: List[int]) -> bool:
        """Check if audio has clipping (samples at max amplitude).
        
        Args:
            samples: List of PCM sample values
        
        Returns:
            True if >1% of samples are at max amplitude
        """
        if not samples:
            return False
        
        # Max amplitude for 16-bit audio
        max_amplitude = 32767
        clipping_threshold = max_amplitude - 100  # Allow small margin
        
        # Count samples at or near max amplitude
        clipped_samples = sum(
            1 for sample in samples 
            if abs(sample) >= clipping_threshold
        )
        
        # Check if more than 1% are clipped
        clipping_percentage = clipped_samples / len(samples)
        return clipping_percentage > self.CLIPPING_PERCENTAGE_THRESHOLD
    
    def _calculate_duration(self, audio_data: bytes) -> float:
        """Calculate audio duration in seconds.
        
        Args:
            audio_data: Raw PCM audio data
        
        Returns:
            Duration in seconds
        """
        num_samples = len(audio_data) // self.SAMPLE_WIDTH
        duration = num_samples / self.SAMPLE_RATE
        return duration
