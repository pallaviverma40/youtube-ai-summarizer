import os
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

load_dotenv()

# Preferred models in priority order
DEFAULT_MODELS = [
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

BASE_PROMPT_TEMPLATE = """
You are an expert content analyst and summarizer.
Analyze the following YouTube video content and generate a well-structured, clear summary:

1. 📌 **Executive Summary (TL;DR)**: A concise 2-3 sentence overview.
2. 🎯 **Key Takeaways & Core Concepts**: Bullet points explaining the main arguments, insights, or lessons.
3. ⏱️ **Timestamped Chapter Highlights**: Logical flow of the video topic-by-topic.
4. 💡 **Actionable Insights / Practical Advice**: Key lessons or actionable steps viewers can apply.

{content_section}
"""

SYSTEM_INSTRUCTION = (
    "You provide accurate, well-formatted markdown summaries of video content. "
    "Avoid filler words. Keep formatting clean with emojis, bold headers, and concise bullet points."
)


def get_client() -> genai.Client:
    """Retrieves API key and returns an initialized Gemini client."""
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
    except Exception:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY missing! Set it in Streamlit Cloud Secrets, your local .env file, or the sidebar input."
        )

    return genai.Client(api_key=api_key)


def get_candidate_models(client: genai.Client) -> list[str]:
    """
    Discovers available Gemini models for the user's API key,
    prioritizing active models and falling back to known defaults.
    """
    try:
        discovered = []
        for m in client.models.list():
            raw_name = getattr(m, "name", "") or ""
            clean_name = raw_name.replace("models/", "")
            actions = getattr(m, "supported_actions", []) or []
            if "generateContent" in actions or "gemini" in clean_name.lower():
                discovered.append(clean_name)

        if not discovered:
            return DEFAULT_MODELS

        # Order by preference
        ordered = [m for m in DEFAULT_MODELS if m in discovered]
        remaining = [m for m in discovered if "gemini" in m.lower() and m not in ordered]
        result = ordered + remaining
        return result if result else DEFAULT_MODELS
    except Exception:
        return DEFAULT_MODELS


def _build_prompt(content_str: str, summary_type: str, is_audio: bool = False) -> str:
    """Builds prompt with appropriate format constraints."""
    if is_audio:
        content_section = "Audio recording provided above."
    else:
        content_section = f"Transcript:\n{content_str}"

    prompt = BASE_PROMPT_TEMPLATE.format(content_section=content_section)

    if summary_type == "Quick TL;DR (1 Minute Read)":
        prompt += "\nFormat constraint: Keep the entire output under 150 words."
    elif summary_type == "Bullet Points Only":
        prompt += "\nFormat constraint: Present the entire summary in concise bullet points only."

    return prompt


def generate_summary(transcript_text: str, summary_type: str = "Detailed") -> str:
    """Generates summary from transcript text using Gemini with dynamic model fallbacks."""
    if not transcript_text or not transcript_text.strip():
        raise ValueError("Transcript text is empty. Cannot generate summary.")

    client = get_client()
    candidate_models = get_candidate_models(client)
    prompt = _build_prompt(transcript_text, summary_type, is_audio=False)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.3,
    )

    last_error = None

    for model_name in candidate_models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
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

    raise RuntimeError(f"Unable to generate summary. Last error: {last_error}")


def generate_summary_from_audio(audio_path: str, summary_type: str = "Detailed") -> str:
    """Uploads audio to Gemini File API, waits for processing, and generates summary."""
    if not audio_path or not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    client = get_client()
    candidate_models = get_candidate_models(client)
    prompt = _build_prompt("", summary_type, is_audio=True)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.3,
    )

    audio_file = None
    try:
        # 1. Upload audio to Gemini File API
        audio_file = client.files.upload(file=audio_path)

        # 2. Wait for Gemini to finish audio processing (state == ACTIVE)
        max_wait_seconds = 60
        start_time = time.time()
        while audio_file.state.name == "PROCESSING":
            if time.time() - start_time > max_wait_seconds:
                raise TimeoutError("Timed out waiting for Gemini to process the audio file.")
            time.sleep(3)
            audio_file = client.files.get(name=audio_file.name)

        if audio_file.state.name == "FAILED":
            raise RuntimeError(f"Gemini audio processing failed: {audio_file.error}")

        # 3. Generate content with model fallbacks
        last_error = None
        for model_name in candidate_models:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[audio_file, prompt],
                        config=config,
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

        raise RuntimeError(f"Audio summarization failed across candidate models: {last_error}")

    finally:
        # Clean up the file from Gemini storage
        if audio_file and hasattr(audio_file, "name"):
            try:
                client.files.delete(name=audio_file.name)
            except Exception:
                pass