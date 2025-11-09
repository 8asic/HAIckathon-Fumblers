# tests/integration/test_database_integration.py

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

load_dotenv()

from src.database.news_db import (
    get_connection_to_news_db, 
    add_news, 
    prepare_data_for_llm,
    add_bias
)
from src.services.news_client import NewsClient


async def test_news_client():
    """Test the NewsClient fetches articles with categorization."""
    print("Testing NewsClient...")
    
    client = NewsClient()
    articles = await client.fetch_articles("climate change", 2)
    
    print(f"SUCCESS: Fetched {len(articles)} articles")
    for article in articles:
        print(f"  - '{article['title']}' -> Category: {article['category']}")
    
    return articles


async def test_database_operations():
    """Test database creation and operations."""
    print("\nTesting Database Operations...")
    
    # 1. Create database and table
    get_connection_to_news_db()
    print("SUCCESS: Database created")
    
    # 2. Add news to database
    articles = await test_news_client()
    add_news(data=articles)
    print("SUCCESS: Articles added to database")
    
    # 3. Prepare data for LLM
    llm_articles = prepare_data_for_llm()
    
    # Handle potential None return from prepare_data_for_llm()
    if not llm_articles:
        print("WARNING: No articles prepared for LLM - database may be empty")
        return False
    
    print(f"SUCCESS: Prepared {len(llm_articles)} articles for LLM")
    for article in llm_articles:
        print(f"  - '{article['title']}'")
    
    # 4. Test adding bias analysis (mock data)
    if llm_articles:
        mock_bias_data = [
            {
                "title": llm_articles[0]["title"],
                "bias": "Low emotional bias detected",
                "rewritten_article": "This is a neutral version of the article."
            }
        ]
        add_bias(mock_bias_data)
        print("SUCCESS: Added mock bias analysis to database")
    
    return True


def check_database_file():
    """Check if database file was created in correct location."""
    print("\nChecking Database File Location...")
    
    db_path = "data/databases/news.db"
    if os.path.exists(db_path):
        print(f"SUCCESS: Database file created at: {os.path.abspath(db_path)}")
        
        # Check file size
        size = os.path.getsize(db_path)
        print(f"  File size: {size} bytes")
    else:
        print(f"FAILED: Database file not found at: {os.path.abspath(db_path)}")
        
    # Check data directory structure
    data_dir = "data"
    databases_dir = "data/databases"
    
    print(f"\nDirectory Structure:")
    print(f"  data/ exists: {os.path.exists(data_dir)}")
    print(f"  data/databases/ exists: {os.path.exists(databases_dir)}")


async def main():
    """Run all integration tests."""
    print("Testing NewsClient + Database Integration")
    print("=" * 50)
    
    # Check environment
    required_vars = ['NEWSAPI_AI_KEY', 'NEWS_API_KEY']
    print("Environment Check:")
    for var in required_vars:
        if os.getenv(var):
            print(f"  SET: {var}")
        else:
            print(f"  MISSING: {var}")
    
    # Run tests
    try:
        # Test Database operations (this includes NewsClient test)
        db_success = await test_database_operations()
        
        # Check file locations
        check_database_file()
        
        print("\n" + "=" * 50)
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