import time
from collections import deque
import numpy as np

# Sliding window — last 100 events
WINDOW_SIZE = 100
latency_window = deque(maxlen=WINDOW_SIZE)
error_window = deque(maxlen=WINDOW_SIZE)

LATENCY_Z_THRESHOLD = 2.5  # Z-score threshold for latency spike
ERROR_RATE_THRESHOLD = 0.1  # 10% error rate threshold


def record_latency(latency_ms: float):
    latency_window.append(latency_ms)


def record_error(is_error: bool):
    error_window.append(1 if is_error else 0)


def detect_latency_spike(latency_ms: float) -> dict:
    """Z-score based latency spike detection."""
    if len(latency_window) < 10:
        return {"anomaly": False, "reason": "Not enough data"}

    mean = np.mean(latency_window)
    std = np.std(latency_window)

    if std == 0:
        return {"anomaly": False, "reason": "No variance"}

    z_score = (latency_ms - mean) / std

    if z_score > LATENCY_Z_THRESHOLD:
        return {
            "anomaly": True,
            "reason": f"Latency spike detected (z-score: {z_score:.2f}, latency: {latency_ms}ms, mean: {mean:.2f}ms)"
        }

    return {"anomaly": False, "reason": "Normal latency"}


def detect_high_error_rate() -> dict:
    """Sliding window error rate detection."""
    if len(error_window) < 10:
        return {"anomaly": False, "reason": "Not enough data"}

    error_rate = sum(error_window) / len(error_window)

    if error_rate > ERROR_RATE_THRESHOLD:
        return {
            "anomaly": True,
            "reason": f"High error rate: {error_rate:.1%}"
        }

    return {"anomaly": False, "reason": f"Normal error rate: {error_rate:.1%}"}


def analyze_event(latency_ms: float, is_error: bool) -> dict:
    """Full anomaly analysis for a single event."""
    record_latency(latency_ms)
    record_error(is_error)

    latency_check = detect_latency_spike(latency_ms)
    error_check = detect_high_error_rate()

    anomalies = []
    if latency_check["anomaly"]:
        anomalies.append(latency_check["reason"])
    if error_check["anomaly"]:
        anomalies.append(error_check["reason"])

    return {
        "anomaly_detected": len(anomalies) > 0,
        "anomalies": anomalies,
        "current_latency_ms": latency_ms,
        "window_mean_latency": round(float(np.mean(latency_window)), 2) if latency_window else 0,
        "current_error_rate": round(sum(error_window) / len(error_window), 4) if error_window else 0
    }