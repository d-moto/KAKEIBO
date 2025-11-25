import google.generativeai as genai
#from google import genai
import json
import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger("Kakeibo")

class OCRService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key is required")
        genai.configure(api_key=api_key)
        # gemini-1.5-flash was not found, using gemini-2.0-flash which is available
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze_image(self, image_path: str) -> List[Dict]:
        """
        Analyzes an image and returns a list of transactions found.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            prompt = """
            Analyze this image (receipt or screenshot of transaction history) and extract the transaction details.
            Return a JSON array of objects with the following fields:
            - date: string (YYYY-MM-DD format). If year is missing, assume current year.
            - amount: integer (remove currency symbols and commas)
            - description: string (store name or transaction description)
            - type: string ("Expense" or "Income")
            - payment_method: string (e.g., "Cash", "Credit Card", "Bank", "PayPay", or null if unknown)
            
            If the image is not a receipt or transaction history, return an empty array.
            Output ONLY the JSON array, no markdown formatting or other text.
            """

            response = self.model.generate_content([
                {'mime_type': 'image/jpeg', 'data': image_data},
                prompt
            ])
            
            text = response.text.strip()
            
            # Robust JSON extraction
            try:
                start_index = text.find('[')
                end_index = text.rfind(']')
                
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    json_str = text[start_index:end_index+1]
                    data = json.loads(json_str)
                else:
                    # Fallback: try to parse the whole text if no brackets found (unlikely for array)
                    data = json.loads(text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON Decode Error: {e}. Raw text: {text}")
                raise ValueError(f"Failed to parse API response: {e}")
            
            # Validate and clean data
            valid_data = []
            for item in data:
                if 'date' in item and 'amount' in item:
                    valid_data.append(item)
            
            return valid_data

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            raise e
