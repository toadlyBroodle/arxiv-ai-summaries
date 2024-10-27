import os
import time
import logging
import google.generativeai as genai
import google.api_core.exceptions
from typing import Optional
from dotenv import load_dotenv

class GeminiAPI:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        api_key = os.environ.get("AISTUDIO_GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("AISTUDIO_GOOGLE_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        self.model: genai.GenerativeModel = genai.GenerativeModel("gemini-1.5-flash")
        self.MAX_RETRIES: int = 3
        self.RETRY_DELAY: int = 120  # 2 minutes base delay
        self.WAIT_BETWEEN_CALLS: int = 120  # 2 minutes between API calls
        self._last_call_time = 0

    def _wait_between_calls(self):
        """Ensure we wait appropriate time between API calls"""
        if self._last_call_time > 0:
            elapsed = time.time() - self._last_call_time
            if elapsed < self.WAIT_BETWEEN_CALLS:
                wait_time = self.WAIT_BETWEEN_CALLS - elapsed
                logging.info(f"Waiting {wait_time:.1f} seconds before next API call...")
                time.sleep(wait_time)
        self._last_call_time = time.time()

    def generate_summary(self, prompt: str) -> tuple[Optional[str], Optional[str]]:
        """
        Generate a summary using Gemini API.
        Handles rate limiting by waiting between calls.
        """
        self._wait_between_calls()
        
        if not prompt or not isinstance(prompt, str):
            return None, "Invalid prompt: prompt must be a non-empty string"
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.model.generate_content(prompt)
                
                # Check if the response was blocked
                if response.prompt_feedback.block_reason:
                    error_msg = f"Response blocked: {response.prompt_feedback.block_reason}"
                    logging.error(error_msg)
                    return None, error_msg

                # Handle the response
                if hasattr(response, 'text'):
                    summary = response.text.strip()
                elif hasattr(response, 'parts'):
                    summary = ' '.join([part.text for part in response.parts]).strip()
                else:
                    summary = str(response)
                
                return summary, None

            except google.api_core.exceptions.ResourceExhausted as e:
                logging.warning(f"Rate limit exceeded (attempt {attempt + 1}/{self.MAX_RETRIES}): {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAY * (attempt + 1)  # Exponential backoff
                    logging.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    error_msg = "Rate limit exceeded"
                    logging.error(f"Max retries exceeded: {error_msg}")
                    return None, error_msg
                    
            except google.api_core.exceptions.InvalidArgument as e:
                error_msg = f"Invalid argument error: {str(e)}"
                logging.error(error_msg)
                return None, error_msg
                
            except Exception as e:
                logging.error(f"Unexpected error (attempt {attempt + 1}/{self.MAX_RETRIES}): {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAY * (attempt + 1)
                    logging.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    error_msg = str(e)
                    logging.error(f"Max retries exceeded: {error_msg}")
                    return None, error_msg
        
        return None, "Max retries exceeded"

    def check_api_availability(self) -> bool:
        """Test if the Gemini API is accessible."""
        try:
            self.model.generate_content("test")
            return True
        except Exception as e:
            logging.error(f"API check failed: {str(e)}")
            return False
