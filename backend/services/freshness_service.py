import os
import base64
import re
import json
from datetime import datetime
from typing import Dict, Any
import google.generativeai as genai
from models.schemas import FreshnessRequest, FreshnessResponse, MarketValue

class FreshnessService:
    def __init__(self):
        # Initialize Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    async def analyze_freshness(self, request: FreshnessRequest) -> FreshnessResponse:
        try:
            # Decode base64 image
            image_data = base64.b64decode(request.image_data.split(',')[1] if ',' in request.image_data else request.image_data)

            # Create the prompt for Gemini
            prompt = """You are an expert fish quality assessor for commercial fishing operations. Analyze this fish image and provide a detailed freshness assessment.

Evaluate the following criteria on a scale of 0-100:
1. **Bleeding** (0-100): How well was the fish bled? Look for blood removal completeness, proper technique signs.
2. **Ice Contact** (0-100): Quality of ice coverage and contact. Look for proper icing, coverage of gills and body.
3. **Bruising** (0-100): Assess any physical damage, bruising, or handling marks. Higher score = less damage.

Based on these scores, calculate an overall score and assign a market grade:
- Grade A: 85-100 overall (premium quality)
- Grade B: 70-84 overall (good quality)
- Grade C: 55-69 overall (fair quality)
- Grade D: 0-54 overall (poor quality)

Also provide:
- A single actionable "next action" recommendation (1-2 sentences)
- Estimated price per pound (premium fish: $10-15, good: $7-10, fair: $4-7, poor: $2-4)
- List of 2-4 specific quality factors observed

Respond ONLY with valid JSON in this exact format:
{
  "bleeding": 85,
  "ice_contact": 90,
  "bruising": 88,
  "overall": 88,
  "grade": "A",
  "next_action": "Excellent handling so far. Continue current icing technique.",
  "estimated_price": 12.50,
  "quality_factors": ["Excellent bleeding", "Good ice contact", "Minimal bruising"]
}"""

            # Call Gemini API with image
            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])

            # Parse response
            result_text = response.text.strip()

            # Extract JSON from markdown code blocks if present
            if "```json" in result_text:
                result_text = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL).group(1)
            elif "```" in result_text:
                result_text = re.search(r'```\s*(.*?)\s*```', result_text, re.DOTALL).group(1)

            # Parse JSON
            analysis = json.loads(result_text)

            # Construct response
            return FreshnessResponse(
                bleeding=analysis['bleeding'],
                ice_contact=analysis['ice_contact'],
                bruising=analysis['bruising'],
                overall=analysis['overall'],
                grade=analysis['grade'],
                next_action=analysis['next_action'],
                timestamp=datetime.now().isoformat(),
                market_value=MarketValue(
                    estimated_price=analysis['estimated_price'],
                    quality_factors=analysis['quality_factors']
                )
            )

        except Exception as e:
            # Fallback to reasonable defaults on error
            print(f"Error analyzing freshness: {str(e)}")
            return FreshnessResponse(
                bleeding=70,
                ice_contact=70,
                bruising=70,
                overall=70,
                grade='B',
                next_action="Unable to fully analyze image. Ensure good ice contact and proper bleeding.",
                timestamp=datetime.now().isoformat(),
                market_value=MarketValue(
                    estimated_price=8.00,
                    quality_factors=["Analysis incomplete - maintain standard handling practices"]
                )
            )