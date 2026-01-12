"""
Gemini API Client wrapper for Memotion.
Handles connection to Google Gemini API and message generation.
"""
import logging
import os
from typing import Optional, Dict, Any
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Wrapper for Google Gemini API.
    Handles API key configuration, model initialization, and content generation.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3-flash-preview"):
        """
        Initialize Gemini client.

        Args:
            api_key: Google Gemini API key. If None, reads from environment variable.
            model_name: Gemini model to use (default: gemini-1.5-flash).
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        self.model_name = model_name
        self._configure_api()
        self.model = genai.GenerativeModel(self.model_name)
        logger.info(f"GeminiClient initialized with model: {self.model_name}")

    def _configure_api(self):
        """Configure Gemini API with API key."""
        genai.configure(api_key=self.api_key)
        logger.debug("Gemini API configured successfully")

    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.95,
        top_k: int = 40
    ) -> str:
        """
        Generate content using Gemini API.

        Args:
            prompt: Input prompt text.
            temperature: Sampling temperature (0.0-1.0). Higher = more creative.
            max_tokens: Maximum tokens in response.
            top_p: Nucleus sampling parameter.
            top_k: Top-k sampling parameter.

        Returns:
            Generated text response.

        Raises:
            Exception: If API call fails.
        """
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=max_tokens,
            )

            logger.info(f"Generating content with Gemini (temp={temperature}, model={self.model_name})")
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            if not response.text:
                logger.error("Gemini returned empty response")
                raise Exception("Empty response from Gemini API")

            logger.info(f"Successfully generated content ({len(response.text)} chars)")
            return response.text

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate content: {str(e)}")

    def generate_json_content(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 4096
    ) -> Dict[str, Any]:
        """
        Generate structured JSON content using Gemini API.
        Uses lower temperature for more consistent output.

        Args:
            prompt: Input prompt requesting JSON output.
            temperature: Sampling temperature (default: 0.3 for structured output).
            max_tokens: Maximum tokens in response.

        Returns:
            Parsed JSON dictionary.

        Raises:
            Exception: If API call fails or response is not valid JSON.
        """
        import json

        try:
            # Add JSON instruction to prompt if not already present
            if "json" not in prompt.lower():
                prompt = f"{prompt}\n\nRespond with valid JSON only."

            response_text = self.generate_content(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Try to extract JSON from code blocks if present
            original_response = response_text
            extracted_json = None
            
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                extracted_json = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                extracted_json = response_text[json_start:json_end].strip()
            else:
                # No code blocks, assume whole response is JSON
                extracted_json = response_text.strip()

            # Clean the JSON string to remove any trailing text
            extracted_json = self._clean_json_string(extracted_json)

            # Log the extracted JSON for debugging
            logger.info(f"Extracted JSON from AI response: {extracted_json[:500]}...")

            # Try parsing extracted JSON first
            try:
                parsed_json = json.loads(extracted_json)
                logger.info("Successfully parsed JSON response from Gemini")
                logger.info(f"Raw AI response: {original_response}")
                logger.info(f"Parsed JSON: {json.dumps(parsed_json, indent=2)}")
                return parsed_json
            except json.JSONDecodeError as e1:
                logger.warning(f"Failed to parse extracted JSON: {str(e1)}")
                # Try to fix common JSON issues
                fixed_json = self._fix_malformed_json(extracted_json)
                if fixed_json != extracted_json:
                    try:
                        parsed_json = json.loads(fixed_json)
                        logger.info("Successfully parsed fixed JSON response from Gemini")
                        return parsed_json
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Fixed JSON also failed: {str(e2)}")
                
                # Fallback: try parsing the original response
                logger.warning("Failed to parse extracted JSON, trying original response")
                cleaned_original = self._clean_json_string(original_response)
                parsed_json = json.loads(cleaned_original)
                logger.info("Successfully parsed JSON from original response")
                return parsed_json

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {str(e)}")
            logger.error(f"Extracted JSON text: {extracted_json}")
            logger.error(f"Cleaned JSON text: {self._clean_json_string(extracted_json)}")
            logger.error(f"Full response text: {original_response}")
            # Log the problematic character position
            if extracted_json:
                logger.error(f"Character at error position: {extracted_json[min(len(extracted_json)-1, 381)]}")
            raise Exception(f"Invalid JSON response from Gemini: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating JSON content: {str(e)}", exc_info=True)
            raise

    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean JSON string by removing trailing text after the last valid closing brace.
        Attempts to complete incomplete JSON structures.
        
        Args:
            json_str: Raw JSON string that may contain trailing text.
            
        Returns:
            Cleaned JSON string.
        """
        # Find the last closing brace
        last_brace = json_str.rfind('}')
        if last_brace == -1:
            return json_str
            
        # Extract JSON up to the last closing brace
        cleaned = json_str[:last_brace + 1]
        
        # Try to balance braces to ensure we have valid JSON structure
        open_braces = cleaned.count('{')
        close_braces = cleaned.count('}')
        
        # If braces are balanced, return cleaned
        if open_braces == close_braces:
            return cleaned
            
        # If not balanced, try to find a valid JSON substring
        # This is a simple approach - find the longest valid JSON prefix
        for i in range(len(cleaned) - 1, 0, -1):
            test_json = cleaned[:i + 1]
            test_open = test_json.count('{')
            test_close = test_json.count('}')
            if test_open == test_close and test_open > 0:
                return test_json
                
        # If still not balanced, try to complete the JSON by adding missing braces
        if open_braces > close_braces:
            missing_closes = open_braces - close_braces
            cleaned += '}' * missing_closes
            
            # Try to add recommendations if missing
            if '"recommendations"' not in cleaned:
                # Find the position before the last }
                last_brace_pos = cleaned.rfind('}')
                if last_brace_pos > 0:
                    # Insert recommendations array before the last }
                    recommendations = ',\n  "recommendations": [\n    "Monitor patient condition closely",\n    "Consult healthcare provider if symptoms worsen"\n  ]'
                    cleaned = cleaned[:last_brace_pos] + recommendations + cleaned[last_brace_pos:]
        
        return cleaned

    def _fix_malformed_json(self, json_str: str) -> str:
        """
        Attempt to fix common JSON formatting issues.
        
        Args:
            json_str: Potentially malformed JSON string.
            
        Returns:
            Fixed JSON string.
        """
        # Fix unterminated strings by adding closing quotes
        lines = json_str.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.rstrip()
            # Count quotes in the line
            quote_count = line.count('"')
            # If odd number of quotes, the string might be unterminated
            if quote_count % 2 == 1:
                # Find the last quote and add closing quote if needed
                last_quote_pos = line.rfind('"')
                if last_quote_pos != -1 and not line.endswith('"'):
                    # Check if there are commas or braces after the last quote
                    after_quote = line[last_quote_pos + 1:]
                    if ',' in after_quote or '}' in after_quote or ']' in after_quote:
                        # Insert closing quote before the punctuation
                        for punct in [',', '}', ']']:
                            punct_pos = after_quote.find(punct)
                            if punct_pos != -1:
                                line = line[:last_quote_pos + 1] + '"' + after_quote
                                break
            fixed_lines.append(line)
        
        fixed_json = '\n'.join(fixed_lines)
        
        # If no changes were made, return original
        if fixed_json == json_str:
            return json_str
            
        logger.info(f"Attempted to fix malformed JSON: {fixed_json[:500]}...")
        return fixed_json

    def chat(self, messages: list, temperature: float = 0.7) -> str:
        """
        Multi-turn chat conversation with Gemini.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Sampling temperature.

        Returns:
            Generated response text.
        """
        try:
            # Convert messages to Gemini format
            chat_session = self.model.start_chat(history=[])

            for msg in messages[:-1]:  # All but last message
                if msg['role'] == 'user':
                    chat_session.send_message(msg['content'])

            # Send last message and get response
            response = chat_session.send_message(
                messages[-1]['content'],
                generation_config=genai.types.GenerationConfig(temperature=temperature)
            )

            return response.text

        except Exception as e:
            logger.error(f"Chat error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to chat with Gemini: {str(e)}")

    def generate_content_with_image(
        self,
        prompt: str,
        image_path: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.95,
        top_k: int = 40
    ) -> str:
        """
        Generate content using Gemini API with image input.

        Args:
            prompt: Input prompt text.
            image_path: Path to the image file.
            temperature: Sampling temperature (0.0-1.0). Higher = more creative.
            max_tokens: Maximum tokens in response.
            top_p: Nucleus sampling parameter.
            top_k: Top-k sampling parameter.

        Returns:
            Generated text response.

        Raises:
            Exception: If API call fails.
        """
        try:
            import PIL.Image

            # Load image
            image = PIL.Image.open(image_path)

            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=max_tokens,
            )

            logger.info(f"Generating content with image using Gemini (temp={temperature}, model={self.model_name})")
            response = self.model.generate_content(
                [prompt, image],
                generation_config=generation_config
            )

            if not response.text:
                logger.error("Gemini returned empty response for image")
                raise Exception("Empty response from Gemini API")

            logger.info(f"Successfully generated content with image ({len(response.text)} chars)")
            return response.text

        except Exception as e:
            logger.error(f"Gemini API error with image: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate content with image: {str(e)}")

    def generate_json_content_with_image(
        self,
        prompt: str,
        image_path: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 4096
    ) -> Dict[str, Any]:
        """
        Generate structured JSON content using Gemini API with image input.
        Uses lower temperature for more consistent output.

        Args:
            prompt: Input prompt requesting JSON output.
            image_path: Path to the image file.
            temperature: Sampling temperature (default: 0.3 for structured output).
            max_tokens: Maximum tokens in response.

        Returns:
            Parsed JSON dictionary.

        Raises:
            Exception: If API call fails or response is not valid JSON.
        """
        import json

        try:
            # Add JSON instruction to prompt if not already present
            if "json" not in prompt.lower():
                prompt = f"{prompt}\n\nRespond with valid JSON only."

            response_text = self.generate_content_with_image(
                prompt=prompt,
                image_path=image_path,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Try to extract JSON from code blocks if present
            original_response = response_text
            extracted_json = None
            
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                extracted_json = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                extracted_json = response_text[json_start:json_end].strip()
            else:
                # No code blocks, assume whole response is JSON
                extracted_json = response_text.strip()

            # Clean the JSON string to remove any trailing text
            extracted_json = self._clean_json_string(extracted_json)

            # Log the extracted JSON for debugging
            logger.info(f"Extracted JSON from AI image response: {extracted_json[:500]}...")

            # Try parsing extracted JSON first
            try:
                parsed_json = json.loads(extracted_json)
                logger.info("Successfully parsed JSON response from Gemini with image")
                return parsed_json
            except json.JSONDecodeError as e1:
                logger.warning(f"Failed to parse extracted JSON from image: {str(e1)}")
                # Try to fix common JSON issues
                fixed_json = self._fix_malformed_json(extracted_json)
                if fixed_json != extracted_json:
                    try:
                        parsed_json = json.loads(fixed_json)
                        logger.info("Successfully parsed fixed JSON response from Gemini with image")
                        return parsed_json
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Fixed JSON also failed: {str(e2)}")
                
                # Fallback: try parsing the original response
                logger.warning("Failed to parse extracted JSON, trying original response")
                cleaned_original = self._clean_json_string(original_response)
                parsed_json = json.loads(cleaned_original)
                logger.info("Successfully parsed JSON from original image response")
                return parsed_json

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini image response: {str(e)}")
            logger.error(f"Extracted JSON text: {extracted_json}")
            raise Exception(f"Invalid JSON response from Gemini with image: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating JSON content with image: {str(e)}", exc_info=True)
            raise
