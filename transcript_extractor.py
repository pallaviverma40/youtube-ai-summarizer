import re
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
)

def extract_video_id(url: str) -> str | None:
    """Extracts YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript_text(video_id: str) -> tuple[str | None, list | None]:
    """
    Fetches transcript from YouTube in its native format.
    Returns:
        (full_text_string, raw_transcript_list_with_timestamps) or (None, None)
    """
    try:
        api = YouTubeTranscriptApi() if callable(YouTubeTranscriptApi) else YouTubeTranscriptApi
        raw_data = None

        # Strategy 1: Fetch via instance or class get_transcript
        if hasattr(api, "get_transcript"):
            try:
                raw_data = api.get_transcript(video_id)
            except Exception:
                pass
        elif hasattr(YouTubeTranscriptApi, "get_transcript"):
            try:
                raw_data = YouTubeTranscriptApi.get_transcript(video_id)
            except Exception:
                pass

        # Strategy 2: Fetch via list() iteration
        if raw_data is None and hasattr(api, "list"):
            try:
                transcript_list = api.list(video_id)
                for transcript in transcript_list:
                    raw_data = transcript.fetch()
                    if raw_data:
                        break
            except Exception:
                pass

        # Strategy 3: Direct fetch method
        if raw_data is None and hasattr(api, "fetch"):
            try:
                raw_data = api.fetch(video_id)
            except Exception:
                pass

        if not raw_data:
            return None, None

        # Extract text snippets
        text_parts = []
        for item in raw_data:
            if isinstance(item, dict):
                text_parts.append(item.get("text", ""))
            elif hasattr(item, "text"):
                text_parts.append(getattr(item, "text", ""))
            else:
                text_parts.append(str(item))

        full_text = " ".join(text_parts).strip()
        return full_text, raw_data

    except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript):
        return None, None
    except Exception as e:
        error_msg = str(e).lower()
        if "not translatable" in error_msg or "could not retrieve" in error_msg:
            return None, None
        raise RuntimeError(f"Error fetching transcript: {e}")