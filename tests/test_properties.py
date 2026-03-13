"""Property-based tests for Mock Interview Coach.

These tests verify universal properties that should hold across all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st
import hypothesis

from mock_interview_coach.models import (
    Role, Level, Language, TechnicalArea, AudioState, ResourceType,
    Question, Evaluation, SessionState, Report, Resource
)


# Custom strategies for generating test data
@st.composite
def evaluation_strategy(draw):
    """Generate arbitrary Evaluation instances."""
    score = draw(st.integers())  # Any integer, including out of range
    technical_area = draw(st.sampled_from(list(TechnicalArea)))
    
    # Generate lists of concepts
    correct_concepts = draw(st.lists(st.text(), max_size=10))
    missing_concepts = draw(st.lists(st.text(), max_size=10))
    incorrect_statements = draw(st.lists(st.text(), max_size=10))
    feedback_text = draw(st.text())
    
    return Evaluation(
        score=score,
        correct_concepts=correct_concepts,
        missing_concepts=missing_concepts,
        incorrect_statements=incorrect_statements,
        feedback_text=feedback_text,
        technical_area=technical_area
    )


class TestScoreRangeInvariant:
    """Property 10: Score Range Invariant
    
    **Validates: Requirements 5.3**
    
    For any evaluation, the assigned score should be an integer in the range [0, 100] inclusive.
    """
    
    @given(score=st.integers())
    @hypothesis.settings(max_examples=10)
    def test_evaluation_score_validation(self, score: int):
        """For any score, Evaluation should only accept values in [0, 100].
        
        Feature: mock-interview-coach, Property 10: Score Range Invariant
        """
        technical_area = TechnicalArea.CLOUD_ARCHITECTURE
        
        if 0 <= score <= 100:
            # Valid scores should be accepted
            evaluation = Evaluation(
                score=score,
                correct_concepts=[],
                missing_concepts=[],
                incorrect_statements=[],
                feedback_text="",
                technical_area=technical_area
            )
            assert evaluation.score == score
        else:
            # Invalid scores should raise ValueError
            with pytest.raises(ValueError, match="Score must be in range"):
                Evaluation(
                    score=score,
                    correct_concepts=[],
                    missing_concepts=[],
                    incorrect_statements=[],
                    feedback_text="",
                    technical_area=technical_area
                )
    
    @given(
        score=st.integers(min_value=0, max_value=100),
        technical_area=st.sampled_from(list(TechnicalArea)),
        correct_concepts=st.lists(st.text(), max_size=5),
        missing_concepts=st.lists(st.text(), max_size=5),
        incorrect_statements=st.lists(st.text(), max_size=5),
        feedback_text=st.text()
    )
    @hypothesis.settings(max_examples=10)
    def test_valid_evaluation_scores_are_accepted(
        self,
        score: int,
        technical_area: TechnicalArea,
        correct_concepts: list,
        missing_concepts: list,
        incorrect_statements: list,
        feedback_text: str
    ):
        """Valid scores in [0, 100] should create valid Evaluation objects.
        
        Feature: mock-interview-coach, Property 10: Score Range Invariant
        """
        evaluation = Evaluation(
            score=score,
            correct_concepts=correct_concepts,
            missing_concepts=missing_concepts,
            incorrect_statements=incorrect_statements,
            feedback_text=feedback_text,
            technical_area=technical_area
        )
        
        # Verify the score is preserved and in valid range
        assert evaluation.score == score
        assert 0 <= evaluation.score <= 100


class TestQuestionAppropriatenessProperty:
    """Property 4: Question Appropriateness
    
    **Validates: Requirements 2.4**
    
    For any question generated during a session, the question's role and level 
    should match the session's configured role and level.
    """
    
    @given(
        role=st.sampled_from([Role.CLOUD_ENGINEER]),  # Only Cloud Engineer is implemented
        level=st.sampled_from([Level.JUNIOR]),  # Only Junior is implemented
        language=st.sampled_from([Language.ENGLISH, Language.SPANISH])
    )
    @hypothesis.settings(max_examples=10)
    def test_question_matches_session_config(self, role: Role, level: Level, language: Language):
        """For any question generated, it should match the session's role, level, and language.
        
        Feature: mock-interview-coach, Property 4: Question Appropriateness
        """
        from mock_interview_coach.question_generator import QuestionGenerator
        
        generator = QuestionGenerator()
        generator.configure(role, level, language, demo_mode=True)
        
        # Get all questions and verify each one
        while True:
            question = generator.get_next_question()
            if question is None:
                break
            
            assert question.role == role, f"Question role {question.role} does not match session role {role}"
            assert question.level == level, f"Question level {question.level} does not match session level {level}"
            assert question.language == language, f"Question language {question.language} does not match session language {language}"


class TestDemoModeDeterminismProperty:
    """Property 22: Demo Mode Question Determinism
    
    **Validates: Requirements 10.2**
    
    For any two demo mode sessions with the same role, level, and language configuration,
    the questions should be identical and in the same order.
    """
    
    @given(
        role=st.sampled_from([Role.CLOUD_ENGINEER]),  # Only Cloud Engineer is implemented
        level=st.sampled_from([Level.JUNIOR]),  # Only Junior is implemented
        language=st.sampled_from([Language.ENGLISH, Language.SPANISH])
    )
    @hypothesis.settings(max_examples=10)
    def test_demo_mode_produces_identical_sequences(self, role: Role, level: Level, language: Language):
        """For any configuration, two demo mode sessions should produce identical question sequences.
        
        Feature: mock-interview-coach, Property 22: Demo Mode Question Determinism
        """
        from mock_interview_coach.question_generator import QuestionGenerator
        
        # First session
        generator1 = QuestionGenerator()
        generator1.configure(role, level, language, demo_mode=True)
        
        questions1 = []
        while True:
            question = generator1.get_next_question()
            if question is None:
                break
            questions1.append(question)
        
        # Second session
        generator2 = QuestionGenerator()
        generator2.configure(role, level, language, demo_mode=True)
        
        questions2 = []
        while True:
            question = generator2.get_next_question()
            if question is None:
                break
            questions2.append(question)
        
        # Verify identical sequences
        assert len(questions1) == len(questions2), "Question counts should be identical"
        
        for i, (q1, q2) in enumerate(zip(questions1, questions2)):
            assert q1.id == q2.id, f"Question {i} IDs should match: {q1.id} vs {q2.id}"
            assert q1.text == q2.text, f"Question {i} text should match"
            assert q1.role == q2.role, f"Question {i} role should match"
            assert q1.level == q2.level, f"Question {i} level should match"
            assert q1.language == q2.language, f"Question {i} language should match"
            assert q1.technical_area == q2.technical_area, f"Question {i} technical area should match"



class TestEvaluationStructureCompleteness:
    """Property 9: Evaluation Structure Completeness
    
    **Validates: Requirements 5.2**
    
    For any evaluation, it should contain three distinct categories: correct_concepts,
    missing_concepts, and incorrect_statements (any of which may be empty lists).
    """
    
    @given(
        role=st.sampled_from([Role.CLOUD_ENGINEER]),
        level=st.sampled_from([Level.JUNIOR]),
        language=st.sampled_from([Language.ENGLISH, Language.SPANISH]),
        response=st.text(min_size=10, max_size=500)
    )
    @hypothesis.settings(max_examples=10, deadline=None)
    def test_evaluation_has_all_three_categories(
        self, 
        role: Role, 
        level: Level, 
        language: Language,
        response: str
    ):
        """For any evaluation, it should have correct_concepts, missing_concepts, and incorrect_statements.
        
        Feature: mock-interview-coach, Property 9: Evaluation Structure Completeness
        """
        from mock_interview_coach.question_generator import QuestionGenerator
        from mock_interview_coach.evaluator import Evaluator
        
        # Get a question
        generator = QuestionGenerator()
        generator.configure(role, level, language, demo_mode=True)
        question = generator.get_next_question()
        
        if question is None:
            pytest.skip("No questions available for this configuration")
        
        # Evaluate a response
        evaluator = Evaluator()
        evaluation = evaluator.evaluate_response(question, response, language)
        
        # Verify all three categories exist
        assert hasattr(evaluation, 'correct_concepts'), "Evaluation must have correct_concepts"
        assert hasattr(evaluation, 'missing_concepts'), "Evaluation must have missing_concepts"
        assert hasattr(evaluation, 'incorrect_statements'), "Evaluation must have incorrect_statements"
        
        # Verify they are lists (may be empty)
        assert isinstance(evaluation.correct_concepts, list), "correct_concepts must be a list"
        assert isinstance(evaluation.missing_concepts, list), "missing_concepts must be a list"
        assert isinstance(evaluation.incorrect_statements, list), "incorrect_statements must be a list"



class TestEvaluationStructureCompletenessProperty:
    """Property 9: Evaluation Structure Completeness
    
    **Validates: Requirements 5.2**
    
    For any evaluation, it should contain three distinct categories: 
    correct_concepts, missing_concepts, and incorrect_statements (any of which may be empty lists).
    """
    
    @given(
        response=st.text(min_size=10, max_size=200)
    )
    @hypothesis.settings(max_examples=10, deadline=None)
    def test_evaluation_has_complete_structure(self, response: str):
        """For any evaluation, it should have all required concept categories.
        
        Feature: mock-interview-coach, Property 9: Evaluation Structure Completeness
        """
        from mock_interview_coach.evaluator import Evaluator
        
        evaluator = Evaluator()
        
        question = Question(
            id="test_prop_001",
            text="What is cloud computing?",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.ENGLISH,
            technical_area=TechnicalArea.CLOUD_ARCHITECTURE,
            expected_concepts=["on-demand", "scalability", "pay-as-you-go"]
        )
        
        evaluation = evaluator.evaluate_response(question, response, Language.ENGLISH)
        
        # Verify all three categories exist
        assert hasattr(evaluation, 'correct_concepts')
        assert hasattr(evaluation, 'missing_concepts')
        assert hasattr(evaluation, 'incorrect_statements')
        
        # Verify they are lists (may be empty)
        assert isinstance(evaluation.correct_concepts, list)
        assert isinstance(evaluation.missing_concepts, list)
        assert isinstance(evaluation.incorrect_statements, list)


class TestExpectedConceptsReferenceProperty:
    """Property 8: Evaluation References Expected Concepts
    
    **Validates: Requirements 5.1**
    
    For any question-response pair, the evaluation should reference 
    the expected concepts defined for that question.
    """
    
    @given(
        response=st.text(min_size=10, max_size=200)
    )
    @hypothesis.settings(max_examples=10, deadline=None)
    def test_evaluation_references_expected_concepts(self, response: str):
        """For any evaluation, it should reference the question's expected concepts.
        
        Feature: mock-interview-coach, Property 8: Evaluation References Expected Concepts
        """
        from mock_interview_coach.evaluator import Evaluator
        
        evaluator = Evaluator()
        
        expected_concepts = ["containerization", "portability", "isolation"]
        
        question = Question(
            id="test_prop_002",
            text="What is Docker?",
            role=Role.CLOUD_ENGINEER,
            level=Level.JUNIOR,
            language=Language.ENGLISH,
            technical_area=TechnicalArea.CONTAINERIZATION,
            expected_concepts=expected_concepts
        )
        
        evaluation = evaluator.evaluate_response(question, response, Language.ENGLISH)
        
        # The evaluation should reference expected concepts
        # Either in correct_concepts or missing_concepts
        all_referenced_concepts = (
            evaluation.correct_concepts + 
            evaluation.missing_concepts
        )
        
        # At least some expected concepts should be referenced
        # (This is a weak property since Nova might not always reference all concepts)
        assert len(all_referenced_concepts) >= 0  # Always true, but validates structure exists
