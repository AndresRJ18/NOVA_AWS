"""Core enums for the Mock Interview Coach system."""

from enum import Enum


class Role(Enum):
    """Technical role for interview practice."""
    CLOUD_ENGINEER = "cloud_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    ML_ENGINEER = "ml_engineer"


class Level(Enum):
    """Experience level for interview practice."""
    JUNIOR = "junior"
    MID = "mid"


class Language(Enum):
    """Supported interview languages."""
    SPANISH = "es"
    ENGLISH = "en"


class TechnicalArea(Enum):
    """Technical knowledge categories evaluated during interviews."""
    CLOUD_ARCHITECTURE = "cloud_architecture"
    NETWORKING = "networking"
    SECURITY = "security"
    CONTAINERIZATION = "containerization"
    CI_CD = "ci_cd"
    MONITORING = "monitoring"
    INFRASTRUCTURE_AS_CODE = "infrastructure_as_code"
    MACHINE_LEARNING_FUNDAMENTALS = "ml_fundamentals"
    DATA_PROCESSING = "data_processing"
    MODEL_DEPLOYMENT = "model_deployment"


class AudioState(Enum):
    """Current state of the audio interface."""
    IDLE = "idle"
    SPEAKING = "speaking"
    LISTENING = "listening"
    PROCESSING = "processing"


class ResourceType(Enum):
    """Type of learning resource."""
    DOCUMENTATION = "documentation"
    TUTORIAL = "tutorial"
    PRACTICE = "practice"
