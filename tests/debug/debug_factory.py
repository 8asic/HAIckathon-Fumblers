# tests/debug/debug_factory.py

import os
import sys
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

load_dotenv()

from src.services.model_factory import ModelFactory


def debug_model_factory():
    """Debug ModelFactory provider initialization and main method."""
    print("Debugging ModelFactory...")
    
    # Test each provider individually
    providers = [
        ("Gemini", ModelFactory.get_gemini_model),
        ("Groq", ModelFactory.get_groq_client), 
    ]
    
    for name, method in providers:
        print(f"\nTesting {name}...")
        try:
            result = method()
            print(f"SUCCESS: {name} - {result[1]}")
        except Exception as e:
            print(f"FAILED: {name} - {e}")
            import traceback
            traceback.print_exc()
    
    # Test the main get_model method
    print(f"\nTesting get_model()...")
    try:
        result = ModelFactory.get_model()
        print(f"SUCCESS: get_model() - {result[1]} - {result[2].value}")
    except Exception as e:
        print(f"FAILED: get_model() - {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_model_factory()