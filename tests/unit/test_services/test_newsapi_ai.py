# tests/unit/test_services/test_newsapi_ai.py

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.news_client import NewsClient


async def test_newsapi_ai_full_articles():
    """Test NewsAPI.ai with full article content."""
    print("Testing NewsAPI.ai Full Articles")
    
    client = NewsClient()
    
    test_queries = [
        "climate change",
        "global warming", 
        "renewable energy",
        "carbon emissions"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        articles = await client.fetch_articles(query, 3)
        
        if not articles:
            print(f"No articles found for '{query}'")
            continue
            
        print(f"Found {len(articles)} articles")
        
        for i, article in enumerate(articles):
            print(f"\nArticle {i+1}:")
            print(f"   Title: {article.get('title', 'No title')}")
            print(f"   Source: {article.get('source', 'Unknown')}")
            print(f"   API Source: {article.get('api_source', 'Unknown')}")
            print(f"   Full Content: {article.get('full_content', False)}")
            
            content = article.get('content', '')
            print(f"   Content Length: {len(content)} characters")
            print(f"   Content Preview: {content[:150]}...")
            
            if article.get('sentiment') is not None:
                sentiment = article.get('sentiment', 0)
                print(f"   Sentiment: {sentiment}")
            if article.get('categories'):
                print(f"   Categories: {', '.join(article.get('categories', [])[:3])}")
            
            print(f"   URL: {article.get('url', 'No URL')}")


async def test_article_content_quality():
    """Test the quality and length of article content for bias analysis."""
    print("\n" + "="*60)
    print("Testing Article Content Quality for Bias Analysis")
    
    client = NewsClient()
    articles = await client.fetch_articles("climate change", 5)
    
    if not articles:
        print("No articles to analyze")
        return
    
    content_stats = []
    for i, article in enumerate(articles):
        content = article.get('content', '')
        stats = {
            'article_num': i + 1,
            'title': article.get('title', '')[:50] + '...',
            'title_length': len(article.get('title', '')),
            'content_length': len(content),
            'word_count': len(content.split()),
            'has_full_content': article.get('full_content', False),
            'api_source': article.get('api_source', 'unknown'),
            'is_usable': len(content) > 200
        }
        content_stats.append(stats)
    
    print("\nContent Statistics:")
    usable_count = 0
    for stats in content_stats:
        status = "PASS" if stats['is_usable'] else "FAIL"
        print(f"   {status} Article {stats['article_num']} ({stats['api_source']}):")
        print(f"     Title: {stats['title']}")
        print(f"     Content: {stats['content_length']} chars, {stats['word_count']} words")
        print(f"     Full Content: {stats['has_full_content']}")
        print(f"     Usable for Analysis: {stats['is_usable']}")
        
        if stats['is_usable']:
            usable_count += 1
    
    print(f"\nSummary: {usable_count}/{len(content_stats)} articles usable for bias analysis")


async def test_climate_specific_queries():
    """Test queries specifically related to climate change themes."""
    print("\n" + "="*60)
    print("Testing Climate Change Specific Queries")
    
    client = NewsClient()
    
    climate_queries = [
        "climate change policy",
        "IPCC report",
        "carbon neutral",
        "extreme weather climate",
        "climate adaptation"
    ]
    
    for query in climate_queries:
        print(f"\nTesting: '{query}'")
        articles = await client.fetch_articles(query, 2)
        
        if articles:
            print(f"Found {len(articles)} articles")
            for article in articles:
                print(f"   {article.get('title')}")
                content_lower = article.get('content', '').lower()
                climate_keywords = ['climate', 'warming', 'emissions', 'carbon', 'environment']
                matches = [kw for kw in climate_keywords if kw in content_lower]
                print(f"   Climate keywords found: {len(matches)}")
        else:
            print("   No articles found")


async def test_fallback_mechanism():
    """Test what happens when primary API fails."""
    print("\n" + "="*60)
    print("Testing Fallback Mechanism")
    
    original_key = os.getenv("NEWSAPI_AI_KEY")
    os.environ["NEWSAPI_AI_KEY"] = "invalid_key"
    
    client = NewsClient()
    articles = await client.fetch_articles("climate change", 2)
    
    if original_key:
        os.environ["NEWSAPI_AI_KEY"] = original_key
    
    if articles:
        print(f"Fallback worked! Got {len(articles)} articles from {articles[0].get('api_source')}")
        for article in articles:
            print(f"   {article.get('title')}")
    else:
        print("All APIs failed")


async def main():
    """Run all NewsAPI.ai tests."""
    print("Starting NewsAPI.ai Comprehensive Tests")
    print("="*60)
    
    if not os.getenv("NEWSAPI_AI_KEY"):
        print("NEWSAPI_AI_KEY not found in environment variables")
        print("Make sure to set it in your .env file")
        return
    
    await test_newsapi_ai_full_articles()
    await test_article_content_quality() 
    await test_climate_specific_queries()
    await test_fallback_mechanism()
    
    print("\n" + "="*60)
    print("All tests completed")


if __name__ == "__main__":
    asyncio.run(main())