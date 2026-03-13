"""Core data classes for the Mock Interview Coach system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from .enums import Role, Level, Language, TechnicalArea, AudioState, ResourceType


@dataclass
class Question:
    """Represents a technical interview question."""
    id: str
    text: str
    role: Role
    level: Level
    language: Language
    technical_area: TechnicalArea
    expected_concepts: List[str]


@dataclass
class Evaluation:
    """Represents the evaluation of a user's response with detailed structured feedback."""
    score: int  # 0-100
    correct_concepts: List[str]
    missing_concepts: List[str]
    incorrect_statements: List[str] = field(default_factory=list)
    feedback_text: str = ""
    technical_area: TechnicalArea = TechnicalArea.CLOUD_ARCHITECTURE
    
    # New structured feedback fields
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommended_topics: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate score is in valid range [0, 100]."""
        if not isinstance(self.score, int):
            raise TypeError(f"Score must be an integer, got {type(self.score).__name__}")
        if not (0 <= self.score <= 100):
            raise ValueError(f"Score must be in range [0, 100], got {self.score}")


@dataclass
class Resource:
    """Represents a learning resource recommendation."""
    title: str
    url: str
    type: ResourceType
    language: Language
    is_free: bool
    description: str


@dataclass
class SessionState:
    """Represents the current state of an interview session."""
    session_id: str
    role: Role
    level: Level
    language: Language
    demo_mode: bool
    current_question_index: int
    questions: List[Question]
    responses: List[str]
    evaluations: List[Evaluation]
    is_paused: bool
    audio_state: AudioState
    created_at: datetime
    updated_at: datetime


@dataclass
class Report:
    """Represents the final interview report."""
    session_id: str
    role: Role
    level: Level
    language: Language
    overall_score: int
    area_scores: Dict[TechnicalArea, int]
    questions_and_responses: List[Tuple[Question, str, Evaluation]]
    learning_resources: Dict[TechnicalArea, List[Resource]]
    timestamp: datetime


@dataclass
class LatencyMetric:
    """Latency measurement for monitoring voice operations.
    
    This dataclass stores latency measurements for different voice operations
    (STT, TTS, end-to-end) to enable performance monitoring and optimization.
    
    Attributes:
        operation: Type of operation measured ("stt", "tts", "end_to_end")
        latency_ms: Measured latency in milliseconds
        timestamp: When the measurement was taken
        session_id: Session identifier for context
        success: Whether the operation completed successfully
    """
    operation: str  # "stt", "tts", "end_to_end"
    latency_ms: int
    timestamp: datetime
    session_id: str
    success: bool


@dataclass
class VoiceSession:
    """Voice session data for tracking voice interactions.
    
    This dataclass maintains state for a voice-enabled interview session,
    including WebSocket connection info, audio state, and performance metrics.
    
    Attributes:
        session_id: Unique session identifier
        websocket_id: WebSocket connection identifier
        audio_state: Current audio system state
        language: Interview language
        model_id: Nova Sonic model being used
        is_text_fallback: Whether text fallback mode is active
        last_audio: Last audio data for replay functionality
        latency_metrics: List of latency measurements for monitoring
        error_count: Number of errors encountered in this session
        created_at: Session creation timestamp
    """
    session_id: str
    websocket_id: str
    audio_state: AudioState
    language: Language
    model_id: str
    is_text_fallback: bool = False
    last_audio: Optional[bytes] = None
    latency_metrics: List['LatencyMetric'] = field(default_factory=list)
    error_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LatencyMetric:
    """Latency measurement for monitoring voice operations.

    This dataclass stores latency measurements for different voice operations
    (STT, TTS, end-to-end) to enable performance monitoring and optimization.

    Attributes:
        operation: Type of operation measured ("stt", "tts", "end_to_end")
        latency_ms: Measured latency in milliseconds
        timestamp: When the measurement was taken
        session_id: Session identifier for context
        success: Whether the operation completed successfully
    """
    operation: str  # "stt", "tts", "end_to_end"
    latency_ms: int
    timestamp: datetime
    session_id: str
    success: bool


@dataclass
class VoiceSession:
    """Voice session data for tracking voice interactions.

    This dataclass maintains state for a voice-enabled interview session,
    including WebSocket connection info, audio state, and performance metrics.

    Attributes:
        session_id: Unique session identifier
        websocket_id: WebSocket connection identifier
        audio_state: Current audio system state
        language: Interview language
        model_id: Nova Sonic model being used
        is_text_fallback: Whether text fallback mode is active
        last_audio: Last audio data for replay functionality
        latency_metrics: List of latency measurements for monitoring
        error_count: Number of errors encountered in this session
        created_at: Session creation timestamp
    """
    session_id: str
    websocket_id: str
    audio_state: AudioState
    language: Language
    model_id: str
    is_text_fallback: bool = False
    last_audio: Optional[bytes] = None
    latency_metrics: List[LatencyMetric] = field(default_factory=list)
    error_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

