import json
import re
import uuid
import asyncio

from models.schemas import CorrelatedError, Suggestion, Severity
from config import get_settings

settings = get_settings()


SYSTEM_PROMPT = (
    "You are a senior software engineer and debugging expert. "
    "Analyse production errors from log files together with the relevant source code "
    "and provide precise, actionable fixes. "
    "Severity guide: CRITICAL = data loss / security / crash; "
    "ERROR = functional failure; WARNING = degraded / incorrect behaviour. "
    "Confidence is 0.0–1.0 based on how certain you are about the root cause. "
    "CRITICAL RULE: respond with VALID JSON ONLY. "
    "No markdown, no backticks, no preamble, no explanation outside the JSON object."
)


_model = None

if settings.gemini_api_key:
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        try:
            _model = genai.GenerativeModel(
                model_name=settings.model,
                system_instruction=SYSTEM_PROMPT,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=1024,
                    response_mime_type="application/json",   
                ),
            )
            print(f"[ai_engine] Gemini '{settings.model}' ready (JSON mode)")
        except TypeError:
            _model = genai.GenerativeModel(
                model_name=settings.model,
                system_instruction=SYSTEM_PROMPT,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=1024,
                ),
            )
            print(f"[ai_engine] Gemini '{settings.model}' ready (text mode)")

    except Exception as exc:
        print(f"[ai_engine] Gemini init failed: {exc}")
        _model = None
else:
    print("[ai_engine] No GEMINI_API_KEY set — running in mock mode")



_RESPONSE_SCHEMA = """{
  "severity": "CRITICAL" | "ERROR" | "WARNING",
  "root_cause": "<1-2 sentence technical explanation>",
  "suggestion": "<specific, actionable fix>",
  "fixed_code": "<corrected version of the relevant lines only>",
  "confidence": 0.95
}"""


def _build_prompt(corr: CorrelatedError) -> str:
    return (
        f"Analyse this production error and provide a precise fix.\n\n"
        f"LANGUAGE      : {corr.language}\n"
        f"ERROR TYPE    : {corr.error.exception_type}\n"
        f"LOG LEVEL     : {corr.error.level}\n"
        f"ERROR MESSAGE : {corr.error.message}\n"
        f"SOURCE FILE   : {corr.source_file}\n\n"
        f"CODE CONTEXT (→ marks the error line):\n"
        f"{corr.code_context}\n\n"
        f"Return ONLY this JSON (no backticks, no explanation):\n"
        f"{_RESPONSE_SCHEMA}"
    )



_MOCK_POOL = [
    {
        "severity": "CRITICAL",
        "root_cause": "NullPointerException: the object is not null-checked before method invocation.",
        "suggestion": "Wrap the field access in an Optional or add an explicit null guard.",
        "fixed_code": "if (user != null && user.getName() != null) {\n    return user.getName().length();\n}\nreturn 0;",
        "confidence": 0.94,
    },
    {
        "severity": "ERROR",
        "root_cause": "IndexOutOfBoundsException: list size is not validated before random-access.",
        "suggestion": "Guard the get() call with a size check, or use an iterator / stream.",
        "fixed_code": "if (index >= 0 && index < items.size()) {\n    return items.get(index);\n}\nthrow new IllegalArgumentException(\"Index out of range: \" + index);",
        "confidence": 0.91,
    },
    {
        "severity": "WARNING",
        "root_cause": "Resource not closed in a finally block, causing a potential connection leak.",
        "suggestion": "Use try-with-resources to guarantee the connection is always closed.",
        "fixed_code": "try (Connection conn = dataSource.getConnection()) {\n    // use conn\n}",
        "confidence": 0.87,
    },
    {
        "severity": "ERROR",
        "root_cause": "KeyError: the dictionary key is not guaranteed to exist at runtime.",
        "suggestion": "Use dict.get(key, default) or check 'key in dict' before access.",
        "fixed_code": "name = data.get('name', 'Unknown')",
        "confidence": 0.92,
    },
    {
        "severity": "CRITICAL",
        "root_cause": "ZeroDivisionError: denominator variable can reach 0 under certain inputs.",
        "suggestion": "Add a zero-guard before the division and handle the edge case explicitly.",
        "fixed_code": "if denominator == 0:\n    raise ValueError('Denominator cannot be zero')\nresult = numerator / denominator",
        "confidence": 0.96,
    },
]



def _parse_response(text: str) -> dict:
    """
    Parse Gemini's JSON response with graceful fallbacks.
    Gemini sometimes wraps the JSON in markdown fences despite instructions;
    we strip those and try multiple extraction strategies.
    """
    cleaned = text.strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    # Direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract first {...} block from the text
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {
        "severity": "ERROR",
        "root_cause": "Could not fully parse the AI response.",
        "suggestion": "Review the error message and stack trace manually.",
        "fixed_code": "",
        "confidence": 0.30,
    }



def _to_suggestion(data: dict, corr: CorrelatedError) -> Suggestion:
    sev_str = str(data.get("severity", "ERROR")).upper()
    try:
        severity = Severity(sev_str)
    except ValueError:
        severity = Severity.ERROR

    return Suggestion(
        id=str(uuid.uuid4())[:8],
        severity=severity,
        error_type=corr.error.exception_type,
        source_file=corr.source_file,
        line=corr.line,
        method=corr.method,
        root_cause=data.get("root_cause", ""),
        suggestion=data.get("suggestion", ""),
        fixed_code=data.get("fixed_code", ""),
        confidence=min(1.0, max(0.0, float(data.get("confidence", 0.5)))),
        original_context=corr.code_context,
    )


async def _generate(prompt: str) -> str:
    """Call Gemini; support both async (new SDK) and sync-in-thread (old SDK)."""
    try:
        response = await _model.generate_content_async(prompt)
    except AttributeError:
        # SDK older than ~0.4 — run synchronous call in thread pool
        response = await asyncio.to_thread(_model.generate_content, prompt)
    return response.text


_SEVERITY_ORDER = {"CRITICAL": 0, "ERROR": 1, "WARNING": 2, "INFO": 3}



async def analyze_errors(correlated: list[CorrelatedError]) -> list[Suggestion]:
    """
    Analyse up to settings.max_suggestions correlated errors.
    Returns suggestions sorted CRITICAL-first, then by descending confidence.
    """
    items = correlated[: settings.max_suggestions]

    if not _model:
        suggestions: list[Suggestion] = []
        for i, corr in enumerate(items):
            mock = _MOCK_POOL[i % len(_MOCK_POOL)]
            suggestions.append(_to_suggestion(mock, corr))
        return _sort(suggestions)

    semaphore = asyncio.Semaphore(3)

    async def _call_one(corr: CorrelatedError) -> Suggestion | None:
        async with semaphore:
            try:
                text = await _generate(_build_prompt(corr))
                data = _parse_response(text)
                return _to_suggestion(data, corr)
            except Exception as exc:
                print(f"[ai_engine] Gemini error for {corr.source_file}:{corr.line}: {exc}")
                return None

    results = await asyncio.gather(*[_call_one(c) for c in items])
    suggestions = [s for s in results if s is not None]
    return _sort(suggestions)


def _sort(suggestions: list[Suggestion]) -> list[Suggestion]:
    return sorted(
        suggestions,
        key=lambda s: (_SEVERITY_ORDER.get(s.severity, 9), -s.confidence),
    )
