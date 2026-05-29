import time
import uuid
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from proxy.streaming.redis_client import log_event
import os

load_dotenv()

app = FastAPI(title="LLMeter", version="0.1.0")

PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gpt-3.5-turbo")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gpt-3.5-turbo-instruct")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/v1/chat/completions"


class ChatRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    messages: list
    model: str = PRIMARY_MODEL
    temperature: float = 0.7
    max_tokens: int = 512


class ProxyResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    request_id: str
    response: str
    model_used: str
    latency_ms: float
    fallback_used: bool


async def call_llm(messages: list, model: str) -> tuple[str, float]:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
    }

    start = time.time()
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(OPENAI_BASE_URL, json=payload, headers=headers)
        res.raise_for_status()

    latency_ms = (time.time() - start) * 1000
    content = res.json()["choices"][0]["message"]["content"]
    return content, latency_ms


@app.post("/chat", response_model=ProxyResponse)
async def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())
    fallback_used = False
    prompt = request.messages[-1]["content"] if request.messages else ""

    try:
        response, latency_ms = await call_llm(request.messages, PRIMARY_MODEL)
        model_used = PRIMARY_MODEL

    except Exception as e:
        print(f"Primary model failed: {e}. Switching to fallback.")
        try:
            response, latency_ms = await call_llm(request.messages, FALLBACK_MODEL)
            model_used = FALLBACK_MODEL
            fallback_used = True
        except Exception as fallback_error:
            raise HTTPException(status_code=503, detail=f"Both models failed: {fallback_error}")

    # Log event to Redis Stream
    log_event(
        request_id=request_id,
        prompt=prompt,
        response=response,
        model=model_used,
        latency_ms=round(latency_ms, 2),
        fallback_used=fallback_used
    )

    return ProxyResponse(
        request_id=request_id,
        response=response,
        model_used=model_used,
        latency_ms=round(latency_ms, 2),
        fallback_used=fallback_used
    )


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/events")
async def get_events():
    from proxy.streaming.redis_client import read_recent_events, get_stream_length
    events = read_recent_events(count=50)
    return {
        "total_events": get_stream_length(),
        "recent_events": events
    }