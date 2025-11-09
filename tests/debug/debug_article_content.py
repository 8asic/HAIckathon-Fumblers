import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

load_dotenv()

async def debug_article_content():
    """Debug what's actually being sent to the LLM."""
    from src.services.news_client import NewsClient
    from src.agents.detector import BiasDetector
    
    print("Debugging Article Content")
    print("=" * 50)
    
    # Fetch articles
    client = NewsClient()
    articles = await client.fetch_articles(None, 2)
    
    if not articles:
        print("No articles fetched")
        return
    
    for i, article in enumerate(articles):
        print(f"\n--- Article {i+1} ---")
        print(f"Title: {article['title']}")
        print(f"Body length: {len(article['body'])} chars")
        print(f"Body preview: {article['body'][:200]}...")
        print(f"Category: {article['category']}")
        
        # Test bias detection on this article
        print("\nTesting bias detection...")
        detector = BiasDetector()
        result = await detector.detect_biases(article['body'])
        
        print(f"Result: {result.get('summary', 'No summary')}")
        print(f"Scores: Overall={result.get('overall_bias_score')}, "
              f"Emotional={result.get('emotional_bias_score')}")
        
        if "fallback" in result.get('summary', '').lower():
            print("❌ FALLBACK RESPONSE")
            # Check if article body is problematic
            if len(article['body']) < 50:
                print("⚠️  Article body too short")
            if "original article not provided" in article['body'].lower():
                print("⚠️  Article body contains placeholder text")
        else:
            print("✅ REAL ANALYSIS")

if __name__ == "__main__":
    asyncio.run(debug_article_content())