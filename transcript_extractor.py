import os
import re
import yt_dlp
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
)

def extract_video_id(url: str) -> str | None:
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
    """Fetches native transcript if available."""
    try:
        api = YouTubeTranscriptApi() if callable(YouTubeTranscriptApi) else YouTubeTranscriptApi
        raw_data = None

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

        if not raw_data:
            return None, None

        text_parts = [item.get("text", "") for item in raw_data if isinstance(item, dict)]
        return " ".join(text_parts).strip(), raw_data

    except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript):
        return None, None
    except Exception:
        return None, None

def download_audio_fallback(youtube_url: str, output_path: str = "temp_audio.mp3") -> str | None:
    """Downloads low-bitrate audio from YouTube as a fallback."""
    ydl_opts = {
        'format': 'ba[ext=m4a]/ba',
        'outtmpl': output_path,
        'overwrites': True,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        return output_path if os.path.exists(output_path) else None
    except Exception:
        return None