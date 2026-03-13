"""Unit tests for QuestionGenerator component."""

import pytest
from mock_interview_coach.question_generator import QuestionGenerator
from mock_interview_coach.models import (
    Role,
    Level,
    Language,
    TechnicalArea,
    QuestionGenerationError,
)


class TestQuestionGeneratorConfiguration:
    """Test QuestionGenerator configuration."""
    
    def test_configure_cloud_engineer_junior_english(self):
        """Test configuration for Cloud Engineer Junior in English."""
        generator = QuestionGenerator()
        generator.configure(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.ENGLISH)
        
        assert generator.get_question_count() > 0
        question = generator.get_next_question()
        assert question is not None
        assert question.role == Role.CLOUD_ENGINEER
        assert question.level == Level.JUNIOR
        assert question.language == Language.ENGLISH
    
    def test_configure_cloud_engineer_junior_spanish(self):
        """Test configuration for Cloud Engineer Junior in Spanish."""
        generator = QuestionGenerator()
        generator.configure(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.SPANISH)
        
        assert generator.get_question_count() > 0
        question = generator.get_next_question()
        assert question is not None
        assert question.role == Role.CLOUD_ENGINEER
        assert question.level == Level.JUNIOR
        assert question.language == Language.SPANISH
    
    def test_configure_unsupported_combination_raises_error(self):
        """Test that unsupported role/level/language combinations raise error."""
        generator = QuestionGenerator()
        
        # DevOps Engineer is not yet implemented
        with pytest.raises(QuestionGenerationError):
            generator.configure(Role.DEVOPS_ENGINEER, Level.JUNIOR, Language.ENGLISH)


class TestQuestionSelection:
    """Test question selection logic."""
    
    def test_get_next_question_returns_questions_in_sequence(self):
        """Test that get_next_question returns questions sequentially."""
        generator = QuestionGenerator()
        generator.configure(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.ENGLISH, demo_mode=True)
        
        question_count = generator.get_question_count()
        questions = []
        
        for _ in range(question_count):
            question = generator.get_next_question()
            assert question is not None
            questions.append(question)
        
        # After all questions, should return None
        assert generator.get_next_question() is None
        
        # All questions should be unique
        question_ids = [q.id for q in questions]
        assert len(question_ids) == len(set(question_ids))
    
    def test_question_count_matches_available_questions(self):
        """Test that question count matches actual available questions."""
        generator = QuestionGenerator()
        generator.configure(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.ENGLISH, demo_mode=True)
        
        expected_count = generator.get_question_count()
        actual_count = 0
        
        while generator.get_next_question() is not None:
            actual_count += 1
        
        assert actual_count == expected_count
    
    def test_all_questions_have_correct_attributes(self):
        """Test that all questions have required attributes."""
        generator = QuestionGenerator()
        generator.configure(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.ENGLISH)
        
        while True:
            question = generator.get_next_question()
            if question is None:
                break
            
            # Check all required attributes
            assert question.id
            assert question.text
            assert question.role == Role.CLOUD_ENGINEER
            assert question.level == Level.JUNIOR
            assert question.language == Language.ENGLISH
            assert isinstance(question.technical_area, TechnicalArea)
            assert isinstance(question.expected_concepts, list)
            assert len(question.expected_concepts) > 0


