"""Difficulty Adjuster for adaptive interview simulation."""

from typing import List, Optional
from mock_interview_coach.models import Evaluation, Level, TechnicalArea


class DifficultyAdjuster:
    """Adjusts interview difficulty based on candidate performance."""
    
    def __init__(self):
        """Initialize the Difficulty Adjuster."""
        self._performance_history: List[int] = []
        self._current_level: Level = Level.JUNIOR
    
    def analyze_performance(self, evaluations: List[Evaluation]) -> dict:
        """Analyze candidate performance and determine next difficulty.
        
        Args:
            evaluations: List of evaluations from the session
            
        Returns:
            Dictionary with performance analysis and recommended difficulty
        """
        if not evaluations:
            return {
                "average_score": 0,
                "trend": "neutral",
                "recommended_level": self._current_level,
                "weak_areas": [],
                "strong_areas": []
            }
        
        # Calculate average score
        scores = [eval.score for eval in evaluations]
        average_score = sum(scores) / len(scores)
        
        # Determine trend (improving, declining, stable)
        trend = self._calculate_trend(scores)
        
        # Identify weak and strong areas
        area_scores = {}
        for eval in evaluations:
            if eval.technical_area not in area_scores:
                area_scores[eval.technical_area] = []
            area_scores[eval.technical_area].append(eval.score)
        
        weak_areas = []
        strong_areas = []
        
        for area, area_score_list in area_scores.items():
            avg = sum(area_score_list) / len(area_score_list)
            if avg < 60:
                weak_areas.append(area)
            elif avg >= 80:
                strong_areas.append(area)
        
        # Recommend difficulty level
        recommended_level = self._recommend_level(average_score, trend)
        
        return {
            "average_score": round(average_score, 1),
            "trend": trend,
            "recommended_level": recommended_level,
            "weak_areas": weak_areas,
            "strong_areas": strong_areas,
            "recent_scores": scores[-3:] if len(scores) >= 3 else scores
        }
    
    def should_increase_difficulty(self, evaluations: List[Evaluation]) -> bool:
        """Determine if difficulty should be increased.
        
        Args:
            evaluations: Recent evaluations
            
        Returns:
            True if difficulty should increase
        """
        if len(evaluations) < 3:
            return False
        
        recent_scores = [eval.score for eval in evaluations[-3:]]
        average = sum(recent_scores) / len(recent_scores)
        
        # Increase difficulty if consistently scoring above 80
        return average >= 80 and all(score >= 75 for score in recent_scores)
    
    def should_decrease_difficulty(self, evaluations: List[Evaluation]) -> bool:
        """Determine if difficulty should be decreased.
        
        Args:
            evaluations: Recent evaluations
            
        Returns:
            True if difficulty should decrease
        """
        if len(evaluations) < 3:
            return False
        
        recent_scores = [eval.score for eval in evaluations[-3:]]
        average = sum(recent_scores) / len(recent_scores)
        
        # Decrease difficulty if consistently scoring below 50
        return average < 50 and all(score < 60 for score in recent_scores)
    
    def get_next_difficulty_hint(self, evaluations: List[Evaluation]) -> str:
        """Get a hint about what difficulty the next question should be.
        
        Args:
            evaluations: Recent evaluations
            
        Returns:
            Difficulty hint: "easier", "same", or "harder"
        """
        if not evaluations:
            return "same"
        
        if self.should_increase_difficulty(evaluations):
            return "harder"
        elif self.should_decrease_difficulty(evaluations):
            return "easier"
        else:
            return "same"
    
    def _calculate_trend(self, scores: List[int]) -> str:
        """Calculate performance trend.
        
        Args:
            scores: List of scores
            
        Returns:
            Trend: "improving", "declining", or "stable"
        """
        if len(scores) < 3:
            return "stable"
        
        # Compare first half vs second half
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
        
        diff = second_half_avg - first_half_avg
        
        if diff > 10:
            return "improving"
        elif diff < -10:
            return "declining"
        else:
            return "stable"
    
    def _recommend_level(self, average_score: float, trend: str) -> Level:
        """Recommend difficulty level based on performance.
        
        Args:
            average_score: Average score
            trend: Performance trend
            
        Returns:
            Recommended level
        """
        # If improving and scoring well, recommend mid level
        if trend == "improving" and average_score >= 75:
            return Level.MID
        
        # If declining or struggling, stay at junior
        if trend == "declining" or average_score < 60:
            return Level.JUNIOR
        
        # If stable and scoring well, recommend mid
        if average_score >= 70:
            return Level.MID
        
        return Level.JUNIOR
