# 🎬 AI YouTube Video Summarizer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://youtube-ai-summarizer-b5dpcfisfxvbr3kdb5wdrc.streamlit.app/)

An AI-powered web application that extracts transcripts from YouTube videos and generates structured summaries, actionable takeaways, and chapter highlights using Google's Gemini models and Streamlit.

## ✨ Features

* **Automatic Transcript Extraction:** Fetches native subtitles without third-party download limits using `youtube-transcript-api`.
* **Smart Audio Fallback:** Automatically bypasses cloud IP blocks using `yt-dlp` to download audio and process it directly via Gemini when native subtitles are disabled.
* **Multilingual Support:** Processes non-English transcripts natively using Gemini's built-in multilingual understanding.
* **Custom Summary Formats:** Choose between Detailed Breakdown, Quick TL;DR, or Bullet Points.
* **Interactive UI:** Built with Streamlit for fast, clean in-browser analysis alongside embedded video playback.
* **High-Availability Fallbacks:** Automatically routes requests across available Gemini models with exponential backoff.

## 🛠️ Tech Stack

* **Frontend / Framework:** Streamlit
* **LLM Engine:** Google GenAI SDK (Gemini 2.5/3.6 Flash & Pro)
* **Data Ingestion:** `youtube-transcript-api`, `yt-dlp`
* **Environment Management:** `python-dotenv`

## 🚀 Quick Start (Local Setup)

**1. Clone the Repository**
```bash
git clone [https://github.com/pallaviverma40/youtube-ai-summarizer.git](https://github.com/pallaviverma40/youtube-ai-summarizer.git)
cd youtube-ai-summarizer
