"""
Medication Scan AI Agent for identifying medications from images.
Uses Gemini API with vision capabilities to analyze medication images.
"""
import json
import logging
import os
from typing import Dict, Any, Optional
from app.ai_agent.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class MedicationScanAgent:
    """
    AI Agent for scanning medication images and extracting medication information.
    Generates structured medication data in the format of medication_library.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize Medication Scan Agent.

        Args:
            gemini_client: GeminiClient instance. If None, creates a new one.
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.prompt_template = self._get_prompt_template()
        logger.info("MedicationScanAgent initialized")

    def _get_prompt_template(self) -> str:
        """
        Get prompt template for medication scanning.

        Returns:
            Prompt template string.
        """
        return """
You are a pharmaceutical expert AI assistant. Analyze the medication image and extract information.

Your task is to identify the medication from the image and provide structured information in JSON format.

Look for:
- Medication name (brand name and generic name if visible)
- Dosage information (strength, form: tablet, capsule, etc.)
- Frequency per day (if mentioned on packaging)
- Description (what the medication is for, active ingredients if visible)
- Notes (additional instructions, warnings, or important information)

If you cannot clearly identify a medication from the image, respond with:
{"error": "Thuốc Not found"}

Otherwise, respond with medication information in this exact JSON format:
{
  "name": "Medication Name",
  "description": "Description of what the medication is for and active ingredients",
  "dosage": "Dosage strength and form (e.g., 500mg tablet)",
  "frequency_per_day": 2,
  "notes": "Additional notes, warnings, or instructions"
}

Guidelines:
- Be precise and accurate
- Only extract information that is clearly visible in the image
- If uncertain about any field, use reasonable defaults or leave as null/empty
- frequency_per_day should be a number (1, 2, 3, etc.) or null if not visible
- Respond with valid JSON only
"""

    def scan_medication_image(self, image_path: str) -> Dict[str, Any]:
        """
        Scan medication image and extract information.

        Args:
            image_path: Path to the medication image file.

        Returns:
            Dictionary containing medication information or error.

        Raises:
            Exception: If image processing fails.
        """
        try:
            logger.info(f"Scanning medication image: {image_path}")

            # Check if image file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return {"error": "Image file not found"}

            # Generate content with image
            response = self.gemini_client.generate_json_content_with_image(
                prompt=self.prompt_template,
                image_path=image_path,
                temperature=0.1,  # Low temperature for accuracy
                max_tokens=2048
            )

            logger.info(f"Successfully scanned medication image: {response}")
            return response

        except Exception as e:
            logger.error(f"Failed to scan medication image: {str(e)}", exc_info=True)
            # Return agent error instead of "Thuốc not found"
            return {"agent_error": f"Lỗi AI Agent: {str(e)}"}