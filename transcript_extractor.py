def download_audio_fallback(youtube_url: str, output_path: str | None = None) -> str | None:
    """Downloads low-bitrate audio from YouTube as a fallback using yt-dlp with anti-bot bypass."""
    if not output_path:
        video_id = extract_video_id(youtube_url) or "video"
        output_path = os.path.join(tempfile.gettempdir(), f"yt_audio_{video_id}.m4a")

    ydl_opts = {
        "format": "ba[ext=m4a]/ba/w",
        "outtmpl": output_path,
        "overwrites": True,
        "quiet": False, # Crucial: Keep this False so Streamlit Cloud logs the actual error if blocked
        "no_warnings": False,
        "extractor_args": {
            "youtube": {
                # 'tv' and 'ios' clients bypass standard cloud IP blocks
                "player_client": ["tv", "ios", "mweb"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
            "Accept-Language": "en-US,en;q=0.9",
        }
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
        print(f"\n❌ [yt-dlp Download Error]: {str(e)}\n")
        return None