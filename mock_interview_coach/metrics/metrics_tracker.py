"""Metrics Tracker for interview statistics."""

import json
import os
from typing import Dict, List
from datetime import datetime
from collections import defaultdict

from mock_interview_coach.models import Role, Level, Language, TechnicalArea


class MetricsTracker:
    """Tracks and aggregates interview metrics."""
    
    def __init__(self, storage_path: str = "metrics_data.json"):
        """Initialize the Metrics Tracker.
        
        Args:
            storage_path: Path to store metrics data
        """
        self._storage_path = storage_path
        self._metrics = self._load_metrics()
    
    def record_session(
        self,
        role: Role,
        level: Level,
        language: Language,
        overall_score: int,
        area_scores: Dict[TechnicalArea, int],
        questions_count: int
    ) -> None:
        """Record a completed interview session.
        
        Args:
            role: Interview role
            level: Experience level
            language: Interview language
            overall_score: Overall score (0-100)
            area_scores: Scores by technical area
            questions_count: Number of questions answered
        """
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "role": role.value,
            "level": level.value,
            "language": language.value,
            "overall_score": overall_score,
            "area_scores": {area.value: score for area, score in area_scores.items()},
            "questions_count": questions_count
        }
        
        self._metrics["sessions"].append(session_data)
        self._metrics["total_interviews"] += 1
        self._metrics["total_questions"] += questions_count
        
        # Update role stats
        role_key = role.value
        if role_key not in self._metrics["by_role"]:
            self._metrics["by_role"][role_key] = {
                "count": 0,
                "total_score": 0,
                "average_score": 0
            }
        
        self._metrics["by_role"][role_key]["count"] += 1
        self._metrics["by_role"][role_key]["total_score"] += overall_score
        self._metrics["by_role"][role_key]["average_score"] = (
            self._metrics["by_role"][role_key]["total_score"] / 
            self._metrics["by_role"][role_key]["count"]
        )
        
        # Update area difficulty stats
        for area, score in area_scores.items():
            area_key = area.value
            if area_key not in self._metrics["area_difficulty"]:
                self._metrics["area_difficulty"][area_key] = {
                    "count": 0,
                    "total_score": 0,
                    "average_score": 0,
                    "fail_count": 0
                }
            
            self._metrics["area_difficulty"][area_key]["count"] += 1
            self._metrics["area_difficulty"][area_key]["total_score"] += score
            self._metrics["area_difficulty"][area_key]["average_score"] = (
                self._metrics["area_difficulty"][area_key]["total_score"] /
                self._metrics["area_difficulty"][area_key]["count"]
            )
            
            if score < 60:
                self._metrics["area_difficulty"][area_key]["fail_count"] += 1
        
        self._save_metrics()
    
    def get_global_stats(self) -> Dict:
        """Get global statistics.
        
        Returns:
            Dictionary with global stats
        """
        if self._metrics["total_interviews"] == 0:
            return self._get_mock_stats()
        
        # Calculate overall average
        total_score = sum(
            session["overall_score"] 
            for session in self._metrics["sessions"]
        )
        average_score = total_score / self._metrics["total_interviews"]
        
        # Find most difficult area
        most_difficult = None
        lowest_score = 100
        
        for area, stats in self._metrics["area_difficulty"].items():
            if stats["average_score"] < lowest_score:
                lowest_score = stats["average_score"]
                most_difficult = area
        
        # Score distribution
        score_ranges = {"0-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for session in self._metrics["sessions"]:
            score = session["overall_score"]
            if score <= 40:
                score_ranges["0-40"] += 1
            elif score <= 60:
                score_ranges["41-60"] += 1
            elif score <= 80:
                score_ranges["61-80"] += 1
            else:
                score_ranges["81-100"] += 1
        
        return {
            "total_interviews": self._metrics["total_interviews"],
            "total_questions": self._metrics["total_questions"],
            "average_score": round(average_score, 1),
            "most_difficult_area": most_difficult,
            "most_difficult_score": round(lowest_score, 1),
            "by_role": self._metrics["by_role"],
            "score_distribution": score_ranges,
            "recent_sessions": self._metrics["sessions"][-10:]
        }
    
    def get_area_stats(self) -> Dict:
        """Get statistics by technical area.
        
        Returns:
            Dictionary with area statistics
        """
        if not self._metrics["area_difficulty"]:
            return {}
        
        return {
            area: {
                "average_score": round(stats["average_score"], 1),
                "total_attempts": stats["count"],
                "fail_rate": round((stats["fail_count"] / stats["count"]) * 100, 1) if stats["count"] > 0 else 0
            }
            for area, stats in self._metrics["area_difficulty"].items()
        }
    
    def _load_metrics(self) -> Dict:
        """Load metrics from storage."""
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "total_interviews": 0,
            "total_questions": 0,
            "sessions": [],
            "by_role": {},
            "area_difficulty": {}
        }
    
    def _save_metrics(self) -> None:
        """Save metrics to storage."""
        try:
            with open(self._storage_path, 'w') as f:
                json.dump(self._metrics, f, indent=2)
        except Exception as e:
            print(f"Failed to save metrics: {e}")
    
    def _get_mock_stats(self) -> Dict:
        """Get mock statistics for demo purposes."""
        return {
            "total_interviews": 134,
            "total_questions": 987,
            "average_score": 72.3,
            "most_difficult_area": "kubernetes",
            "most_difficult_score": 58.2,
            "by_role": {
                "cloud_engineer": {"count": 56, "average_score": 74.5},
                "devops_engineer": {"count": 48, "average_score": 71.8},
                "ml_engineer": {"count": 30, "average_score": 69.2}
            },
            "score_distribution": {
                "0-40": 12,
                "41-60": 28,
                "61-80": 54,
                "81-100": 40
            },
            "recent_sessions": []
        }
