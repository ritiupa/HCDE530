"""
language_analysis.py
--------------------
Takes a list of transcript segments and finds friction moments:
hesitation phrases, confusion signals, and navigation problems.

Two approaches run in parallel:
1. Local pattern matching -- fast, no API cost, catches common friction phrases.
2. Mistral via HuggingFace Inference API -- catches subtler signals and adds context.

Returns an enriched list of segments with friction flags added.
"""

import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

FRICTION_PATTERNS = [
    r"\bwhere\b.{0,20}\bfind\b",
    r"\bdon.t know\b",
    r"\bnot sure\b",
    r"\bexpected\b",
    r"\bconfused\b",
    r"\bwhat does\b",
    r"\bwhy (is|does|would)\b",
    r"\bhow do I\b",
    r"\bthat.s weird\b",
    r"\bwait\b",
    r"\bhmm+\b",
    r"\buh+\b",
    r"\bum+\b",
    r"\bnot (clear|obvious|intuitive)\b",
    r"\bi (guess|suppose)\b",
    r"\bmaybe\b.{0,15}\btry\b",
    r"\bnothing happened\b",
    r"\bdoesn.t work\b",
    r"\bbroken\b",
    r"\bback\b.{0,10}\btry\b",
]

HEURISTIC_MAP = {
    "navigation": "H6: Recognition rather than recall",
    "feedback": "H1: Visibility of system status",
    "error": "H9: Help users recognize and recover from errors",
    "confusion": "H2: Match between system and real world",
    "expectation": "H4: Consistency and standards",
    "control": "H3: User control and freedom",
    "general": "H10: Help and documentation",
}


def _classify_friction_type(pattern: str) -> str:
    if any(kw in pattern for kw in ["find", "where", "how do"]):
        return "navigation"
    if any(kw in pattern for kw in ["expected", "consistency"]):
        return "expectation"
    if any(kw in pattern for kw in ["confused", "weird", "what does"]):
        return "confusion"
    if any(kw in pattern for kw in ["doesn.t work", "broken", "nothing happened"]):
        return "error"
    return "general"


def flag_friction_locally(segments: list[dict]) -> list[dict]:
    """Fast local pass: check each segment against friction phrase patterns."""
    flagged = []
    for seg in segments:
        text = seg["text"].lower()
        is_friction = False
        friction_type = "general"

        for pattern in FRICTION_PATTERNS:
            if re.search(pattern, text):
                is_friction = True
                friction_type = _classify_friction_type(pattern)
                break

        flagged.append({
            **seg,
            "friction_flag": is_friction,
            "friction_type": friction_type if is_friction else None,
            "heuristic": HEURISTIC_MAP.get(friction_type) if is_friction else None,
        })

    return flagged


def analyze_with_mistral(segments: list[dict]) -> list[dict]:
    """
    Send friction-flagged segments to Mistral via HuggingFace Inference API
    to add severity ratings and richer context to each finding.
    """
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        print("No HUGGINGFACE_API_KEY found -- skipping Mistral enrichment.")
        return segments

    friction_segments = [s for s in segments if s.get("friction_flag")]
    if not friction_segments:
        return segments

    friction_text = "\n".join([
        f"[{s['start']}s] {s['text']}" for s in friction_segments
    ])

    prompt = f"""You are analyzing a usability session transcript.
Below are moments where the participant showed signs of friction or confusion.

For each moment, provide:
1. Severity: Critical, Major, or Minor
2. One sentence describing what usability problem this reveals
3. The Nielsen heuristic most relevant to this friction

Friction moments:
{friction_text}

Respond in this exact format for each moment, separated by ---:
[timestamp]s | [Severity] | [Problem description] | [Heuristic]"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 1000, "temperature": 0.3},
    }

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

        raw_text = (
            result[0]["generated_text"]
            if isinstance(result, list)
            else result.get("generated_text", "")
        )
        entries = raw_text.split("---")

        mistral_lookup = {}
        for entry in entries:
            entry = entry.strip()
            if "|" not in entry:
                continue
            parts = [p.strip() for p in entry.split("|")]
            if len(parts) >= 4:
                ts_match = re.search(r"[\d.]+", parts[0])
                if ts_match:
                    ts = float(ts_match.group())
                    mistral_lookup[ts] = {
                        "severity": parts[1],
                        "problem": parts[2],
                        "heuristic_mistral": parts[3],
                    }

        enriched = []
        for seg in segments:
            if seg.get("friction_flag"):
                extra = mistral_lookup.get(seg["start"], {})
                enriched.append({**seg, **extra})
            else:
                enriched.append(seg)

        return enriched

    except Exception as e:
        print(f"Mistral enrichment failed: {e}. Using local analysis only.")
        return segments


def analyze(segments: list[dict]) -> list[dict]:
    """
    Full analysis pipeline: local pattern matching then Mistral enrichment.
    Returns the full segment list with friction flags, severity, and heuristic tags.
    """
    print("Running local friction detection...")
    flagged = flag_friction_locally(segments)

    friction_count = sum(1 for s in flagged if s["friction_flag"])
    print(f"Found {friction_count} friction moments out of {len(flagged)} segments.")

    print("Running Mistral enrichment...")
    return analyze_with_mistral(flagged)
