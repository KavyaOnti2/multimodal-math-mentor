import whisper
from typing import Tuple

# Load Whisper model once
model = whisper.load_model("base")

def transcribe_audio(audio_path: str) -> Tuple[str, float]:
    """
    Returns transcript and heuristic confidence.
    """

    try:
        result = model.transcribe(audio_path)

        text = result.get("text", "").strip()

        if not text:
            return "", 0.0

        # Whisper doesn't give confidence → heuristic
        confidence = 0.8 if len(text) > 5 else 0.4

        return text, confidence

    except Exception as e:
        print(f"ASR Error: {e}")
        return "", 0.0