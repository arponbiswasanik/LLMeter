import re
from presidio_analyzer import AnalyzerEngine

#initialize PII analyzer
pii_analyzer = AnalyzerEngine()

#common prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore (all |previous |above |prior )?instructions",
    r"disregard (all |previous |above |prior )?instructions",
    r"forget (all |previous |above |prior )?instructions",
    r"you are now",
    r"act as (a |an )?",
    r"pretend (you are|to be)",
    r"jailbreak",
    r"dan mode",
    r"developer mode",
    r"system prompt",
    r"bypass (your |all )?(restrictions|guidelines|rules)",
    r"do anything now",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_prompt_injection(text: str) -> tuple[bool, str]:
    """Check if text contains prompt injection attempts."""
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True, f"Prompt injection pattern detected: '{pattern.pattern}'"
    return False, ""


def detect_pii(text: str) -> tuple[bool, str]:
    """Check if text contains sensitive PII using Microsoft Presidio."""
    results = pii_analyzer.analyze(text=text, language="en")
    
    # Only flag actually sensitive PII types
    SENSITIVE_ENTITIES = {
        "EMAIL_ADDRESS",
        "PHONE_NUMBER", 
        "CREDIT_CARD",
        "US_SSN",
        "IBAN_CODE",
        "MEDICAL_LICENSE",
        "US_PASSPORT",
        "US_DRIVER_LICENSE",
    }
    
    sensitive_results = [r for r in results if r.entity_type in SENSITIVE_ENTITIES]
    
    if sensitive_results:
        entities = list(set([r.entity_type for r in sensitive_results]))
        return True, f"Sensitive PII detected: {', '.join(entities)}"
    return False, ""


def analyze_request(prompt: str) -> dict:
    """
    Full request analysis pipeline.
    Returns analysis result with flagged status and reason.
    """
    # check prompt injection
    injected, injection_reason = detect_prompt_injection(prompt)
    if injected:
        return {
            "flagged": True,
            "reason": injection_reason,
            "threat_type": "prompt_injection"
        }

    #check PII
    has_pii, pii_reason = detect_pii(prompt)
    if has_pii:
        return {
            "flagged": True,
            "reason": pii_reason,
            "threat_type": "pii_detected"
        }

    return {
        "flagged": False,
        "reason": "",
        "threat_type": None
    }