import os
import re
import tempfile
import yt_dlp
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
)


def extract_video_id(url: str) -> str | None:
    """Extracts the 11-character YouTube video ID from various URL formats or raw IDs."""
    if not url:
        return None

    url = url.strip()

    # Direct 11-character ID
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url):
        return url

    patterns = [
        r"(?:v=|\/v\/|youtu\.be\/|embed\/|shorts\/|live\/)([0-9A-Za-z_-]{11})",
        r"[?&]v=([0-9A-Za-z_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_transcript_text(video_id: str) -> tuple[str | None, list | None]:
    """
    Fetches native video transcript.
    Compatible with both youtube-transcript-api >= 1.0.0 and legacy versions.
    Tries preferred languages ('en', 'en-US', etc.) and falls back to any available transcript.
    """
    try:
        raw_data = None
        api = YouTubeTranscriptApi() if callable(YouTubeTranscriptApi) else YouTubeTranscriptApi

        # Approach 1: Modern youtube-transcript-api (>= 1.0.0)
        if hasattr(api, "fetch") or hasattr(api, "list"):
            try:
                # Try English first
                fetched = api.fetch(video_id, languages=("en", "en-US", "en-GB"))
                raw_data = fetched.to_raw_data()
            except Exception:
                # Fall back to first available transcript (other languages or auto-generated)
                try:
                    transcript_list = api.list(video_id)
                    for transcript in transcript_list:
                        fetched = transcript.fetch()
                        raw_data = fetched.to_raw_data()
                        break
                except Exception:
                    pass

        # Approach 2: Legacy youtube-transcript-api (< 1.0.0)
        if not raw_data:
            get_fn = getattr(api, "get_transcript", None) or getattr(YouTubeTranscriptApi, "get_transcript", None)
            if get_fn:
                try:
                    raw_data = get_fn(video_id, languages=["en", "en-US", "en-GB"])
                except Exception:
                    try:
                        list_fn = getattr(api, "list_transcripts", None) or getattr(YouTubeTranscriptApi, "list_transcripts", None)
                        if list_fn:
                            t_list = list_fn(video_id)
                            for t in t_list:
                                raw_data = t.fetch()
                                break
                    except Exception:
                        pass

        if not raw_data:
            return None, None

        # Build clean string from raw segments
        text_parts = [item.get("text", "") for item in raw_data if isinstance(item, dict)]
        full_text = " ".join(text_parts).strip()
        return full_text if full_text else None, raw_data

    except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript):
        return None, None
    except Exception as e:
        print(f"[WARN] Error extracting transcript: {e}")
        return None, None


def download_audio_fallback(youtube_url: str, output_path: str | None = None) -> str | None:
    """Downloads low-bitrate audio from YouTube as a fallback using yt-dlp."""
    if not output_path:
        video_id = extract_video_id(youtube_url) or "video"
        output_path = os.path.join(tempfile.gettempdir(), f"yt_audio_{video_id}.m4a")

    ydl_opts = {
        "format": "ba[ext=m4a]/ba",
        "outtmpl": output_path,
        "overwrites": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        print(f"[ERROR] yt-dlp download failed: {e}")
        return None