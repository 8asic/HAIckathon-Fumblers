# src/agents/detector.py

import asyncio
import json
from typing import Dict, Any
from src.services.model_factory import ModelFactory, ProviderType


class BiasDetector:
    def __init__(self):
        self.client, self.model_name, self.provider = ModelFactory.get_model()
    
    async def detect_biases(self, article_text: str) -> Dict[str, Any]:
        """Async bias detection with provider-specific handling."""
        if not article_text or len(article_text.strip()) < 10:
            return self._get_fallback_response()
        
        prompt = self._create_bias_analysis_prompt(article_text)
        
        try:
            if self.provider == ProviderType.GROQ:
                return await self._analyze_chat_completion(prompt)
            elif self.provider == ProviderType.GEMINI:
                return await self._analyze_gemini(prompt)
            elif self.provider == ProviderType.CLAUDE:
                return await self._analyze_claude(prompt)
            else:
                return self._get_fallback_response()
        except Exception as e:
            print(f"Bias detection failed: {e}")
            return self._get_fallback_response()
    
    async def _analyze_chat_completion(self, prompt: str) -> Dict[str, Any]:
        """Analysis for Groq chat completion APIs."""
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert media bias analyst. Analyze articles for specific, rewritable biases and return valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
        )
        
        result_text = response.choices[0].message.content
        if result_text is None:
            return self._get_fallback_response()
        
        return self._extract_json(result_text)
    
    async def _analyze_gemini(self, prompt: str) -> Dict[str, Any]:
        """Analysis for Gemini client."""
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.client.generate_content(prompt)
        )
        return self._extract_json(response.text)
    
    async def _analyze_claude(self, prompt: str) -> Dict[str, Any]:
        """Analysis for Claude client."""
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                temperature=0.1,
                system="You are an expert media bias analyst. Always respond with valid JSON.",
                messages=[{"role": "user", "content": prompt}]
            )
        )
        
        result_text = response.content[0].text
        return self._extract_json(result_text)
        
    def _create_bias_analysis_prompt(self, article_text: str) -> str:
        return f"""
        Analyze this news article for specific, rewritable biases:

        ARTICLE: {article_text}

        Identify specific phrases that need rewriting in these categories:
        1. EMOTIONAL LANGUAGE: Loaded words, sensationalism, exaggeration
        2. FRAMING BIAS: Oversimplification, binary thinking, selective framing  
        3. OMISSION: Missing context, important facts, alternative views
        4. PARTISAN LANGUAGE: Ideological slant, political leaning
        5. JUDGMENTAL TERMS: Value judgments, moralizing language
        6. METAPHORS/DRAMA: Dramatic framing, war/sports metaphors

        Return JSON with this exact structure:
        {{
            "emotional_bias_score": 0-100,
            "framing_bias_score": 0-100,
            "omission_bias_score": 0-100,
            "overall_bias_score": 0-100,
            "biased_phrases": [
                {{
                    "text": "exact problematic phrase from article",
                    "bias_type": "emotional/framing/omission/partisan/judgmental/metaphor",
                    "explanation": "detailed explanation of why this phrasing is biased",
                    "suggested_replacement": "neutral alternative phrasing"
                }}
            ],
            "summary": "comprehensive analysis of main bias patterns found"
        }}

        Be specific and actionable for rewriting purposes.
        """
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from model response."""
        try:
            cleaned = text.strip().replace('```json', '').replace('```', '').strip()
            
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            
            if start == -1 or end == 0:
                return self._get_fallback_response()
                
            json_str = cleaned[start:end]
            return json.loads(json_str)
            
        except json.JSONDecodeError:
            return self._get_fallback_response()
        except Exception:
            return self._get_fallback_response()

    def _get_fallback_response(self) -> Dict[str, Any]:
        """Return a fallback response when analysis fails."""
        return {
            "emotional_bias_score": 50,
            "framing_bias_score": 50,
            "omission_bias_score": 50,
            "overall_bias_score": 50,
            "biased_phrases": [],
            "summary": "Bias analysis unavailable - using fallback response"
        }