# src/agents/explainer.py

import asyncio
from src.services.model_factory import ModelFactory, ProviderType


class BiasExplainer:
    def __init__(self):
        self.client, self.model_name, self.provider = ModelFactory.get_model()
    
    async def explain_biases(self, bias_analysis: dict) -> str:
        """Generate educational explanation of detected biases."""
        prompt = f"""
        Explain these media biases in simple, educational terms (2-3 paragraphs):
        
        Bias Analysis: {bias_analysis.get('summary', 'No analysis available')}
        
        Focus on:
        - How these specific biases affect reader perception
        - Why neutral reporting matters for informed decisions
        - Practical tips for recognizing similar biases
        
        Write in accessible language for general readers.
        """
        
        try:
            if self.provider == ProviderType.GROQ:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=500,
                        temperature=0.3
                    )
                )
                return response.choices[0].message.content or "Unable to generate explanation."
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
                        max_tokens=500,
                        temperature=0.3,
                        messages=[{"role": "user", "content": prompt}]
                    )
                )
                return response.content[0].text
            else:
                return "Unable to generate explanation at this time."
        except Exception as e:
            return "Unable to generate explanation at this time."