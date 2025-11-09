import os
from typing import Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()


class NewsClient:
    """Client for fetching news articles from various APIs with quality filtering."""
    
    def __init__(self) -> None:
        self.newsapi_ai_key = os.getenv("NEWSAPI_AI_KEY")
        self.newsapi_key = os.getenv("NEWS_API_KEY")

    async def fetch_articles(self, query: str = "climate change", count: int = 5) -> List[Dict]:
        """Fetch articles from news APIs with fallback mechanisms.
        
        Args:
            query: Search query for articles
            count: Number of articles to fetch
            
        Returns:
            List of article dictionaries with content and metadata
        """
        print(f"Fetching {count} articles for: '{query}'")
        
        articles = await self._fetch_newsapi_ai(query, count)
        if articles:
            articles = self._filter_quality_articles(articles)
            print(f"Using NewsAPI.ai - found {len(articles)} quality articles")
            return articles
            
        articles = await self._fetch_newsapi(query, count)
        if articles:
            articles = self._filter_quality_articles(articles)
            print(f"Using NewsAPI.org - found {len(articles)} articles")
            return articles
            
        print("All news APIs failed, using demo articles")
        return self._get_demo_articles()

    async def _fetch_newsapi_ai(self, query: str, count: int = 5) -> List[Dict]:
        """Fetch articles from NewsAPI.ai with full content."""
        if not self.newsapi_ai_key:
            print("NEWSAPI_AI_KEY not found")
            return []
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "action": "getArticles",
                    "keyword": query,
                    "articlesPage": 1,
                    "articlesCount": count,
                    "articlesSortBy": "rel",
                    "articlesSortByAsc": False,
                    "articlesArticleBodyLen": -1,
                    "resultType": "articles",
                    "dataType": ["news"],
                    "lang": "eng",
                    "ignoreSourceGroups": ["blog", "pressrelease"],
                    "isDuplicateFilter": "skip",
                    "apiKey": self.newsapi_ai_key,
                    "forceMaxDataTimeWindow": 31
                }
                
                print(f"Calling NewsAPI.ai with query: '{query}'")
                response = await client.post(
                    "https://eventregistry.org/api/v1/article/getArticles",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    articles_data = data.get("articles", {}).get("results", [])
                    
                    formatted_articles = []
                    for article in articles_data:
                        body = article.get('body', '')
                        content = body if body else article.get('summary', '')
                        
                        if not content or len(content.strip()) < 100:
                            continue
                            
                        formatted_articles.append({
                            'title': article.get('title', 'No title'),
                            'content': content,
                            'description': article.get('summary', '')[:200] + '...' if article.get('summary') else content[:200] + '...',
                            'url': article.get('url', ''),
                            'source': article.get('source', {}).get('title', 'Unknown'),
                            'full_content': bool(body and len(body) > 100),
                            'api_source': 'newsapi_ai',
                            'publishedAt': article.get('date', ''),
                            'sentiment': article.get('sentiment', 0),
                            'categories': article.get('categories', [])
                        })
                    
                    print(f"Successfully formatted {len(formatted_articles)} articles")
                    return formatted_articles
                else:
                    print(f"NewsAPI.ai API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"NewsAPI.ai error: {e}")
            return []

    async def _fetch_newsapi(self, query: str, count: int = 5) -> List[Dict]:
        """Fetch articles from NewsAPI.org as fallback."""
        if not self.newsapi_key:
            return []
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": query,
                        "apiKey": self.newsapi_key,
                        "pageSize": count,
                        "sortBy": "publishedAt",
                        "language": "en"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles_data = data.get("articles", [])
                    
                    formatted_articles = []
                    for article in articles_data:
                        content = article.get('content', '') or article.get('description', '')
                        formatted_articles.append({
                            'title': article.get('title', ''),
                            'content': content,
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'source': article.get('source', {}).get('name', ''),
                            'full_content': False,
                            'api_source': 'newsapi',
                            'publishedAt': article.get('publishedAt', '')
                        })
                    
                    return formatted_articles
        except Exception as e:
            print(f"NewsAPI.org error: {e}")
        return []

    def _filter_quality_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filter out low-quality articles based on content and metadata."""
        filtered = []
        
        for article in articles:
            title = article.get('title', '').strip()
            content = article.get('content', '').strip()
            
            bad_title_indicators = ['read more', 'click here', '...', '»', 'javascript', 'function()']
            if any(indicator in title.lower() for indicator in bad_title_indicators):
                continue
                
            if len(title) < 10 or title.lower() == 'no title':
                continue
                
            if len(content) < 200:
                continue
                
            if title and not all(ord(c) < 128 for c in title[:50]):
                continue
                
            boilerplate_phrases = ['by clicking submit', 'cookie policy', 'privacy policy', 'terms of service']
            if any(phrase in content.lower() for phrase in boilerplate_phrases):
                continue
                
            filtered.append(article)
        
        print(f"Quality filter: {len(articles)} → {len(filtered)} articles")
        return filtered

    def _get_demo_articles(self) -> List[Dict]:
        """Return demo articles for fallback when APIs are unavailable."""
        print("Using demo articles as fallback")
        return [
            {
                "title": "New Climate Study Shows Alarming Temperature Rise",
                "content": "A comprehensive new study published in Nature Climate Change reveals that global temperatures are rising faster than previously predicted. The research, conducted by an international team of scientists, shows that current climate models may have underestimated the rate of warming in polar regions. This could have significant implications for sea level rise and extreme weather events worldwide. The study calls for urgent action to reduce greenhouse gas emissions.",
                "description": "New research indicates climate change may be accelerating faster than expected, with particular concern about polar regions.",
                "source": "Science Journal",
                "full_content": True,
                "api_source": "demo",
                "publishedAt": "2024-01-15T10:00:00Z",
                "sentiment": -0.3,
                "categories": ["science", "climate"]
            },
            {
                "title": "Renewable Energy Investments Reach Record High",
                "content": "Global investments in renewable energy sources have reached an all-time high, according to a report from the International Energy Agency. Solar and wind power installations are accelerating worldwide, with many countries exceeding their clean energy targets. This surge in green energy investment is driven by falling costs and increased government support. Experts say this trend could help nations meet their climate commitments under the Paris Agreement.",
                "description": "Record investments in solar and wind power are driving the global transition to clean energy.",
                "source": "Energy Times", 
                "full_content": True,
                "api_source": "demo",
                "publishedAt": "2024-01-14T14:30:00Z",
                "sentiment": 0.7,
                "categories": ["energy", "business"]
            }
        ]