# tests/test_clients.py

import asyncio
import os
import sys
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

load_dotenv()

from src.services.model_factory import ModelFactory, ProviderType
from src.agents.detector import BiasDetector
from src.agents.rewriter import ArticleRewriter
from src.agents.explainer import BiasExplainer


async def test_model_factory():
    """Test that ModelFactory can initialize all providers."""
    print("Testing ModelFactory...")
    
    try:
        client, model_name, provider = ModelFactory.get_model()
        print(f"SUCCESS: ModelFactory - {provider.value} - {model_name}")
        return True
    except Exception as e:
        print(f"FAILED: ModelFactory - {e}")
        return False


async def test_bias_detector():
    """Test bias detection with sample article."""
    print("\nTesting BiasDetector...")
    
    sample_article = """
    Amazon is absolutely crushing it in the AI race after being a total laggard for years. 
    Their amazing comeback story shows they're destroying the competition with incredible innovation.
    """
    
    try:
        detector = BiasDetector()
        result = await detector.detect_biases(sample_article)
        
        print("SUCCESS: Bias detection completed")
        print(f"  Overall bias score: {result.get('overall_bias_score')}")
        print(f"  Biased phrases found: {len(result.get('biased_phrases', []))}")
        return True
    except Exception as e:
        print(f"FAILED: Bias detection - {e}")
        return False


async def test_article_rewriter():
    """Test article rewriting."""
    print("\nTesting ArticleRewriter...")
    
    sample_article = """
    The company's disastrous performance shocked investors who were utterly disappointed.
    This catastrophic failure will undoubtedly lead to massive layoffs and financial ruin.
    """
    
    sample_bias_analysis = {
        "emotional_bias_score": 85,
        "framing_bias_score": 70,
        "omission_bias_score": 40,
        "overall_bias_score": 75,
        "biased_phrases": [
            {
                "text": "disastrous performance",
                "bias_type": "emotional",
                "suggested_replacement": "challenging performance"
            }
        ]
    }
    
    try:
        rewriter = ArticleRewriter()
        result = await rewriter.rewrite_neutral(sample_article, sample_bias_analysis)
        
        print("SUCCESS: Article rewriting completed")
        print(f"  Original length: {len(sample_article)}")
        print(f"  Rewritten length: {len(result)}")
        return True
    except Exception as e:
        print(f"FAILED: Article rewriting - {e}")
        return False


async def test_bias_explainer():
    """Test bias explanation."""
    print("\nTesting BiasExplainer...")
    
    sample_bias_analysis = {
        "emotional_bias_score": 75,
        "summary": "The article uses strong emotional language and sensational framing."
    }
    
    try:
        explainer = BiasExplainer()
        result = await explainer.explain_biases(sample_bias_analysis)
        
        print("SUCCESS: Bias explanation completed")
        print(f"  Explanation preview: {result[:100]}...")
        return True
    except Exception as e:
        print(f"FAILED: Bias explanation - {e}")
        return False


async def test_individual_providers():
    """Test each provider individually."""
    print("\nTesting Individual Providers...")
    
    providers = [
        ("Gemini", ModelFactory.get_gemini_model),
        ("Groq", ModelFactory.get_groq_client),
        ("Claude", ModelFactory.get_claude_client),
    ]
    
    success_count = 0
    for name, method in providers:
        try:
            client, model_name, provider = method()
            print(f"SUCCESS: {name} - {model_name}")
            success_count += 1
        except Exception as e:
            print(f"FAILED: {name} - {e}")
    
    return success_count > 0


async def main():
    """Run all tests."""
    print("Starting Client Tests")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ['GEMINI_API_KEY', 'GROQ_API_KEY']
    print("Checking environment variables:")
    for var in required_vars:
        if os.getenv(var):
            print(f"  SET: {var}")
        else:
            print(f"  MISSING: {var}")
    
    # Run tests
    tests = [
        test_model_factory(),
        test_bias_detector(),
        test_article_rewriter(), 
        test_bias_explainer(),
        test_individual_providers()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # Process results
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            processed_results.append(False)
        else:
            processed_results.append(result)
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    passed_count = sum(1 for r in processed_results if r is True)
    print(f"  Passed: {passed_count}/{len(processed_results)}")
    
    if passed_count == len(processed_results):
        print("ALL TESTS PASSED: Clients are working correctly")
    else:
        print("SOME TESTS FAILED: Review errors above")


if __name__ == "__main__":
    asyncio.run(main())