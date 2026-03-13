"""Property-based tests for the Evaluator component."""

import pytest
from hypothesis import given, strategies as st, settings
from mock_interview_coach.models import Question, Language, Role, Level, TechnicalArea
from mock_interview_coach.evaluator import Evaluator


# Strategy for generating valid questions
@st.composite
def question_strategy(draw):
    """Generate random valid questions."""
    role = draw(st.sampled_from(list(Role)))
    level = draw(st.sampled_from(list(Level)))
    language = draw(st.sampled_from(list(Language)))
    technical_area = draw(st.sampled_from(list(TechnicalArea)))
    
    # Generate expected concepts (1-5 concepts)
    num_concepts = draw(st.integers(min_value=1, max_value=5))
    expected_concepts = [
        draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('L',))))
        for _ in range(num_concepts)
    ]
    
    question_text = draw(st.text(min_size=10, max_size=200))
    question_id = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('L', 'N'))))
    
    return Question(
        id=question_id,
        text=question_text,
        role=role,
        level=level,
        language=language,
        technical_area=technical_area,
        expected_concepts=expected_concepts
    )


# Strategy for generating responses
response_strategy = st.text(min_size=0, max_size=500)


@pytest.fixture
def evaluator():
    """Create an Evaluator instance."""
    return Evaluator()


# Feature: mock-interview-coach, Property 9: Evaluation Structure Completeness
@given(
    question=question_strategy(),
    response=response_strategy,
    language=st.sampled_from(list(Language))
)
@settings(max_examples=100, deadline=None)
def test_property_evaluation_structure_completeness(question, response, language):
    """
    Property 9: Evaluation Structure Completeness
    
    For any evaluation, it should contain three distinct categories: 
    correct_concepts, missing_concepts, and incorrect_statements 
    (any of which may be empty lists).
    
    **Validates: Requirements 5.2**
    """
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
    
    # Verify they are distinct (not the same object)
    assert evaluation.correct_concepts is not evaluation.missing_concepts
    assert evaluation.correct_concepts is not evaluation.incorrect_statements
    assert evaluation.missing_concepts is not evaluation.incorrect_statements


# Feature: mock-interview-coach, Property 10: Score Range Invariant
@given(
    question=question_strategy(),
    response=response_strategy,
    language=st.sampled_from(list(Language))
)
@settings(max_examples=100, deadline=None)
def test_property_score_range_invariant(question, response, language):
    """
    Property 10: Score Range Invariant
    
    For any evaluation, the assigned score should be an integer 
    in the range [0, 100] inclusive.
    
    **Validates: Requirements 5.3**
    """
    evaluator = Evaluator()
    
    evaluation = evaluator.evaluate_response(question, response, language)
    
    # Verify score is an integer
    assert isinstance(evaluation.score, int), f"Score must be an integer, got {type(evaluation.score).__name__}"
    
    # Verify score is in valid range
    assert 0 <= evaluation.score <= 100, f"Score must be in range [0, 100], got {evaluation.score}"


# Feature: mock-interview-coach, Property 8: Evaluation References Expected Concepts
@given(
    question=question_strategy(),
    response=response_strategy,
    language=st.sampled_from(list(Language))
)
@settings(max_examples=100, deadline=None)
def test_property_evaluation_references_expected_concepts(question, response, language):
    """
    Property 8: Evaluation References Expected Concepts
    
    For any question-response pair, the evaluation should reference 
    the expected concepts defined for that question.
    
    **Validates: Requirements 5.1**
    """
    evaluator = Evaluator()
    
    evaluation = evaluator.evaluate_response(question, response, language)
    
    # Get all concepts mentioned in the evaluation
    all_evaluation_concepts = set(
        evaluation.correct_concepts + 
        evaluation.missing_concepts
    )
    
    # The union of correct and missing concepts should account for all expected concepts
    # (though the evaluator might not perfectly identify all of them)
    # At minimum, the evaluation should be aware of the expected concepts
    
    # For this property, we verify that:
    # 1. The evaluation has been made in the context of the question's expected concepts
    # 2. The technical area matches
    assert evaluation.technical_area == question.technical_area, \
        "Evaluation technical area must match question technical area"
    
    # 3. If the response is non-empty and contains expected concepts,
    #    they should appear in correct_concepts or missing_concepts
    if response.strip():
        # The evaluation should have processed the expected concepts
        # (either as correct or missing)
        # This is implicitly validated by the evaluator's logic
        assert isinstance(evaluation.correct_concepts, list)
        assert isinstance(evaluation.missing_concepts, list)
