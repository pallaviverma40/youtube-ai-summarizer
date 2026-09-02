import os
import streamlit as st
from transcript_extractor import (
    extract_video_id,
    get_transcript_text,
    download_audio_fallback,
)
from summarizer import generate_summary, generate_summary_from_audio

st.set_page_config(page_title="AI YouTube Summarizer", page_icon="🎬", layout="wide")

st.title("🎬 AI YouTube Video Summarizer")
st.caption("Summarize any YouTube video in seconds using AI.")

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Configuration")
    summary_type = st.selectbox(
        "Summary Style",
        ["Detailed", "Quick TL;DR (1 Minute Read)", "Bullet Points Only"]
    )
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
            col1, col2 = st.columns([1, 1.5])
            
            with col1:
                st.video(video_url)
            
            with col2:
                summary = None
                with st.spinner("⏳ Checking for native video transcript..."):
                    transcript_text, _ = get_transcript_text(video_id)
                
                # Case 1: Video has subtitles
                if transcript_text:
                    with st.spinner("🤖 Generating summary with Gemini..."):
                        try:
                            summary = generate_summary(transcript_text, summary_type)
                        except Exception as e:
                            st.error(f"Error generating summary: {e}")
                
                # Case 2: No subtitles -> Audio fallback via Gemini File API
                else:
                    st.info("ℹ️ No native subtitles found. Falling back to direct audio processing...")
                    
                    with st.spinner("📥 Extracting audio stream from video..."):
                        audio_file = download_audio_fallback(video_url)
                    
                    if audio_file and os.path.exists(audio_file):
                        try:
                            with st.spinner("🎙️ Uploading and analyzing audio with Gemini..."):
                                summary = generate_summary_from_audio(audio_file, summary_type)
                        except Exception as e:
                            st.error(f"Audio processing error: {e}")
                        finally:
                            # Clean up temporary audio file locally
                            if os.path.exists(audio_file):
                                os.remove(audio_file)
                    else:
                        st.error("❌ Could not extract subtitles or download audio for this video.")

                # Render summary and download button if generated
                if summary:
                    st.success("✅ Summary Generated!")
                    st.markdown(summary)
                    
                    st.download_button(
                        label="📥 Download Summary as Markdown",
                        data=summary,
                        file_name=f"summary_{video_id}.md",
                        mime="text/markdown"
                    )