import os
import streamlit as st
from transcript_extractor import (
    extract_video_id,
    get_transcript_text,
    download_audio_fallback,
)
from summarizer import generate_summary, generate_summary_from_audio

st.set_page_config(page_title="AI YouTube Summarizer", page_icon="🎬", layout="wide")

# Initialize session state for persistent results across reruns
if "summary" not in st.session_state:
    st.session_state.summary = None
if "active_video_url" not in st.session_state:
    st.session_state.active_video_url = ""
if "active_video_id" not in st.session_state:
    st.session_state.active_video_id = ""
if "transcript" not in st.session_state:
    st.session_state.transcript = None

st.title("🎬 AI YouTube Video Summarizer")
st.caption("Summarize any YouTube video in seconds using Google Gemini.")

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Configuration")
    
    summary_type = st.selectbox(
        "Summary Style",
        ["Detailed", "Quick TL;DR (1 Minute Read)", "Bullet Points Only"]
    )
    
    st.markdown("---")
    user_api_key = st.text_input(
        "Gemini API Key (optional):",
        type="password",
        help="Leave blank if GEMINI_API_KEY is already set in your .env or Streamlit Secrets."
    )
    if user_api_key.strip():
        os.environ["GEMINI_API_KEY"] = user_api_key.strip()
    
    st.markdown("---")
    st.markdown("💡 **Tip**: Supports videos of any length thanks to Gemini's 1M+ token context window.")

# Main input
video_url = st.text_input("Enter YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("✨ Summarize Video", type="primary"):
    if not video_url.strip():
        st.warning("Please enter a valid YouTube URL.")
    else:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("Invalid YouTube URL. Please check the link and try again.")
        else:
            st.session_state.active_video_url = video_url
            st.session_state.active_video_id = video_id
            st.session_state.summary = None
            st.session_state.transcript = None

            with st.status("🔍 Analyzing video...", expanded=True) as status:
                st.write("Checking for native video transcripts...")
                transcript_text, _ = get_transcript_text(video_id)

                # Case 1: Video has subtitles
                if transcript_text:
                    st.session_state.transcript = transcript_text
                    st.write("✅ Transcript found! Generating summary with Gemini...")
                    try:
                        st.session_state.summary = generate_summary(transcript_text, summary_type)
                        status.update(label="✅ Summary generated!", state="complete", expanded=False)
                    except Exception as e:
                        status.update(label="❌ Failed to generate summary", state="error")
                        st.error(f"Error generating summary: {e}")

                # Case 2: Audio fallback
                else:
                    st.write("ℹ️ No native subtitles found. Falling back to direct audio processing...")
                    st.write("📥 Extracting audio stream from video...")
                    audio_file = download_audio_fallback(video_url)

                    if audio_file and os.path.exists(audio_file):
                        try:
                            st.write("🎙️ Uploading and analyzing audio with Gemini...")
                            st.session_state.summary = generate_summary_from_audio(audio_file, summary_type)
                            status.update(label="✅ Audio summary generated!", state="complete", expanded=False)
                        except Exception as e:
                            status.update(label="❌ Audio processing error", state="error")
                            st.error(f"Audio processing error: {e}")
                        finally:
                            if os.path.exists(audio_file):
                                try:
                                    os.remove(audio_file)
                                except OSError:
                                    pass
                    else:
                        status.update(label="❌ Extraction failed", state="error")
                        st.error("Could not extract subtitles or download audio stream for this video.")

# Render persistent layout (Video on Left, Summary on Right)
if st.session_state.active_video_url:
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.video(st.session_state.active_video_url)
        
        if st.session_state.transcript:
            with st.expander("📄 View Source Transcript"):
                st.write(st.session_state.transcript)

    with col2:
        if st.session_state.summary:
            st.subheader("📝 Summary")
            st.markdown(st.session_state.summary)

            st.download_button(
                label="📥 Download Summary as Markdown",
                data=st.session_state.summary,
                file_name=f"summary_{st.session_state.active_video_id}.md",
                mime="text/markdown",
            )