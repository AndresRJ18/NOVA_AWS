"""Tests for latency tracking functionality."""

import pytest
from datetime import datetime, timedelta
from mock_interview_coach.voice_interface.latency_tracker import LatencyTracker
from mock_interview_coach.models import LatencyMetric


class TestLatencyTrackerInitialization:
    """Test LatencyTracker initialization."""
    
    def test_initialization_with_session_id(self):
        """Test tracker initializes with session ID."""
        tracker = LatencyTracker(session_id="test-session")
        
        assert tracker.session_id == "test-session"
        assert tracker.metrics == []
    
    def test_initialization_creates_empty_metrics_list(self):
        """Test tracker starts with empty metrics list."""
        tracker = LatencyTracker(session_id="test-session")
        
        assert len(tracker.metrics) == 0


class TestLatencyMeasurement:
    """Test latency measurement with context manager."""
    
    def test_measure_context_manager_records_latency(self):
        """Test context manager measures and records latency."""
        tracker = LatencyTracker(session_id="test-session")
        
        with tracker.measure("stt") as metric:
            # Simulate some work
            pass
        
        # Verify metric was recorded
        assert len(tracker.metrics) == 1
        assert tracker.metrics[0].operation == "stt"
        assert tracker.metrics[0].latency_ms >= 0
        assert tracker.metrics[0].session_id == "test-session"
        assert tracker.metrics[0].success is True
    
    def test_measure_records_failure_on_exception(self):
        """Test context manager records failure when exception occurs."""
        tracker = LatencyTracker(session_id="test-session")
        
        with pytest.raises(ValueError):
            with tracker.measure("tts") as metric:
                raise ValueError("Test error")
        
        # Verify metric was recorded with failure
        assert len(tracker.metrics) == 1
        assert tracker.metrics[0].operation == "tts"
        assert tracker.metrics[0].success is False
    
    def test_measure_multiple_operations(self):
        """Test measuring multiple operations."""
        tracker = LatencyTracker(session_id="test-session")
        
        with tracker.measure("stt"):
            pass
        
        with tracker.measure("tts"):
            pass
        
        with tracker.measure("end_to_end"):
            pass
        
        # Verify all metrics were recorded
        assert len(tracker.metrics) == 3
        assert tracker.metrics[0].operation == "stt"
        assert tracker.metrics[1].operation == "tts"
        assert tracker.metrics[2].operation == "end_to_end"


class TestManualMetricRecording:
    """Test manual metric recording."""
    
    def test_record_metric_creates_metric(self):
        """Test manually recording a metric."""
        tracker = LatencyTracker(session_id="test-session")
        
        metric = tracker.record_metric(
            operation="stt",
            latency_ms=150,
            success=True
        )
        
        assert metric.operation == "stt"
        assert metric.latency_ms == 150
        assert metric.success is True
        assert metric.session_id == "test-session"
        assert len(tracker.metrics) == 1
    
    def test_record_metric_with_custom_timestamp(self):
        """Test recording metric with custom timestamp."""
        tracker = LatencyTracker(session_id="test-session")
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        
        metric = tracker.record_metric(
            operation="tts",
            latency_ms=200,
            success=True,
            timestamp=custom_time
        )
        
        assert metric.timestamp == custom_time
    
    def test_record_metric_defaults_to_current_time(self):
        """Test recording metric defaults to current time."""
        tracker = LatencyTracker(session_id="test-session")
        before = datetime.utcnow()
        
        metric = tracker.record_metric(
            operation="stt",
            latency_ms=100,
            success=True
        )
        
        after = datetime.utcnow()
        
        assert before <= metric.timestamp <= after


