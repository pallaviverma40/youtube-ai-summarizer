import streamlit as st
from transcript_extractor import extract_video_id, get_transcript_text
from summarizer import generate_summary

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
                with st.spinner("⏳ Extracting transcript and generating summary..."):
                    transcript_text, raw_data = get_transcript_text(video_id)
                    
                    if not transcript_text:
                        st.error("❌ No subtitles/transcripts found for this video. Consider enabling audio transcription fallback.")
                    else:
                        summary = generate_summary(transcript_text, summary_type)
                        st.success("✅ Summary Generated!")
                        st.markdown(summary)
                        
                        # Download Button
                        st.download_button(
                            label="📥 Download Summary as Markdown",
                            data=summary,
                            file_name=f"summary_{video_id}.md",
                            mime="text/markdown"
                        )