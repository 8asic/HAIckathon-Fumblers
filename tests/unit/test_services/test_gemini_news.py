# tests/unit/test_services/test_gemini_news.py

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.gemini_client import GeminiClient
from src.services.news_client import NewsClient


async def test_full_pipeline():
    """Test the complete integration between Gemini and NewsAPI services."""
    print("Testing Gemini + NewsAPI.ai Integration")
    
    print("\n1. Testing Gemini client...")
    try:
        gemini = GeminiClient()
        
        test_article = """
        The radical climate policy will destroy our economy and create catastrophic unemployment. 
        Climate alarmists are pushing dangerous proposals that will ruin everything.
        This extreme green agenda is clearly a terrible idea that will lead to unprecedented disaster.
        """
        
        bias_analysis = gemini.analyze_bias(test_article)
        print("Gemini analysis completed")
        print(f"Overall bias score: {bias_analysis.get('overall_bias_score', 'N/A')}")
        print(f"Summary: {bias_analysis.get('summary', 'No summary')}")
        
        biased_phrases = bias_analysis.get('biased_phrases', [])
        if biased_phrases:
            print(f"Found {len(biased_phrases)} biased phrases")
            for phrase in biased_phrases[:3]:
                print(f"   - '{phrase.get('text', '')}' ({phrase.get('bias_type', 'unknown')})")
                
    except Exception as e:
        print(f"Gemini failed: {e}")
        return
    
    print("\n2. Testing NewsAPI.ai client with climate change articles...")
    try:
        news_client = NewsClient()
        articles = await news_client.fetch_articles("climate change", 3)
        
        if articles:
            print(f"NewsAPI.ai fetched {len(articles)} articles")
            for i, article in enumerate(articles):
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                api_source = article.get('api_source', 'Unknown')
                print(f"   {i+1}. {title[:80]}...")
                print(f"      Source: {source} | API: {api_source}")
        else:
            print("NewsAPI.ai failed - check API key")
            return
            
    except Exception as e:
        print(f"NewsAPI.ai failed: {e}")
        return
    
    print("\n3. Testing full pipeline with real climate articles...")
    if articles:
        for i, article in enumerate(articles):
            print(f"\nAnalyzing Article {i+1}: {article['title'][:60]}...")
            
            content = article.get('content') or article.get('description') or "No content available"
            
            if content and content != "No content available" and len(content) > 100:
                print(f"   Content length: {len(content)} chars")
                analysis = gemini.analyze_bias(content)
                bias_score = analysis.get('overall_bias_score', 'N/A')
                print(f"   Analysis completed - Bias score: {bias_score}/100")
                
                if bias_score > 60:
                    biased_phrases = analysis.get('biased_phrases', [])
                    if biased_phrases:
                        print(f"   Top biased phrase: '{biased_phrases[0].get('text', '')}'")
            else:
                print(f"   Article has insufficient content ({len(content)} chars)")
    
    print("\nFull pipeline test completed")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())