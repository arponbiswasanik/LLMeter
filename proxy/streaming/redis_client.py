import redis
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STREAM_NAME = "llmeter:events"

r = redis.from_url(REDIS_URL, decode_responses=True)


def log_event(
    request_id: str,
    prompt: str,
    response: str,
    model: str,
    latency_ms: float,
    fallback_used: bool,
    flagged: bool = False,
    flag_reason: str = None
):
    """Log a single LLM request/response event to Redis Stream."""
    event = {
        "request_id": request_id,
        "timestamp": str(time.time()),
        "prompt": prompt[:500],        # truncate long prompts
        "response": response[:500],    # truncate long responses
        "model": model,
        "latency_ms": str(latency_ms),
        "fallback_used": str(fallback_used),
        "flagged": str(flagged),
        "flag_reason": flag_reason or ""
    }
    r.xadd(STREAM_NAME, event)


def read_recent_events(count: int = 50) -> list:
    """Read the most recent N events from the stream."""
    events = r.xrevrange(STREAM_NAME, count=count)
    result = []
    for event_id, data in events:
        data["event_id"] = event_id
        result.append(data)
    return result


def get_stream_length() -> int:
    """Return total number of events logged."""
    return r.xlen(STREAM_NAME)