import numpy as np
from collections import deque
from scipy.stats import ks_2samp

WINDOW_SIZE = 50
DRIFT_THRESHOLD = 0.05  # p-value threshold

# reference window (first 50 requests — baseline)
reference_window = deque(maxlen=WINDOW_SIZE)
current_window = deque(maxlen=WINDOW_SIZE)

baseline_set = False


def add_response_length(response: str):
    """Track response length as drift signal."""
    length = len(response.split())
    
    if len(reference_window) < WINDOW_SIZE:
        reference_window.append(length)
    else:
        current_window.append(length)


def detect_drift() -> dict:
    """
    Kolmogorov-Smirnov test to detect distribution drift
    between reference and current response lengths.
    """
    if len(reference_window) < WINDOW_SIZE or len(current_window) < 10:
        return {
            "drift_detected": False,
            "reason": "Not enough data",
            "p_value": None,
            "reference_mean": round(float(np.mean(reference_window)), 2) if reference_window else 0,
            "current_mean": 0
        }

    stat, p_value = ks_2samp(list(reference_window), list(current_window))

    drift_detected = p_value < DRIFT_THRESHOLD

    return {
        "drift_detected": drift_detected,
        "reason": f"KS test p-value: {p_value:.4f} ({'drift detected' if drift_detected else 'stable'})",
        "p_value": round(float(p_value), 4),
        "reference_mean": round(float(np.mean(reference_window)), 2),
        "current_mean": round(float(np.mean(current_window)), 2) if current_window else 0
    }