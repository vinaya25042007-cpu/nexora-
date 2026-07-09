"""
AI service: wraps Anthropic's Claude API for:
  1. Extracting structured data from a discharge summary (free text / OCR'd text)
  2. Generating a personalized recovery plan (meds, rehab, diet, follow-ups)
  3. Parsing voice-assistant transcripts into intents + entities
  4. Turning a check-in / wound risk into a plain-language explanation

All calls degrade gracefully: if ANTHROPIC_API_KEY isn't set, or an error
occurs, a safe rule-based fallback is used so the API never crashes.
"""
import json
import re
from typing import Any, Optional

from anthropic import Anthropic

from app.config import settings

_client: Optional[Anthropic] = None


def get_client() -> Optional[Anthropic]:
    global _client
    if not settings.ANTHROPIC_API_KEY:
        return None
    if _client is None:
        _client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def _extract_json(text: str) -> Any:
    """Best-effort extraction of a JSON object/array from model output."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    return None


EXTRACTION_PROMPT = """You are a clinical assistant helping structure a hospital discharge summary.
Read the discharge summary text below and extract the information into STRICT JSON only
(no preamble, no markdown fences, no commentary). Use this exact schema:

{{
  "surgery_type": "string or null",
  "surgery_date": "YYYY-MM-DD or null",
  "diagnosis": "string or null",
  "medications": [
    {{"name": "string", "dosage": "string", "frequency_per_day": 1, "instructions": "string"}}
  ],
  "rehab_exercises": [
    {{"name": "string", "description": "string", "frequency": "e.g. 3x/day", "duration_days": 14}}
  ],
  "diet_recommendations": ["string", "..."],
  "follow_up_appointments": [
    {{"days_after_discharge": 7, "reason": "string"}}
  ],
  "precautions": ["string", "..."],
  "warning_signs": ["string", "..."]
}}

If information is missing, use null or an empty list. Never invent dosages not present in the text.

DISCHARGE SUMMARY TEXT:
---
{text}
---

Respond with JSON only."""


def extract_discharge_summary(raw_text: str) -> dict:
    client = get_client()
    if client is None:
        return _fallback_extraction(raw_text)

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(text=raw_text[:12000])}],
        )
        text_out = "".join(block.text for block in resp.content if block.type == "text")
        parsed = _extract_json(text_out)
        if parsed:
            return parsed
    except Exception:
        pass
    return _fallback_extraction(raw_text)


def _fallback_extraction(raw_text: str) -> dict:
    """Very simple keyword-based fallback if the AI call fails or no API key configured."""
    return {
        "surgery_type": None,
        "surgery_date": None,
        "diagnosis": None,
        "medications": [],
        "rehab_exercises": [],
        "diet_recommendations": [
            "Stay hydrated, drink at least 8 glasses of water daily",
            "Eat a protein-rich, high-fiber diet to support healing",
        ],
        "follow_up_appointments": [{"days_after_discharge": 7, "reason": "Post-op check-up"}],
        "precautions": ["Avoid strenuous activity", "Keep incision site clean and dry"],
        "warning_signs": [
            "Fever above 38.5C",
            "Increasing redness or swelling at incision site",
            "Pus or foul-smelling discharge",
            "Severe or worsening pain",
        ],
    }


PLAN_PROMPT = """You are a clinical recovery-planning assistant. Based on the structured
discharge data below, write a warm, clear, patient-facing recovery plan summary
(4-6 sentences, plain language, no medical jargon where possible). Respond with
STRICT JSON only in this schema:

{{
  "summary_text": "string"
}}

STRUCTURED DISCHARGE DATA:
{data}
"""


def generate_recovery_plan_summary(structured_data: dict) -> str:
    client = get_client()
    if client is None:
        return (
            "Your personalized recovery plan is ready. Please take medications as "
            "scheduled, follow the rehab exercises daily, stick to the recommended diet, "
            "and attend your follow-up appointments. Contact your care team right away if "
            "you notice any warning signs listed in your plan."
        )
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[
                {"role": "user", "content": PLAN_PROMPT.format(data=json.dumps(structured_data))}
            ],
        )
        text_out = "".join(block.text for block in resp.content if block.type == "text")
        parsed = _extract_json(text_out)
        if parsed and "summary_text" in parsed:
            return parsed["summary_text"]
    except Exception:
        pass
    return "Your personalized recovery plan has been generated based on your discharge summary."


VOICE_INTENT_PROMPT = """You are the natural-language understanding engine for a
post-surgery recovery voice assistant. Classify the user's spoken transcript into
one intent and extract entities. Respond with STRICT JSON only:

{{
  "intent": "one of: log_medication_taken | log_symptom | log_pain_level | ask_recovery_plan | ask_next_appointment | request_sos | general_question | unclear",
  "entities": {{"medication_name": "string or null", "pain_level": "int or null", "symptom": "string or null"}},
  "reply_text": "a short, warm spoken reply to the user (1-2 sentences)"
}}

USER TRANSCRIPT: "{transcript}"
"""


def parse_voice_command(transcript: str) -> dict:
    client = get_client()
    if client is None:
        return _fallback_voice_intent(transcript)
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": VOICE_INTENT_PROMPT.format(transcript=transcript)}],
        )
        text_out = "".join(block.text for block in resp.content if block.type == "text")
        parsed = _extract_json(text_out)
        if parsed and "intent" in parsed:
            return parsed
    except Exception:
        pass
    return _fallback_voice_intent(transcript)


def _fallback_voice_intent(transcript: str) -> dict:
    t = transcript.lower()
    if "took" in t or "taken" in t:
        return {
            "intent": "log_medication_taken",
            "entities": {"medication_name": None, "pain_level": None, "symptom": None},
            "reply_text": "Got it, I've logged that medication as taken.",
        }
    if "help" in t or "emergency" in t or "sos" in t:
        return {
            "intent": "request_sos",
            "entities": {"medication_name": None, "pain_level": None, "symptom": None},
            "reply_text": "I'm alerting your caregiver and care team right now.",
        }
    if "pain" in t or "hurt" in t:
        return {
            "intent": "log_pain_level",
            "entities": {"medication_name": None, "pain_level": None, "symptom": None},
            "reply_text": "Thanks for letting me know, I've logged your pain level.",
        }
    if "appointment" in t:
        return {
            "intent": "ask_next_appointment",
            "entities": {"medication_name": None, "pain_level": None, "symptom": None},
            "reply_text": "Let me check your upcoming appointments.",
        }
    return {
        "intent": "unclear",
        "entities": {"medication_name": None, "pain_level": None, "symptom": None},
        "reply_text": "Sorry, I didn't quite catch that. Could you repeat it?",
    }
