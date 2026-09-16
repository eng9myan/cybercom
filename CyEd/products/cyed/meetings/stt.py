"""
Speech-to-text seam. Audio→transcript needs a provider (Whisper / AWS Transcribe /
Azure Speech), gated by CYED_STT_ENABLED. A device that already transcribes just
posts `transcript`, so summarisation (below) is real regardless.
"""

import os


def transcribe(audio_bytes: bytes, content_type: str = "") -> str | None:
    if os.environ.get("CYED_STT_ENABLED") == "1":
        # A real provider call goes here and returns the transcript text.
        return None
    return None
