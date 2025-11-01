from google import genai

from ..utils.config import get_settings

settings = get_settings()


def get_gemini_client():
    return genai.Client(api_key=settings.gemini_api_key)