class TestDemoMode:
    """Test demo mode functionality."""
    
    def test_demo_mode_cloud_engineer_junior_english(self):
        """Test demo mode for Cloud Engineer Junior in English."""
        generator = QuestionGenerator()
        generator.configure(
            Role.CLOUD_ENGINEER, 
            Level.JUNIOR, 
            Language.ENGLISH, 
            demo_mode=True
        )
        
        question_count = generator.get_question_count()
        assert question_count >= 5, "Demo mode should have at least 5 questions"
        
        questions = []
        for _ in range(question_count):
            question = generator.get_next_question()
            assert question is not None
            assert question.role == Role.CLOUD_ENGINEER
            assert question.level == Level.JUNIOR
            assert question.language == Language.ENGLISH
            questions.append(question)
        
        # Verify all questions are for Cloud Engineer Junior
        assert all(q.role == Role.CLOUD_ENGINEER for q in questions)
        assert all(q.level == Level.JUNIOR for q in questions)
        assert all(q.language == Language.ENGLISH for q in questions)
    
    def test_demo_mode_cloud_engineer_junior_spanish(self):
        """Test demo mode for Cloud Engineer Junior in Spanish."""
        generator = QuestionGenerator()
        generator.configure(
            Role.CLOUD_ENGINEER, 
            Level.JUNIOR, 
            Language.SPANISH, 
            demo_mode=True
        )
        
        question_count = generator.get_question_count()
        assert question_count >= 5, "Demo mode should have at least 5 questions"
        
        questions = []
        for _ in range(question_count):
            question = generator.get_next_question()
            assert question is not None
            assert question.role == Role.CLOUD_ENGINEER
            assert question.level == Level.JUNIOR
            assert question.language == Language.SPANISH
            questions.append(question)
        
        # Verify all questions are for Cloud Engineer Junior in Spanish
        assert all(q.role == Role.CLOUD_ENGINEER for q in questions)
        assert all(q.level == Level.JUNIOR for q in questions)
        assert all(q.language == Language.SPANISH for q in questions)
    
    def test_demo_mode_deterministic_order(self):
        """Test that demo mode returns questions in deterministic order."""
        # First session
        generator1 = QuestionGenerator()
        generator1.configure(
            Role.CLOUD_ENGINEER, 
            Level.JUNIOR, 
            Language.ENGLISH, 
            demo_mode=True
        )
        
        questions1 = []
        while True:
            question = generator1.get_next_question()
            if question is None:
                break
            questions1.append(question)
        
        # Second session
        generator2 = QuestionGenerator()
        generator2.configure(
            Role.CLOUD_ENGINEER, 
            Level.JUNIOR, 
            Language.ENGLISH, 
            demo_mode=True
        )
        
        questions2 = []
        while True:
            question = generator2.get_next_question()
            if question is None:
                break
            questions2.append(question)
        
        # Questions should be identical and in same order
        assert len(questions1) == len(questions2)
        for q1, q2 in zip(questions1, questions2):
            assert q1.id == q2.id
            assert q1.text == q2.text
            assert q1.role == q2.role
            assert q1.level == q2.level
            assert q1.language == q2.language


class TestQuestionCountBoundaries:
    """Test question count boundaries."""
    
    def test_question_count_within_session_bounds(self):
        """Test that question count is appropriate for a session (5-10 questions)."""
        generator = QuestionGenerator()
        generator.configure(Role.CLOUD_ENGINEER, Level.JUNIOR, Language.ENGLISH)
        
        question_count = generator.get_question_count()
        # The question bank has 10 questions, which is within bounds
        assert question_count >= 5, "Should have at least 5 questions"
        assert question_count <= 10, "Should have at most 10 questions for a session"
    
    def test_demo_mode_question_count_within_bounds(self):
        """Test that demo mode question count is within session bounds."""
        generator = QuestionGenerator()
        generator.configure(
            Role.CLOUD_ENGINEER, 
            Level.JUNIOR, 
            Language.ENGLISH, 
            demo_mode=True
        )
        
        question_count = generator.get_question_count()
        assert question_count >= 5, "Demo mode should have at least 5 questions"
        assert question_count <= 10, "Demo mode should have at most 10 questions"


class TestReset:
    """Test reset functionality."""
    
    def test_reset_allows_restarting_questions(self):
        """Test that reset allows restarting from the beginning."""
        generator = QuestionGenerator()
        generator.configure(
            Role.CLOUD_ENGINEER, 
            Level.JUNIOR, 
            Language.ENGLISH, 
            demo_mode=True
        )
        
        # Get first question
        first_question = generator.get_next_question()
        assert first_question is not None
        
        # Get a few more questions
        generator.get_next_question()
        generator.get_next_question()
        
        # Reset
        generator.reset()
        
        # Should get the same first question again
        reset_first_question = generator.get_next_question()
        assert reset_first_question is not None
        assert reset_first_question.id == first_question.id
    
    def test_reset_restores_full_question_count(self):
        """Test that reset restores the full question count."""
        generator = QuestionGenerator()
        generator.configure(
            Role.CLOUD_ENGINEER, 
            Level.JUNIOR, 
            Language.ENGLISH, 
            demo_mode=True
        )
        
        original_count = generator.get_question_count()
        
        # Consume some questions
        generator.get_next_question()
        generator.get_next_question()
        
        # Reset
        generator.reset()
        
        # Count should be restored
        count_after_reset = 0
        while generator.get_next_question() is not None:
            count_after_reset += 1
        
        assert count_after_reset == original_count


class TestErrorHandling:
    """Test error handling."""
    
    def test_get_next_question_before_configure_returns_none(self):
        """Test that calling get_next_question before configure returns None."""
        generator = QuestionGenerator()
        
        # Should return None when not configured
        assert generator.get_next_question() is None
    
    def test_get_question_count_before_configure_returns_zero(self):
        """Test that calling get_question_count before configure returns 0."""
        generator = QuestionGenerator()
        
        # Should return 0 when not configured
        assert generator.get_question_count() == 0
    
    def test_reset_before_configure_does_not_crash(self):
        """Test that calling reset before configure does not crash."""
        generator = QuestionGenerator()
        
        # Should not raise an exception
        generator.reset()
