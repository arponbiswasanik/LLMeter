from detoxify import Detoxify
import numpy as np

toxicity_model = Detoxify('original')

def analyze_response(response: str) -> dict:
    """Analyze LLM response for toxicity and quality issues."""
    
    # Toxicity check
    scores = toxicity_model.predict(response)
    is_toxic = scores['toxicity'] > 0.7
    
    # Length check
    word_count = len(response.split())
    too_short = word_count < 3
    
    # Repetition check
    words = response.lower().split()
    unique_ratio = len(set(words)) / len(words) if words else 1
    is_repetitive = unique_ratio < 0.3
    
    flagged = is_toxic or too_short or is_repetitive
    reasons = []
    
    if is_toxic:
        reasons.append(f"Toxic content detected (score: {scores['toxicity']:.2f})")
    if too_short:
        reasons.append("Response too short")
    if is_repetitive:
        reasons.append(f"Repetitive response (unique ratio: {unique_ratio:.2f})")
    
    return {
        "flagged": flagged,
        "reason": "; ".join(reasons),
        "toxicity_score": round(float(scores['toxicity']), 4),
        "word_count": word_count,
        "unique_ratio": round(unique_ratio, 4)
    }