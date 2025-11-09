# src/services/claude_client.py

import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from .model_factory import ModelFactory

load_dotenv()


class ClaudeClient:
    def __init__(self):
        self.client, self.model_name, self.provider = ModelFactory.get_model()
        
    def analyze_bias(self, article_text: str) -> Dict[str, Any]:
        if not article_text or len(article_text.strip()) < 10:
            return self._get_fallback_response()
            
        prompt = self._create_bias_analysis_prompt(article_text)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.1,
                system="You are an expert media bias analyst. Always respond with valid JSON.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.content[0].text
            result = self._extract_json(result_text)
            
            if self._validate_response(result):
                return result
            else:
                return self._get_fallback_response()
                
        except Exception:
            return self._get_fallback_response()

    def _create_bias_analysis_prompt(self, article_text: str) -> str:
        return f"""
        Analyze this news article for media biases and return ONLY valid JSON:

        ARTICLE: {article_text}

        Analyze for these bias types:
        1. Emotional language (loaded words, sensationalism, exaggeration)
        2. Framing bias (oversimplification, binary thinking, selective framing)
        3. Omission bias (missing context, important facts, alternative views)
        4. Partisan language (ideological slant, political leaning)

        Return JSON with this exact structure:
        {{
            "emotional_bias_score": 0-100,
            "framing_bias_score": 0-100,
            "omission_bias_score": 0-100,
            "overall_bias_score": 0-100,
            "biased_phrases": [
                {{
                    "text": "exact phrase from article",
                    "bias_type": "emotional/framing/omission/partisan",
                    "explanation": "detailed explanation of why this is biased"
                }}
            ],
            "summary": "comprehensive analysis of main biases found"
        }}
        """

    def _extract_json(self, text: str) -> Dict[str, Any]:
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = text[start:end]
                return json.loads(json_str)
            return self._get_fallback_response()
        except:
            return self._get_fallback_response()

    def _validate_response(self, response: Dict[str, Any]) -> bool:
        required_fields = [
            'emotional_bias_score', 
            'framing_bias_score', 
            'omission_bias_score', 
            'overall_bias_score'
        ]
        return all(field in response for field in required_fields)

    def _get_fallback_response(self) -> Dict[str, Any]:
        return {
            "emotional_bias_score": 50,
            "framing_bias_score": 50,
            "omission_bias_score": 50,
            "overall_bias_score": 50,
            "biased_phrases": [],
            "summary": "Analysis unavailable"
        }