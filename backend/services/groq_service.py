"""Simple Groq AI service wrapper for testing."""

import os
from dotenv import load_dotenv
from groq import Groq


class GroqService:
    """Lightweight Groq AI client wrapper."""

    def __init__(self, api_key: str = None, model_name: str = None):
        self._api_key = api_key or os.getenv("GROQ_API_KEY")
        
        # Initialize Groq client
        if self._api_key:
            self._client = Groq(api_key=self._api_key)
        else:
            self._client = Groq()  # Uses GROQ_API_KEY from env
        
        # Set model (hardcoded default for hackathon)
        self._model_name = model_name or "llama-3.1-8b-instant"

    def generate_text(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 1,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> str:
        """Generate text from a prompt."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        completion = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
            top_p=1,
            stream=stream,
            stop=None
        )
        
        if stream:
            return completion  # Return the generator for streaming
        else:
            return completion.choices[0].message.content

    def chat(self, messages: list, stream: bool = False) -> str:
        """Chat with context. Pass list of dicts with 'role' and 'content'."""
        completion = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=stream,
            stop=None
        )
        
        if stream:
            return completion  # Return the generator for streaming
        else:
            return completion.choices[0].message.content


def test_groq_service():
    """Test function to verify Groq service functionality."""
    load_dotenv()
    
    service = GroqService()
    
    # Test with streaming (like documentation example)
    completion = service._client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": "Explain what a fishing sonar does in a brief sentence."
            }
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=True,
        stop=None
    )
    
    for chunk in completion:
        print(chunk.choices[0].delta.content or "", end="")
    
    print()  # New line at end


if __name__ == "__main__":
    test_groq_service()

