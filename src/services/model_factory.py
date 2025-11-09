# src/services/model_factory.py

import os
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq
import anthropic
from enum import Enum

load_dotenv()

class ProviderType(Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    CLAUDE = "claude"

class ModelFactory:
    GEMINI_MODELS = [
        'models/gemini-2.0-flash',
        'models/gemini-2.0-flash-001', 
        'models/gemini-flash-latest',
        'models/gemini-2.0-flash-lite',
        'models/gemini-1.5-flash-latest',
    ]
    
    GROQ_MODELS = [
        'llama-3.1-70b-versatile',
        'llama-3.1-8b-instant',
        'llama-3.1-405b-reasoning',
    ]
    
    CLAUDE_MODELS = [
        'claude-3-5-sonnet-20241022',
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
    ]
    
    @classmethod
    def get_model(cls):
        """Get the best available model (Groq first, then Gemini, then Claude)."""
        # Try Groq first (completely free)
        try:
            return cls.get_groq_client()
        except Exception as e:
            print(f"Groq failed: {e}")
            pass
            
        # Try Gemini Flash second (free tier)
        try:
            return cls.get_gemini_model()
        except Exception as e:
            print(f"Gemini failed: {e}")
            pass
            
        # Try Claude as fallback (paid but high quality)
        try:
            return cls.get_claude_client()
        except Exception as e:
            print(f"Claude failed: {e}")
            pass
            
        raise RuntimeError("No AI models available")
    
    @classmethod
    def get_gemini_model(cls):
        """Get Gemini model - returns (client, model_name, provider_type)."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        
        for model_name in cls.GEMINI_MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                test_response = model.generate_content("Test")
                if test_response.text:
                    return model, model_name, ProviderType.GEMINI
            except Exception:
                continue
        
        raise RuntimeError("No compatible Gemini model found")

    @classmethod
    def get_groq_client(cls):
        """Get Groq client - returns (client, model_name, provider_type)."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        client = Groq(api_key=api_key)
        
        for model_name in cls.GROQ_MODELS:
            try:
                test_response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
                if test_response.choices[0].message.content:
                    return client, model_name, ProviderType.GROQ
            except Exception:
                continue
        
        raise RuntimeError("No compatible Groq model found")

    @classmethod
    def get_claude_client(cls):
        """Get Claude client - returns (client, model_name, provider_type)."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        for model_name in cls.CLAUDE_MODELS:
            try:
                # Test the model with a simple message
                test_response = client.messages.create(
                    model=model_name,
                    max_tokens=5,
                    messages=[{"role": "user", "content": "Test"}]
                )
                if test_response.content:
                    return client, model_name, ProviderType.CLAUDE
            except Exception:
                continue
        
        raise RuntimeError("No compatible Claude model found")