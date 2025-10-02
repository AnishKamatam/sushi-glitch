"""Simple Gemini AI service wrapper for testing."""

import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

class GeminiService:
    """Lightweight Gemini AI client wrapper."""

    def __init__(self, api_key: str = None, model_name: str = None):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or "your_gemini_api_key_here"
        
        if self._api_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")
        
        # Configure Gemini
        genai.configure(api_key=self._api_key)
        
        # Set model (default to flash for speed)
        self._model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self._model = genai.GenerativeModel(self._model_name)

    def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt."""
        response = self._model.generate_content(prompt)
        return response.text.strip()

    def chat(self, messages: list) -> str:
        """Chat with context. Pass list of dicts with 'role' and 'content'."""
        # Convert to Gemini format
        chat = self._model.start_chat(history=[])
        
        for msg in messages:
            if msg.get('role') == 'user':
                response = chat.send_message(msg.get('content', ''))
        
        return response.text.strip()


def test_gemini_service():
    """Test function to verify Gemini service functionality."""
    load_dotenv()
    print("Testing Gemini Service...")
    
    service = GeminiService()
    
    # Simple text generation test
    prompt = "Explain what a fishing sonar does in one sentence."
    response = service.generate_text(prompt)
    
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")


if __name__ == "__main__":
    test_gemini_service()

