import os
import sys
import asyncio
from dotenv import load_dotenv

# Fix import path - go up 3 levels from tests/debug/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

load_dotenv()

async def test_llm_connection():
    """Test if LLM providers are working."""
    from src.services.model_factory import ModelFactory
    
    print("Testing LLM Connections...")
    print("=" * 50)
    
    try:
        # Test model factory
        client, model_name, provider = ModelFactory.get_model()
        print(f"Model Factory: {provider.value} - {model_name}")
        
        # Test simple completion
        test_prompt = "Respond with just: TEST_SUCCESS"
        
        if provider.value == "groq":
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=10,
                    temperature=0.1
                )
            )
            result = response.choices[0].message.content
        elif provider.value == "gemini":
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.generate_content(test_prompt)
            )
            result = response.text
        else:  # claude
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.messages.create(
                    model=model_name,
                    max_tokens=10,
                    temperature=0.1,
                    messages=[{"role": "user", "content": test_prompt}]
                )
            )
            result = response.content[0].text
        
        print(f"LLM Response: {result}")
        return True
        
    except Exception as e:
        print(f"LLM Connection Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bias_detector_directly():
    """Test bias detector with a clearly biased article."""
    from src.agents.detector import BiasDetector
    
    print("\nTesting Bias Detector Directly...")
    print("=" * 50)
    
    # Clearly biased article
    biased_article = """
    The government's disastrous climate policy is absolutely destroying our economy. 
    These radical environmentalists are pushing insane proposals that will ruin everything. 
    The catastrophic new regulations will undoubtedly lead to massive job losses and economic collapse.
    This is clearly the worst policy decision in history and will have devastating consequences.
    """
    
    detector = BiasDetector()
    result = await detector.detect_biases(biased_article)
    
    print(f"Bias Analysis Result:")
    print(f"  Overall Score: {result.get('overall_bias_score')}")
    print(f"  Emotional Score: {result.get('emotional_bias_score')}")
    print(f"  Framing Score: {result.get('framing_bias_score')}")
    print(f"  Summary: {result.get('summary')}")
    print(f"  Biased Phrases: {len(result.get('biased_phrases', []))}")
    
    # Check if it's the fallback response
    if result.get('summary', '').startswith('Bias analysis unavailable'):
        print("USING FALLBACK RESPONSE - LLM is not working")
        return False
    else:
        print("REAL LLM RESPONSE - Bias detector is working")
        return True

def test_model_factory_directly():
    """Test ModelFactory directly to see which providers work."""
    print("Testing ModelFactory Providers...")
    print("=" * 50)
    
    from src.services.model_factory import ModelFactory
    
    providers_to_test = [
        ("Groq", ModelFactory.get_groq_client),
        ("Gemini", ModelFactory.get_gemini_model), 
        ("Claude", ModelFactory.get_claude_client)
    ]
    
    working_providers = []
    
    for name, method in providers_to_test:
        try:
            client, model_name, provider = method()
            print(f"✅ {name}: {model_name}")
            working_providers.append(name)
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    return working_providers

if __name__ == "__main__":
    print("LLM Debug Diagnostic")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ['GEMINI_API_KEY', 'GROQ_API_KEY', 'ANTHROPIC_API_KEY']
    print("Environment Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: Missing")
    
    # Test each provider directly
    working_providers = test_model_factory_directly()
    
    if working_providers:
        print(f"\nWorking providers: {', '.join(working_providers)}")
        
        # Run async tests with the first working provider
        print(f"\nRunning detailed tests with {working_providers[0]}...")
        connection_ok = asyncio.run(test_llm_connection())
        detector_ok = asyncio.run(test_bias_detector_directly())
        
        print("\n" + "=" * 60)
        if connection_ok and detector_ok:
            print("ALL TESTS PASSED - LLM is working correctly")
        else:
            print("TESTS FAILED - Check LLM configuration")
    else:
        print("\n❌ NO WORKING LLM PROVIDERS - Check API keys and connectivity")