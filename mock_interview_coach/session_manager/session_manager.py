"""Session Manager implementation with adaptive difficulty."""

import uuid
from datetime import datetime
from typing import Optional, Dict

from mock_interview_coach.models import (
    Role,
    Level,
    Language,
    SessionState,
    Question,
    Evaluation,
    Report,
    AudioState
)
from mock_interview_coach.question_generator import QuestionGenerator
from mock_interview_coach.evaluator import Evaluator
from mock_interview_coach.report_generator import ReportGenerator
from mock_interview_coach.difficulty_adjuster import DifficultyAdjuster
from mock_interview_coach.metrics import MetricsTracker


class SessionManager:
    """Orchestrates interview sessions with adaptive difficulty."""
    
    def __init__(self, use_adaptive_mode: bool = True):
        """Initialize the Session Manager.
        
        Args:
            use_adaptive_mode: If True, use AI-generated adaptive questions
        """
        self._question_generator = QuestionGenerator(use_dynamic_generation=use_adaptive_mode)
        self._evaluator = Evaluator()
        self._report_generator = ReportGenerator()
        self._difficulty_adjuster = DifficultyAdjuster()
        self._metrics_tracker = MetricsTracker()
        self._use_adaptive_mode = use_adaptive_mode
        
        # Current session
        self._current_session: Optional[SessionState] = None
    
    def start_session(
        self,
        role: Role,
        level: Level,
        language: Language,
        demo_mode: bool = False
    ) -> str:
        """Start a new interview session.
        
        Args:
            role: Technical role
            level: Experience level
            language: Interview language
            demo_mode: Whether to use demo mode
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Configure question generator
        self._question_generator.configure(role, level, language, demo_mode)
        
        # Create session state
        self._current_session = SessionState(
            session_id=session_id,
            role=role,
            level=level,
            language=language,
            demo_mode=demo_mode,
            current_question_index=0,
            questions=[],
            responses=[],
            evaluations=[],
            is_paused=False,
            audio_state=AudioState.IDLE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return session_id
    
    def get_next_question(self, session_id: str) -> Optional[Question]:
        """Get the next question with adaptive difficulty.
        
        Args:
            session_id: Session ID
            
        Returns:
            Next question or None if no more questions
        """
        if not self._current_session or self._current_session.session_id != session_id:
            return None
        
        if self._current_session.is_paused:
            return None
        
        # Check if we've reached the question limit (5-10 questions)
        if len(self._current_session.questions) >= 10:
            return None
        
        # Use adaptive mode if enabled and we have evaluation history
        if self._use_adaptive_mode and len(self._current_session.evaluations) >= 1:
            # Analyze performance
            performance = self._difficulty_adjuster.analyze_performance(
                self._current_session.evaluations
            )

            # Get difficulty hint
            difficulty_hint = self._difficulty_adjuster.get_next_difficulty_hint(
                self._current_session.evaluations
            )

            # Generate dynamic question
            try:
                question = self._question_generator.generate_dynamic_question(
                    difficulty_hint=difficulty_hint,
                    weak_areas=performance.get('weak_areas', []),
                    previous_questions=self._current_session.questions
                )
            except Exception as e:
                # Fallback to static questions if dynamic generation fails
                print(f"Dynamic generation failed: {e}, falling back to static")
                question = self._question_generator.get_next_question()
        else:
            # Use static questions for first question (or if adaptive mode disabled).
            # If static bank is empty for this role/level combo, generate dynamically.
            question = self._question_generator.get_next_question()
            if question is None and self._use_adaptive_mode:
                try:
                    question = self._question_generator.generate_dynamic_question(
                        difficulty_hint="same",
                        weak_areas=[],
                        previous_questions=self._current_session.questions
                    )
                except Exception as e:
                    print(f"Dynamic generation failed for first question: {e}")
                    question = None
        
        if question:
            self._current_session.questions.append(question)
            self._current_session.updated_at = datetime.now()
        
        return question
    
    def get_performance_analysis(self, session_id: str) -> Optional[dict]:
        """Get current performance analysis.
        
        Args:
            session_id: Session ID
            
        Returns:
            Performance analysis dictionary or None
        """
        if not self._current_session or self._current_session.session_id != session_id:
            return None
        
        if not self._current_session.evaluations:
            return None
        
        return self._difficulty_adjuster.analyze_performance(
            self._current_session.evaluations
        )
    
    def submit_response(self, session_id: str, response: str) -> Evaluation:
        """Submit a response and get feedback.
        
        Args:
            session_id: Session ID
            response: User's response
            
        Returns:
            Evaluation with feedback
        """
        if not self._current_session or self._current_session.session_id != session_id:
            raise ValueError("Invalid session ID")
        
        if not self._current_session.questions:
            raise ValueError("No question to respond to")
        
        # Get the current question
        current_question = self._current_session.questions[-1]
        
        # Evaluate the response
        evaluation = self._evaluator.evaluate_response(
            current_question,
            response,
            self._current_session.language
        )
        
        # Store response and evaluation
        self._current_session.responses.append(response)
        self._current_session.evaluations.append(evaluation)
        self._current_session.current_question_index += 1
        self._current_session.updated_at = datetime.now()
        
        return evaluation
    
    def end_session(self, session_id: str) -> Report:
        """End the session and generate report.
        
        Args:
            session_id: Session ID
            
        Returns:
            Final report
        """
        if not self._current_session or self._current_session.session_id != session_id:
            raise ValueError("Invalid session ID")
        
        # Generate report
        report = self._report_generator.generate_report(
            self._current_session,
            self._current_session.language
        )
        
        # Record metrics
        self._metrics_tracker.record_session(
            role=self._current_session.role,
            level=self._current_session.level,
            language=self._current_session.language,
            overall_score=report.overall_score,
            area_scores=report.area_scores,
            questions_count=len(self._current_session.questions)
        )
        
        return report
    
    def get_global_metrics(self) -> Dict:
        """Get global metrics.
        
        Returns:
            Global statistics dictionary
        """
        return self._metrics_tracker.get_global_stats()
    
    def get_area_metrics(self) -> Dict:
        """Get area-specific metrics.
        
        Returns:
            Area statistics dictionary
        """
        return self._metrics_tracker.get_area_stats()
    
    def pause_session(self, session_id: str) -> None:
        """Pause the session.
        
        Args:
            session_id: Session ID
        """
        if not self._current_session or self._current_session.session_id != session_id:
            raise ValueError("Invalid session ID")
        
        self._current_session.is_paused = True
        self._current_session.updated_at = datetime.now()
    
    def resume_session(self, session_id: str) -> None:
        """Resume the session.
        
        Args:
            session_id: Session ID
        """
        if not self._current_session or self._current_session.session_id != session_id:
            raise ValueError("Invalid session ID")
        
        self._current_session.is_paused = False
        self._current_session.updated_at = datetime.now()
    
    def get_session_state(self, session_id: str) -> Optional[SessionState]:
        """Get the current session state.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session state or None
        """
        if not self._current_session or self._current_session.session_id != session_id:
            return None
        
        return self._current_session
