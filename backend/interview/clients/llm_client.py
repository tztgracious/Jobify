import json
import os
import re
import requests
from typing import List, Dict, Any, Optional
from jobify_backend.logger import logger

class InterviewLLMClient:
    """
    Centralized client for interacting with LLM providers (OpenRouter/OpenAI).
    Handles authentication, standardized requests, and response parsing.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPEN_ROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "jobify.com",
            "X-Title": "Jobify",
        }
        self.default_model = "openai/gpt-4o"

    def _clean_json_response(self, response_text: str) -> str:
        """Extract JSON object from a potentially markdown-formatted string."""
        cleaned = response_text.strip()
        # Find the first { and last } to extract just the JSON object
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group()
        return cleaned

    def complete(self, prompt: str, model: Optional[str] = None, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a completion request to the LLM.
        Returns a dictionary containing the parsed JSON response or an error state.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.default_model,
            "messages": messages,
        }

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            cleaned_content = self._clean_json_response(content)
            return json.loads(cleaned_content)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            raise Exception(f"Failed to communicate with LLM provider: {e}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise Exception("Received malformed response from LLM provider")

    def complete_raw(self, prompt: str, model: Optional[str] = None) -> str:
        """Returns the raw string content without JSON parsing."""
        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": model or self.default_model,
            "messages": messages,
        }

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM API raw request failed: {e}")
            raise Exception(f"LLM raw request failed: {e}")
