"""Custom exception classes for the Mock Interview Coach system."""


class InterviewError(Exception):
    """Base exception for interview system errors."""
    pass


class AudioCaptureError(InterviewError):
    """Raised when audio input fails."""
    pass


class EvaluationTimeoutError(InterviewError):
    """Raised when evaluation takes too long."""
    pass


class QuestionGenerationError(InterviewError):
    """Raised when question generation fails."""
    pass
