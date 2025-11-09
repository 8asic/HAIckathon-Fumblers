# src/agents/rewriter.py

import asyncio
from typing import Dict, Any
from src.services.model_factory import ModelFactory, ProviderType


class ArticleRewriter:
    def __init__(self):
        self.client, self.model_name, self.provider = ModelFactory.get_model()
    
    async def rewrite_neutral(self, original_text: str, bias_analysis: dict) -> str:
        """Rewrite entire article using detected biases as guidance."""
        prompt = self._create_rewrite_prompt(original_text, bias_analysis)
        
        try:
            if self.provider == ProviderType.GROQ:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=4000,
                        temperature=0.1
                    )
                )
                return response.choices[0].message.content or original_text
            elif self.provider == ProviderType.GEMINI:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.generate_content(prompt)
                )
                return response.text
            elif self.provider == ProviderType.CLAUDE:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.messages.create(
                        model=self.model_name,
                        max_tokens=4000,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                )
                return response.content[0].text
            else:
                return original_text
        except Exception as e:
            print(f"Rewriting failed: {e}")
            return original_text
    
    def _create_rewrite_prompt(self, original_text: str, bias_analysis: dict) -> str:
        """Create detailed rewrite prompt using bias analysis."""
        
        # Extract biased phrases for specific guidance
        biased_phrases = bias_analysis.get('biased_phrases', [])
        specific_guidance = ""
        
        if biased_phrases:
            specific_guidance = "SPECIFIC CHANGES NEEDED:\n"
            for phrase in biased_phrases[:10]:
                suggested = phrase.get('suggested_replacement', 'neutral language')
                specific_guidance += f"- Replace '{phrase.get('text', '')}' with {suggested} (bias: {phrase.get('bias_type', 'unknown')})\n"
        
        return f"""
        Rewrite this news article in a completely neutral, objective tone while preserving ALL factual content.

        ORIGINAL ARTICLE:
        {original_text}

        BIAS ANALYSIS SUMMARY:
        - Emotional bias score: {bias_analysis.get('emotional_bias_score', 0)}/100
        - Framing bias score: {bias_analysis.get('framing_bias_score', 0)}/100  
        - Omission bias score: {bias_analysis.get('omission_bias_score', 0)}/100
        - Overall bias: {bias_analysis.get('overall_bias_score', 0)}/100

        {specific_guidance}

        REWRITING GUIDELINES:
        1. Remove emotional/sensational language
        2. Replace judgmental terms with neutral descriptions
        3. Present multiple perspectives where relevant
        4. Use precise, factual language without exaggeration
        5. Maintain original length and structure
        6. Keep all factual information, dates, numbers, names
        7. Avoid metaphors and dramatic framing
        8. Use measured qualifiers instead of absolutes

        Return ONLY the rewritten article text, no explanations.
        """
    
    async def rewrite_title_neutral(self, original_title: str, bias_analysis: dict) -> str:
        """Rewrite title based on bias analysis."""
        if bias_analysis.get('overall_bias_score', 0) < 20:
            return original_title
            
        prompt = f"""
        Rewrite this news headline to be neutral and factual:

        ORIGINAL: {original_title}

        BIAS CONTEXT:
        - Emotional bias: {bias_analysis.get('emotional_bias_score', 0)}/100
        - Framing bias: {bias_analysis.get('framing_bias_score', 0)}/100

        GUIDELINES:
        - Remove sensationalism and emotional language
        - Keep core factual content
        - Make it concise (under 80 characters if possible)
        - Use neutral, descriptive language

        Return ONLY the rewritten headline.
        """
        
        try:
            if self.provider == ProviderType.GROQ:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=100,
                        temperature=0.1
                    )
                )
                neutral_title = response.choices[0].message.content or original_title
            elif self.provider == ProviderType.GEMINI:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.generate_content(prompt)
                )
                neutral_title = response.text
            elif self.provider == ProviderType.CLAUDE:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.messages.create(
                        model=self.model_name,
                        max_tokens=100,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                )
                neutral_title = response.content[0].text
            else:
                return original_title
            
            clean_title = neutral_title.strip().replace('"', '')
            return clean_title if 10 < len(clean_title) < 120 else original_title
            
        except Exception as e:
            print(f"Title rewriting failed: {e}")
            return original_title