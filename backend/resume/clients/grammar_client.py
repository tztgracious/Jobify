import requests
from jobify_backend.logger import logger
from typing import Dict, Any

class GrammarClient:
    """
    Client for interacting with the LanguageTool API for grammar checks.
    """
    
    def __init__(self):
        self.api_url = "https://api.languagetool.org/v2/check"

    def check_grammar(self, text: str, language: str = "en-US") -> Dict[str, Any]:
        """
        Sends text to LanguageTool and returns the results.
        """
        if not text:
            return {"matches": []}

        try:
            logger.info(f"Starting grammar check (text length: {len(text)})")
            response = requests.post(
                self.api_url,
                data={"text": text, "language": language},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Grammar check API request failed: {e}")
            # We return an empty result instead of crashing, as grammar check is non-critical
            return {"error": str(e), "matches": []}
