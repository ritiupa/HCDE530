"""
transcription.py
----------------
Takes a WAV file path and runs OpenAI Whisper locally to produce a
timestamped transcript. Whisper runs on your machine -- no API key needed,
no cost per call.

Returns a list of segments, each with a start time, end time, and text.
"""

from pathlib import Path


def transcribe(audio_path: str, model_size: str = "base") -> list[dict]:
    """
    Transcribes audio using Whisper and returns timestamped segments.

    Parameters:
        audio_path -- path to the WAV file
        model_size -- Whisper model to use: tiny, base, small, medium, large
                      "base" is a good balance of speed and accuracy for English.
                      Use "small" if accuracy is more important than speed.

    Returns a list of dicts:
        [
            {"start": 0.0, "end": 4.2, "text": "I expected this button to..."},
            {"start": 4.2, "end": 8.7, "text": "where do I find the..."},
            ...
        ]
    """

    try:
        import whisper
    except ImportError:
        raise ImportError(
            "openai-whisper is required. Run: pip install openai-whisper"
        )

    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"Loading Whisper model ({model_size})...")
    model = whisper.load_model(model_size)

    print(f"Transcribing: {audio_path.name}")
    result = model.transcribe(str(audio_path), fp16=False, language="en")

    segments = []
    for seg in result["segments"]:
        segments.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
        })

    print(f"Transcription complete. {len(segments)} segments produced.")
    return segments
