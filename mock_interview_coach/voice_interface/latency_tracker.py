"""Latency tracking utilities for voice operations.

This module provides utilities for measuring and logging latency metrics
for voice operations (STT, TTS, end-to-end) to enable performance monitoring.
"""

import logging
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager

from mock_interview_coach.models import LatencyMetric

# Configure logger
logger = logging.getLogger(__name__)


class LatencyTracker:
    """Utility class for tracking latency metrics.
    
    This class provides context managers and methods for measuring operation
    latency and creating LatencyMetric instances with proper logging.
    
    Attributes:
        session_id: Session identifier for all metrics
        metrics: List of collected latency metrics
    """
    
    def __init__(self, session_id: str):
        """Initialize latency tracker.
        
        Args:
            session_id: Session identifier for context
        """
        self.session_id = session_id
        self.metrics: List[LatencyMetric] = []
    
    @contextmanager
    def measure(self, operation: str):
        """Context manager for measuring operation latency.
        
        Usage:
            tracker = LatencyTracker(session_id="abc123")
            with tracker.measure("stt") as metric:
                # Perform STT operation
                result = await transcribe_audio(...)
            # metric is automatically populated with latency
        
        Args:
            operation: Operation type ("stt", "tts", "end_to_end")
            
        Yields:
            LatencyMetric: Metric object that will be populated on exit
        """
        start_time = datetime.utcnow()
        success = False
        
        # Create metric placeholder
        metric = LatencyMetric(
            operation=operation,
            latency_ms=0,
            timestamp=start_time,
            session_id=self.session_id,
            success=False
        )
        
        try:
            yield metric
            success = True
        except Exception:
            success = False
            raise
        finally:
            # Calculate latency
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update metric
            metric.latency_ms = latency_ms
            metric.success = success
            
            # Store metric
            self.metrics.append(metric)
            
            # Log metric
            log_level = logging.INFO if success else logging.WARNING
            logger.log(
                log_level,
                f"Latency measurement: operation={operation}, "
                f"latency={latency_ms}ms, success={success}",
                extra={
                    "session_id": self.session_id,
                    "operation": operation,
                    "latency_ms": latency_ms,
                    "success": success,
                    "timestamp": start_time.isoformat()
                }
            )
    
    def record_metric(
        self,
        operation: str,
        latency_ms: int,
        success: bool = True,
        timestamp: Optional[datetime] = None
    ) -> LatencyMetric:
        """Manually record a latency metric.
        
        Use this method when you've already measured latency and want to
        record it without using the context manager.
        
        Args:
            operation: Operation type ("stt", "tts", "end_to_end")
            latency_ms: Measured latency in milliseconds
            success: Whether the operation succeeded
            timestamp: When the measurement was taken (defaults to now)
            
        Returns:
            LatencyMetric: The created metric
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        metric = LatencyMetric(
            operation=operation,
            latency_ms=latency_ms,
            timestamp=timestamp,
            session_id=self.session_id,
            success=success
        )
        
        self.metrics.append(metric)
        
        # Log metric
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"Latency recorded: operation={operation}, "
            f"latency={latency_ms}ms, success={success}",
            extra={
                "session_id": self.session_id,
                "operation": operation,
                "latency_ms": latency_ms,
                "success": success,
                "timestamp": timestamp.isoformat()
            }
        )
        
        return metric
    
    def get_metrics(self) -> List[LatencyMetric]:
        """Get all collected metrics.
        
        Returns:
            List of LatencyMetric objects
        """
        return self.metrics.copy()
    
    def get_average_latency(self, operation: Optional[str] = None) -> Optional[float]:
        """Calculate average latency for an operation type.
        
        Args:
            operation: Operation type to filter by (None for all operations)
            
        Returns:
            Average latency in milliseconds, or None if no metrics
        """
        filtered_metrics = [
            m for m in self.metrics
            if operation is None or m.operation == operation
        ]
        
        if not filtered_metrics:
            return None
        
        total_latency = sum(m.latency_ms for m in filtered_metrics)
        return total_latency / len(filtered_metrics)
    
    def get_success_rate(self, operation: Optional[str] = None) -> Optional[float]:
        """Calculate success rate for an operation type.
        
        Args:
            operation: Operation type to filter by (None for all operations)
            
        Returns:
            Success rate as a percentage (0-100), or None if no metrics
        """
        filtered_metrics = [
            m for m in self.metrics
            if operation is None or m.operation == operation
        ]
        
        if not filtered_metrics:
            return None
        
        successful = sum(1 for m in filtered_metrics if m.success)
        return (successful / len(filtered_metrics)) * 100
    
    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        logger.debug(
            "Cleared latency metrics",
            extra={"session_id": self.session_id}
        )
