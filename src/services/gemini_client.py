import google.generativeai as genai
import json
import os
from typing import Dict, List, Any

from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    """Client for interacting with Google's Gemini AI for bias analysis."""
    
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        
        model_names = [
            'models/gemini-2.0-flash',
            'models/gemini-2.0-flash-001',
            'models/gemini-flash-latest',
            'models/gemini-2.0-flash-lite',
            'models/gemini-pro-latest',
            'models/gemma-3-27b-it',
            'models/gemini-2.5-flash'
        ]
        
        self.model = None
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                test_response = self.model.generate_content("Test response")
                if test_response.text:
                    print(f"Loaded model: {model_name}")
                    break
            except Exception:
                continue
        
        if not self.model:
            raise RuntimeError("No compatible Gemini model found")

    def analyze_bias(self, article_text: str) -> Dict[str, Any]:
        """Analyze news article text for various types of media bias.
        
        Args:
            article_text: The text content of the news article to analyze
            
        Returns:
            Dictionary containing bias scores, identified phrases, and analysis summary
        """
        if not article_text or len(article_text.strip()) < 10:
            return self._get_fallback_response()
            
        prompt = f"""
        Analyze this news article for media biases:

        ARTICLE: {article_text}

        Check for these bias types:
        1. Emotional language (loaded words, sensationalism)
        2. Framing bias (oversimplification, binary thinking)
        3. Omission of important context or facts
        4. Partisan or ideological language

        Return ONLY valid JSON with this exact structure:
        {{
            "emotional_bias_score": 0-100,
            "framing_bias_score": 0-100,
            "omission_bias_score": 0-100,
            "overall_bias_score": 0-100,
            "biased_phrases": [
                {{
                    "text": "exact phrase from article",
                    "bias_type": "emotional/framing/omission/partisan",
                    "explanation": "why this phrasing is biased"
                }}
            ],
            "summary": "brief explanation of main biases found"
        }}

        Return ONLY the JSON object, no additional text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            print(f"Raw response preview: {response.text[:150]}...")
            result = self._extract_json(response.text)
            
            if isinstance(result, dict) and 'overall_bias_score' in result:
                return result
            else:
                print("Response missing expected structure")
                return self._get_fallback_response()
                
        except Exception as e:
            print(f"Gemini analysis error: {e}")
            return self._get_fallback_response()

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from model response text."""
        try:
            cleaned = text.strip().replace('```json', '').replace('```', '').strip()
            
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            
            if start == -1 or end == 0:
                print("No JSON structure found in response")
                return self._get_fallback_response()
                
            json_str = cleaned[start:end]
            
            if not json_str.strip().startswith('{'):
                print("Extracted text doesn't start with JSON object")
                return self._get_fallback_response()
                
            print(f"Extracted JSON length: {len(json_str)} chars")
            parsed_json = json.loads(json_str)
            
            required_fields = [
                'emotional_bias_score', 
                'framing_bias_score', 
                'omission_bias_score', 
                'overall_bias_score'
            ]
            
            if all(field in parsed_json for field in required_fields):
                return parsed_json
            else:
                print("Missing required fields in JSON response")
                return self._get_fallback_response()
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return self._get_fallback_response()
        except Exception as e:
            print(f"JSON extraction failed: {e}")
            return self._get_fallback_response()

    def _get_fallback_response(self) -> Dict[str, Any]:
        """Return a fallback response when analysis fails."""
        return {
            "emotional_bias_score": 50,
            "framing_bias_score": 50,
            "omission_bias_score": 50,
            "overall_bias_score": 50,
            "biased_phrases": [],
            "summary": "Analysis unavailable - using fallback"
        }