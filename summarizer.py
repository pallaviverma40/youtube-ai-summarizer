import os
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

load_dotenv()

# Check Streamlit Cloud secrets first; fall back to local .env
api_key = None
try:
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY missing! Set it in Streamlit Cloud Secrets or your local .env file."
    )

client = genai.Client(api_key=api_key)

PROMPT_TEMPLATE = """
You are an expert content analyst and summarizer.
Analyze the following YouTube video transcript and generate a structured summary with:

1. 📌 **Executive Summary (TL;DR)**: A concise 2-3 sentence overview.
2. 🎯 **Key Takeaways & Core Concepts**: Bullet points explaining the main arguments or lessons.
3. ⏱️ **Timestamped Chapter Highlights**: Logical flow of the video.
4. 💡 **Actionable Insights / Practical Advice**: Key lessons or steps viewers can apply.

Transcript:
{transcript}
"""

def generate_summary(transcript_text: str, summary_type: str = "Detailed") -> str:
    """Generates summary using Gemini with fallback models and retry backoff on 503."""

    system_instruction = (
        "You provide accurate, well-formatted markdown summaries of video transcripts. "
        "Avoid filler words. Keep formatting clean with emojis and bold headers."
    )

    prompt = PROMPT_TEMPLATE.format(transcript=transcript_text)

    if summary_type == "Quick TL;DR (1 Minute Read)":
        prompt += "\nFormat constraint: Keep the entire output under 150 words."
    elif summary_type == "Bullet Points Only":
        prompt += "\nFormat constraint: Present the entire summary in concise bullet points only."

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3
    )

    candidate_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-3.6-flash",
    ]

    last_error = None

    for model_name in candidate_models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                if response.text:
                    return response.text
            except ServerError as e:
                last_error = e
                time.sleep(2 * (attempt + 1))
                continue
            except ClientError as e:
                last_error = e
                break
            except Exception as e:
                last_error = e
                break

    raise RuntimeError(
        f"Google servers are experiencing temporary high demand (503). "
        f"Please wait 10-15 seconds and try again. Details: {last_error}"
    )

def generate_summary_from_audio(audio_path: str, summary_type: str = "Detailed") -> str:
    """Uploads downloaded audio to Gemini File API and generates a structured summary."""

    system_instruction = (
        "You provide accurate, well-formatted markdown summaries of spoken audio. "
        "Avoid filler words. Keep formatting clean with emojis and bold headers."
    )

    prompt = (
        "Analyze the spoken content of this audio recording and generate a structured summary with:\n"
        "1. 📌 **Executive Summary (TL;DR)**\n"
        "2. 🎯 **Key Takeaways & Core Concepts**\n"
        "3. ⏱️ **Timestamped Chapter Highlights**\n"
        "4. 💡 **Actionable Insights / Practical Advice**"
    )

    if summary_type == "Quick TL;DR (1 Minute Read)":
        prompt += "\nFormat constraint: Keep output under 150 words."
    elif summary_type == "Bullet Points Only":
        prompt += "\nFormat constraint: Present the entire summary in concise bullet points only."

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3
    )

    # Upload local audio directly to Gemini File API
    audio_file = client.files.upload(file=audio_path)

    try:
        candidate_models = ["gemini-2.5-flash", "gemini-2.5-pro"]
        last_error = None

        for model_name in candidate_models:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[audio_file, prompt],
                        config=config
                    )
                    if response.text:
                        return response.text
                except ServerError as e:
                    last_error = e
                    time.sleep(2 * (attempt + 1))
                    continue
                except Exception as e:
                    last_error = e
                    break

        raise RuntimeError(f"Audio processing failed across models: {last_error}")

    finally:
        # Delete file from Gemini cloud storage to keep storage clean
        try:
            client.files.delete(name=audio_file.name)
        except Exception:
            pass