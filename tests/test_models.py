"""Unit tests for core data models."""

import pytest
from datetime import datetime
from mock_interview_coach.models import (
    Role, Level, Language, TechnicalArea, AudioState, ResourceType,
    Question, Evaluation, SessionState, Report, Resource,
    InterviewError, AudioCaptureError, EvaluationTimeoutError, QuestionGenerationError
)


class TestEnums:
    """Test core enum definitions."""
    
    def test_role_enum_values(self):
        """Test Role enum has correct values."""
        assert Role.CLOUD_ENGINEER.value == "cloud_engineer"
        assert Role.DEVOPS_ENGINEER.value == "devops_engineer"
        assert Role.ML_ENGINEER.value == "ml_engineer"
    
    def test_level_enum_values(self):
        """Test Level enum has correct values."""
        assert Level.JUNIOR.value == "junior"
        assert Level.MID.value == "mid"
    
    def test_language_enum_values(self):
        """Test Language enum has correct values."""
        assert Language.SPANISH.value == "es"
        assert Language.ENGLISH.value == "en"
    
    def test_technical_area_enum_values(self):
        """Test TechnicalArea enum has all required areas."""
        areas = [area.value for area in TechnicalArea]
        assert "cloud_architecture" in areas
        assert "networking" in areas
        assert "security" in areas
        assert "containerization" in areas
        assert "ci_cd" in areas
        assert "monitoring" in areas
        assert "infrastructure_as_code" in areas
        assert "ml_fundamentals" in areas
        assert "data_processing" in areas
        assert "model_deployment" in areas
    
    def test_audio_state_enum_values(self):
        """Test AudioState enum has correct values."""
        assert AudioState.IDLE.value == "idle"
        assert AudioState.SPEAKING.value == "speaking"
        assert AudioState.LISTENING.value == "listening"
        assert AudioState.PROCESSING.value == "processing"
    
    def test_resource_type_enum_values(self):
        """Test ResourceType enum has correct values."""
        assert ResourceType.DOCUMENTATION.value == "documentation"
        assert ResourceType.TUTORIAL.value == "tutorial"
        assert ResourceType.PRACTICE.value == "practice"


class TestDataClasses:
    """Test core data class instantiation."""
    
    def test_question_creation(self):
        """Test Question data class can be instantiated."""
        question = Question(
            id="q1",
            text="What is cloud computing?",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.ENGLISH,
            technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
            expected_concepts=["IaaS", "PaaS", "SaaS"]
        )
        assert question.id == "q1"
        assert question.role == Role.CLOUD_ENGINEER
        assert len(question.expected_concepts) == 3
    
    def test_evaluation_creation(self):
        """Test Evaluation data class can be instantiated."""
        evaluation = Evaluation(
            score=85,
            correct_concepts=["IaaS", "PaaS"],
            missing_concepts=["SaaS"],
            incorrect_statements=[],
            feedback_text="Good understanding of cloud models.",
            technical_area=TechnicalArea.CLOUD_ARCHITECTURE
        )
        assert evaluation.score == 85
        assert len(evaluation.correct_concepts) == 2
        assert len(evaluation.missing_concepts) == 1
    
    def test_resource_creation(self):
        """Test Resource data class can be instantiated."""
        resource = Resource(
            title="AWS Documentation",
            url="https://aws.amazon.com/docs",
            type=ResourceType.DOCUMENTATION,
            language=Language.ENGLISH,
            is_free=True,
            description="Official AWS documentation"
        )
        assert resource.title == "AWS Documentation"
        assert resource.is_free is True
    
    def test_session_state_creation(self):
        """Test SessionState data class can be instantiated."""
        now = datetime.now()
        session = SessionState(
            session_id="session1",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.ENGLISH,
            demo_mode=True,
            current_question_index=0,
            questions=[],
            responses=[],
            evaluations=[],
            is_paused=False,
            audio_state=AudioState.IDLE,
            created_at=now,
            updated_at=now
        )
        assert session.session_id == "session1"
        assert session.demo_mode is True
        assert session.audio_state == AudioState.IDLE
    
    def test_report_creation(self):
        """Test Report data class can be instantiated."""
        report = Report(
            session_id="session1",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.ENGLISH,
            overall_score=75,
            area_scores={TechnicalArea.CLOUD_ARCHITECTURE: 80},
            questions_and_responses=[],
            learning_resources={},
            timestamp=datetime.now()
        )
        assert report.session_id == "session1"
        assert report.overall_score == 75


class TestExceptions:
    """Test custom exception classes."""
    
    def test_interview_error(self):
        """Test InterviewError can be raised."""
        with pytest.raises(InterviewError):
            raise InterviewError("Test error")
    
    def test_audio_capture_error(self):
        """Test AudioCaptureError can be raised."""
        with pytest.raises(AudioCaptureError):
            raise AudioCaptureError("Audio failed")
    
    def test_evaluation_timeout_error(self):
        """Test EvaluationTimeoutError can be raised."""
        with pytest.raises(EvaluationTimeoutError):
            raise EvaluationTimeoutError("Timeout")
    
    def test_question_generation_error(self):
        """Test QuestionGenerationError can be raised."""
        with pytest.raises(QuestionGenerationError):
            raise QuestionGenerationError("Generation failed")
    
    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from InterviewError."""
        assert issubclass(AudioCaptureError, InterviewError)
        assert issubclass(EvaluationTimeoutError, InterviewError)
        assert issubclass(QuestionGenerationError, InterviewError)
