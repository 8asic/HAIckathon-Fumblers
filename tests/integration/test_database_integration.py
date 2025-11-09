# tests/integration/test_database_integration.py

import os
import sys
import asyncio
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

load_dotenv()

from src.database.news_db import (
    get_connection_to_news_db, 
    add_news, 
    prepare_data_for_llm,
    add_bias,
    clear_old_articles,
    get_article_stats
)
from src.services.news_client import NewsClient


async def test_news_client_with_optional_query():
    """Test NewsClient with optional query parameter."""
    print("Testing NewsClient with optional query...")
    
    client = NewsClient()
    
    print("Test 1: Fetch with specific query...")
    articles1 = await client.fetch_articles("renewable energy", 2)
    print(f"Fetched {len(articles1)} articles for 'renewable energy'")
    
    print("Test 2: Fetch with default query...")
    articles2 = await client.fetch_articles(None, 2)
    print(f"Fetched {len(articles2)} articles with default query")
    
    print("Test 3: Fetch with different query...")
    articles3 = await client.fetch_articles("climate policy", 2)
    print(f"Fetched {len(articles3)} articles for 'climate policy'")
    
    return articles1 + articles2 + articles3


async def test_database_operations():
    """Test database operations with fresh articles."""
    print("Testing Database Operations...")
    
    get_connection_to_news_db()
    print("Database created")
    
    clear_old_articles(days_old=0)
    
    articles = await test_news_client_with_optional_query()
    add_news(data=articles)
    print("Articles added to database")
    
    llm_articles = prepare_data_for_llm(limit=10, processed_only=True)
    
    if not llm_articles:
        print("No articles prepared for LLM")
        return False
    
    print(f"Prepared {len(llm_articles)} articles for LLM")
    
    if llm_articles:
        mock_bias_data = [
            {
                "title": llm_articles[0]["title"],
                "bias": "Low emotional bias detected",
                "rewritten_article": "This is a neutral version of the article."
            }
        ]
        add_bias(mock_bias_data)
        print("Added mock bias analysis to database")
    
    return True


def check_database_file():
    """Check database file location and structure."""
    print("Checking Database File Location...")
    
    db_path = "data/databases/news.db"
    if os.path.exists(db_path):
        print(f"Database file created at: {os.path.abspath(db_path)}")
        size = os.path.getsize(db_path)
        print(f"File size: {size} bytes")
    else:
        print(f"Database file not found at: {os.path.abspath(db_path)}")
    
    print("Directory Structure:")
    print(f"  data/ exists: {os.path.exists('data')}")
    print(f"  data/databases/ exists: {os.path.exists('data/databases')}")


async def main():
    """Run all integration tests."""
    print("Testing NewsClient + Database Integration")
    print("=" * 50)
    
    required_vars = ['NEWSAPI_AI_KEY', 'NEWS_API_KEY']
    print("Environment Check:")
    for var in required_vars:
        if os.getenv(var):
            print(f"  SET: {var}")
        else:
            print(f"  MISSING: {var}")
    
    try:
        db_success = await test_database_operations()
        
        check_database_file()
        
        get_article_stats()
        
        print("=" * 50)
        if db_success:
            print("ALL TESTS PASSED: Integration working correctly")
        else:
            print("SOME TESTS FAILED: Review errors above")
            
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())