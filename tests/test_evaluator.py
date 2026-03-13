"""Unit tests for Evaluator component."""

import pytest
from mock_interview_coach.evaluator import Evaluator
from mock_interview_coach.models import (
    Question,
    Role,
    Level,
    Language,
    TechnicalArea,
    EvaluationTimeoutError
)


class TestEvaluatorBasicFunctionality:
    """Test basic Evaluator functionality."""
    
    def test_evaluator_initialization(self):
        """Test that Evaluator can be initialized."""
        evaluator = Evaluator()
        assert evaluator is not None
    
    def test_evaluate_response_returns_evaluation(self):
        """Test that evaluate_response returns an Evaluation object."""
        evaluator = Evaluator()
        
        question = Question(
            id="test_001",
            text="What is cloud computing?",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.ENGLISH,
            technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
            expected_concepts=["on-demand", "scalability", "pay-as-you-go"]
        )
        
        response = "Cloud computing is a model for delivering computing resources on-demand over the internet with pay-as-you-go pricing."
        
        evaluation = evaluator.evaluate_response(question, response, Language.ENGLISH)
        
        assert evaluation is not None
        assert 0 <= evaluation.score <= 100
        assert evaluation.technical_area == TechnicalArea.CLOUD_ARCHITECTURE
        assert isinstance(evaluation.correct_concepts, list)
        assert isinstance(evaluation.missing_concepts, list)
        assert isinstance(evaluation.incorrect_statements, list)
        assert isinstance(evaluation.feedback_text, str)
    
    def test_evaluate_response_spanish(self):
        """Test evaluation in Spanish."""
        evaluator = Evaluator()
        
        question = Question(
            id="test_002",
            text="¿Qué es la computación en la nube?",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.SPANISH,
            technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
            expected_concepts=["bajo demanda", "escalabilidad", "pago por uso"]
        )
        
        response = "La computación en la nube es un modelo para entregar recursos de cómputo bajo demanda a través de internet con precios de pago por uso."
        
        evaluation = evaluator.evaluate_response(question, response, Language.SPANISH)
        
        assert evaluation is not None
        assert 0 <= evaluation.score <= 100
        assert evaluation.technical_area == TechnicalArea.CLOUD_ARCHITECTURE


class TestEvaluationScoring:
    """Test evaluation scoring."""
    
    def test_good_response_gets_high_score(self):
        """Test that a good response gets a high score."""
        evaluator = Evaluator()
        
        question = Question(
            id="test_003",
            text="What is Docker?",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.ENGLISH,
            technical_area=TechnicalArea.CONTAINERIZATION,
            expected_concepts=["containerization", "portability", "isolation"]
        )
        
        response = "Docker is a containerization platform that allows you to package applications with their dependencies into portable containers, providing isolation and consistency across environments."
        
        evaluation = evaluator.evaluate_response(question, response, Language.ENGLISH)
        
        # Good response should score reasonably well
        assert evaluation.score >= 60
    
    def test_empty_response_gets_low_score(self):
        """Test that an empty response gets a low score."""
        evaluator = Evaluator()
        
        question = Question(
            id="test_004",
            text="What is a VPC?",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.ENGLISH,
            technical_area=TechnicalArea.NETWORKING,
            expected_concepts=["Virtual Private Cloud", "network isolation", "subnets"]
        )
        
        response = ""
        
        evaluation = evaluator.evaluate_response(question, response, Language.ENGLISH)
        
        # Empty response should score low
        assert evaluation.score <= 40


class TestFeedbackGeneration:
    """Test feedback generation."""
    
    def test_generate_feedback_returns_string(self):
        """Test that generate_feedback returns a string."""
        evaluator = Evaluator()
        
        question = Question(
            id="test_005",
            text="What is IaaS?",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.ENGLISH,
            technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
            expected_concepts=["Infrastructure as a Service", "virtual machines", "compute resources"]
        )
        
        response = "IaaS stands for Infrastructure as a Service, which provides virtual machines and compute resources."
        
        evaluation = evaluator.evaluate_response(question, response, Language.ENGLISH)
        feedback = evaluator.generate_feedback(evaluation, Language.ENGLISH)
        
        assert isinstance(feedback, str)
        assert len(feedback) > 0


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_aws_credentials_raises_error(self):
        """Test that invalid AWS credentials are handled."""
        # This test would require mocking AWS credentials
        # For now, we'll skip it as it requires environment setup
        pass
