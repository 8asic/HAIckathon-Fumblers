import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agents.rewriter import ArticleRewriter
from src.agents.detector import BiasDetector


async def test_title_rewriting():
    """Test that biased titles get rewritten to neutral versions."""
    
    # Test cases: biased titles and expected neutral versions
    test_cases = [
        {
            "biased_title": "Climate Alarmists Push Radical Policies That Will Destroy Economy",
            "expected_keywords": ["climate", "policy", "economic"]  # Should contain these
        },
        {
            "biased_title": "Catastrophic Warming Dooms Planet to Unprecedented Disaster", 
            "expected_keywords": ["warming", "climate", "impact"]
        },
        {
            "biased_title": "New Study Shows Promising Climate Solutions",
            "expected_keywords": ["study", "climate", "solutions"]  # Already neutral
        }
    ]
    
    rewriter = ArticleRewriter()
    detector = BiasDetector()
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: '{test_case['biased_title']}'")
        
        # Analyze bias in the title (by using it as "content")
        bias_analysis = detector.analyze_bias(test_case['biased_title'])
        bias_score = bias_analysis.get('overall_bias_score', 0)
        print(f"  Bias score: {bias_score}/100")
        
        # Rewrite title
        neutral_title = await rewriter.rewrite_title_neutral(
            test_case['biased_title'], 
            bias_analysis
        )
        
        print(f"  Original: {test_case['biased_title']}")
        print(f"  Neutral:  {neutral_title}")
        
        # Check if rewriting occurred
        if neutral_title != test_case['biased_title']:
            print("  ✅ Title was rewritten")
        else:
            print("  ℹ️  Title unchanged (likely low bias)")
        
        # Verify neutral title contains expected keywords
        contains_keywords = any(
            keyword in neutral_title.lower() 
            for keyword in test_case['expected_keywords']
        )
        if contains_keywords:
            print("  ✅ Neutral title maintains core meaning")
        else:
            print("  ⚠️  Neutral title may have lost core meaning")


if __name__ == "__main__":
    asyncio.run(test_title_rewriting())