import os
from dotenv import load_dotenv

load_dotenv()

PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "llama-3.1-8b-instant")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "llama-3.3-70b-versatile")
LATENCY_THRESHOLD_MS = float(os.getenv("LATENCY_THRESHOLD_MS", 3000))
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", 0.1))

#recovery state
recovery_state = {
    "using_fallback": False,
    "reason": "",
    "incident_count": 0,
    "incidents": []
}


def get_active_model() -> str:
    """Return currently active model based on recovery state."""
    if recovery_state["using_fallback"]:
        return FALLBACK_MODEL
    return PRIMARY_MODEL


def trigger_fallback(reason: str):
    """Switch to fallback model and log incident."""
    if not recovery_state["using_fallback"]:
        recovery_state["using_fallback"] = True
        recovery_state["reason"] = reason
        recovery_state["incident_count"] += 1
        recovery_state["incidents"].append({
            "incident_id": recovery_state["incident_count"],
            "reason": reason,
            "action": f"Switched to fallback model: {FALLBACK_MODEL}"
        })
        print(f"🔴 INCIDENT #{recovery_state['incident_count']}: {reason}")
        print(f"🔄 Switching to fallback: {FALLBACK_MODEL}")


def restore_primary():
    """Switch back to primary model."""
    if recovery_state["using_fallback"]:
        recovery_state["using_fallback"] = False
        recovery_state["reason"] = ""
        print(f"🟢 Primary model restored: {PRIMARY_MODEL}")


def evaluate_and_recover(latency_ms: float, error_rate: float):
    """
    Evaluate current metrics and trigger fallback or restore primary.
    Called after every request.
    """
    if latency_ms > LATENCY_THRESHOLD_MS:
        trigger_fallback(f"Latency too high: {latency_ms}ms > {LATENCY_THRESHOLD_MS}ms threshold")
    elif error_rate > ERROR_RATE_THRESHOLD:
        trigger_fallback(f"Error rate too high: {error_rate:.1%} > {ERROR_RATE_THRESHOLD:.1%} threshold")
    else:
        restore_primary()


def get_recovery_status() -> dict:
    """Return current recovery state for dashboard."""
    return {
        "status": "degraded" if recovery_state["using_fallback"] else "healthy",
        "active_model": get_active_model(),
        "using_fallback": recovery_state["using_fallback"],
        "reason": recovery_state["reason"],
        "total_incidents": recovery_state["incident_count"],
        "incident_log": recovery_state["incidents"]
    }