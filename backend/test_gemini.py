"""
Quick smoke test for the Gemini API connection.
Run from the backend directory with the venv active:
    python test_gemini.py

Reads GEMINI_API_KEY from .env via pydantic-settings.
"""
from app.core.config import settings
from google import genai

client = genai.Client(api_key=settings.gemini_api_key)

response = client.models.generate_content(
    model=settings.llm_model,
    contents="Explain what an IT incident investigation is in one sentence.",
)

print(response.text)
