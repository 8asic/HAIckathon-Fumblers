import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.orchestrator import BiasAnalysisOrchestrator
from src.services.news_client import NewsClient


async def test_complete_system():
    """Test the complete bias detection and title rewriting system."""
    
    print("🧪 Testing Complete Bias Detection & Title Rewriting System")
    print("=" * 60)
    
    orchestrator = BiasAnalysisOrchestrator()
    
    # Test 1: Single article with biased title
    print("\n1. Testing single article with biased title...")
    test_article = {
        "title": "Climate Alarmists Push Radical Policies That Will Destroy Our Economy",
        "content": "Extreme environmentalists are pushing dangerous climate policies that will undoubtedly wreck our economy and cause massive job losses. Their radical agenda threatens to impose unbearable costs on hardworking families while achieving virtually nothing."
    }
    
    result = await orchestrator.analyze_article(
        article_text=test_article["content"],
        original_title=test_article["title"]
    )
    
    print(f"   📊 Bias Score: {result['analysis']['overall_bias_score']}/100")
    print(f"   📝 Original Title: {result['original_title']}")
    print(f"   🔄 Neutral Title:  {result['neutral_title']}")
    print(f"   ✅ Title Changed: {result['original_title'] != result['neutral_title']}")
    
    # Test 2: Real news articles
    print("\n2. Testing with real news articles...")
    try:
        news_client = NewsClient()
        articles = await news_client.fetch_articles("climate change", 2)
        
        if articles:
            for i, article in enumerate(articles, 1):
                print(f"\n   📰 Article {i}: {article['title'][:60]}...")
                
                analysis = await orchestrator.analyze_article(
                    article_text=article['content'],
                    original_title=article['title']
                )
                
                print(f"      Bias Score: {analysis['analysis']['overall_bias_score']}/100")
                print(f"      Title Rewritten: {analysis['original_title'] != analysis['neutral_title']}")
                
                if analysis['original_title'] != analysis['neutral_title']:
                    print(f"      Original: {analysis['original_title']}")
                    print(f"      Neutral:  {analysis['neutral_title']}")
        else:
            print("   ❌ No articles fetched")
            
    except Exception as e:
        print(f"   ❌ News test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 System testing completed!")


if __name__ == "__main__":
    asyncio.run(test_complete_system())