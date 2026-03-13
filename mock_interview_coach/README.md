# Mock Interview Coach

Voice-based technical interview practice system for students and professionals in Latin America.

## Project Structure

```
mock_interview_coach/
├── __init__.py                 # Package initialization
├── models/                     # Core data models and enums
│   ├── __init__.py
│   ├── enums.py               # Role, Level, Language, TechnicalArea, AudioState, ResourceType
│   ├── data_classes.py        # Question, Evaluation, SessionState, Report, Resource
│   └── exceptions.py          # Custom exception classes
├── session_manager/           # Session orchestration
│   ├── __init__.py
│   └── session_manager.py
├── voice_interface/           # Audio input/output handling
│   ├── __init__.py
│   └── voice_interface.py
├── question_generator/        # Question selection logic
│   ├── __init__.py
│   └── question_generator.py
├── evaluator/                 # Response analysis and feedback
│   ├── __init__.py
│   └── evaluator.py
└── report_generator/          # Report creation and PDF export
    ├── __init__.py
    └── report_generator.py
```

## Core Data Models

### Enums
- **Role**: CLOUD_ENGINEER, DEVOPS_ENGINEER, ML_ENGINEER
- **Level**: JUNIOR, MID
- **Language**: SPANISH (es), ENGLISH (en)
- **TechnicalArea**: 10 technical categories (cloud_architecture, networking, security, etc.)
- **AudioState**: IDLE, SPEAKING, LISTENING, PROCESSING
- **ResourceType**: DOCUMENTATION, TUTORIAL, PRACTICE

### Data Classes
- **Question**: Technical interview question with metadata
- **Evaluation**: Response evaluation with score (0-100) and feedback
- **SessionState**: Current state of an interview session
- **Report**: Final interview report with scores and resources
- **Resource**: Learning resource recommendation

### Exceptions
- **InterviewError**: Base exception for all interview system errors
- **AudioCaptureError**: Audio input failure
- **EvaluationTimeoutError**: Evaluation timeout
- **QuestionGenerationError**: Question generation failure

## Testing

The project uses both unit tests and property-based tests:

```bash
# Run all tests
pytest tests/

# Run only property-based tests
pytest tests/test_properties.py

# Run only unit tests
pytest tests/test_models.py
```

### Property-Based Testing
- Framework: Hypothesis
- Minimum 100 iterations per property test
- Tests verify universal correctness properties across all inputs

## Requirements

- Python 3.8+
- pytest >= 7.4.0
- hypothesis >= 6.92.0
- boto3 >= 1.34.0 (for AWS Bedrock integration)
- python-dotenv >= 1.0.0

## Installation

```bash
pip install -r requirements.txt
```

## Development Status

✅ Task 1: Project structure and core data models - COMPLETE
- Core enums defined
- Data classes implemented with validation
- Exception classes created
- Testing framework configured
- Property test for score range validation (Property 10) - PASSED