class TestMetricRetrieval:
    """Test retrieving metrics."""
    
    def test_get_metrics_returns_copy(self):
        """Test get_metrics returns a copy of metrics list."""
        tracker = LatencyTracker(session_id="test-session")
        
        tracker.record_metric("stt", 100, True)
        tracker.record_metric("tts", 200, True)
        
        metrics = tracker.get_metrics()
        
        # Verify it's a copy
        assert metrics is not tracker.metrics
        assert len(metrics) == 2
    
    def test_get_average_latency_for_operation(self):
        """Test calculating average latency for specific operation."""
        tracker = LatencyTracker(session_id="test-session")
        
        tracker.record_metric("stt", 100, True)
        tracker.record_metric("stt", 200, True)
        tracker.record_metric("tts", 300, True)
        
        avg_stt = tracker.get_average_latency("stt")
        
        assert avg_stt == 150.0  # (100 + 200) / 2
    
    def test_get_average_latency_for_all_operations(self):
        """Test calculating average latency for all operations."""
        tracker = LatencyTracker(session_id="test-session")
        
        tracker.record_metric("stt", 100, True)
        tracker.record_metric("tts", 200, True)
        tracker.record_metric("end_to_end", 300, True)
        
        avg_all = tracker.get_average_latency()
        
        assert avg_all == 200.0  # (100 + 200 + 300) / 3
    
    def test_get_average_latency_returns_none_for_no_metrics(self):
        """Test average latency returns None when no metrics."""
        tracker = LatencyTracker(session_id="test-session")
        
        avg = tracker.get_average_latency("stt")
        
        assert avg is None
    
    def test_get_success_rate_for_operation(self):
        """Test calculating success rate for specific operation."""
        tracker = LatencyTracker(session_id="test-session")
        
        tracker.record_metric("stt", 100, True)
        tracker.record_metric("stt", 200, True)
        tracker.record_metric("stt", 150, False)
        tracker.record_metric("tts", 300, True)
        
        success_rate = tracker.get_success_rate("stt")
        
        assert success_rate == pytest.approx(66.666, rel=0.01)  # 2/3 * 100
    
    def test_get_success_rate_for_all_operations(self):
        """Test calculating success rate for all operations."""
        tracker = LatencyTracker(session_id="test-session")
        
        tracker.record_metric("stt", 100, True)
        tracker.record_metric("tts", 200, False)
        tracker.record_metric("end_to_end", 300, True)
        
        success_rate = tracker.get_success_rate()
        
        assert success_rate == pytest.approx(66.666, rel=0.01)  # 2/3 * 100
    
    def test_get_success_rate_returns_none_for_no_metrics(self):
        """Test success rate returns None when no metrics."""
        tracker = LatencyTracker(session_id="test-session")
        
        rate = tracker.get_success_rate("stt")
        
        assert rate is None


class TestMetricClearing:
    """Test clearing metrics."""
    
    def test_clear_metrics_removes_all_metrics(self):
        """Test clearing metrics removes all collected metrics."""
        tracker = LatencyTracker(session_id="test-session")
        
        tracker.record_metric("stt", 100, True)
        tracker.record_metric("tts", 200, True)
        
        assert len(tracker.metrics) == 2
        
        tracker.clear_metrics()
        
        assert len(tracker.metrics) == 0
    
    def test_clear_metrics_allows_new_recordings(self):
        """Test can record new metrics after clearing."""
        tracker = LatencyTracker(session_id="test-session")
        
        tracker.record_metric("stt", 100, True)
        tracker.clear_metrics()
        tracker.record_metric("tts", 200, True)
        
        assert len(tracker.metrics) == 1
        assert tracker.metrics[0].operation == "tts"


class TestLatencyMetricDataclass:
    """Test LatencyMetric dataclass."""
    
    def test_latency_metric_creation(self):
        """Test creating a LatencyMetric instance."""
        timestamp = datetime.utcnow()
        
        metric = LatencyMetric(
            operation="stt",
            latency_ms=150,
            timestamp=timestamp,
            session_id="test-session",
            success=True
        )
        
        assert metric.operation == "stt"
        assert metric.latency_ms == 150
        assert metric.timestamp == timestamp
        assert metric.session_id == "test-session"
        assert metric.success is True
    
    def test_latency_metric_fields_are_accessible(self):
        """Test all fields of LatencyMetric are accessible."""
        metric = LatencyMetric(
            operation="tts",
            latency_ms=200,
            timestamp=datetime.utcnow(),
            session_id="session-123",
            success=False
        )
        
        # Verify all fields are accessible
        assert hasattr(metric, "operation")
        assert hasattr(metric, "latency_ms")
        assert hasattr(metric, "timestamp")
        assert hasattr(metric, "session_id")
        assert hasattr(metric, "success")
