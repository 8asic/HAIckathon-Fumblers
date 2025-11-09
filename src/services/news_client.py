# src/services/news_client.py

import os
import requests
from typing import Dict, List, Optional
import httpx
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()


class NewsClient:
    def __init__(self) -> None:
        self.newsapi_ai_key = os.getenv("NEWSAPI_AI_KEY")
        self.newsapi_key = os.getenv("NEWS_API_KEY")

    async def fetch_articles(self, query: Optional[str] = None, count: int = 5) -> List[Dict]:
        """
        Fetch articles with optional query parameter.
        
        Args:
            query: Optional search query. If None, fetches general news
            count: Number of articles to fetch
            
        Returns:
            List of article dictionaries
        """
        if query:
            print(f"Fetching {count} articles for query: '{query}'")
            articles = await self._fetch_fresh_newsapi_ai(query, count)
        else:
            print(f"Fetching {count} recent articles without specific query")
            articles = await self._fetch_recent_newsapi_ai(count)
        
        if articles:
            print(f"NewsAPI.ai returned {len(articles)} articles")
            return articles
        
        articles = await self._fetch_newsapi(query or "news", count)
        if articles:
            print(f"NewsAPI returned {len(articles)} articles")
            return articles
        
        print("No articles found from APIs, using demo data")
        return self._get_demo_articles()

    async def _fetch_recent_newsapi_ai(self, count: int = 5) -> List[Dict]:
        """Fetch recent articles without specific query."""
        if not self.newsapi_ai_key:
            return []
            
        try:
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "action": "getArticles",
                    "articlesPage": 1,
                    "articlesCount": count,
                    "articlesSortBy": "date",
                    "articlesSortByAsc": False,
                    "articlesArticleBodyLen": -1,
                    "resultType": "articles",
                    "dataType": ["news"],
                    "lang": "eng",
                    "ignoreSourceGroups": ["blog", "pressrelease"],
                    "isDuplicateFilter": "skip",
                    "apiKey": self.newsapi_ai_key,
                    "dateStart": yesterday.strftime("%Y-%m-%d"),
                    "dateEnd": today.strftime("%Y-%m-%d"),
                    "forceMaxDataTimeWindow": 1
                }
                
                response = await client.post(
                    "https://eventregistry.org/api/v1/article/getArticles",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles_data = data.get("articles", {}).get("results", [])
                    
                    articles = []
                    for article in articles_data:
                        body = article.get('body', '')
                        if not body or len(body.strip()) < 100:
                            continue
                            
                        category = self._categorize_article(body)
                            
                        articles.append({
                            'title': article.get('title', 'No title'),
                            'source': article.get('source', {}).get('title', 'Unknown'),
                            'date': article.get('date', '').split('T')[0],
                            'url': article.get('url', ''),
                            'body': body,
                            'category': category
                        })
                    
                    return articles
                else:
                    print(f"NewsAPI.ai error: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"NewsAPI.ai recent fetch failed: {e}")
            return []

    async def _fetch_fresh_newsapi_ai(self, query: str, count: int = 5) -> List[Dict]:
        """Fetch recent articles with specific query."""
        if not self.newsapi_ai_key:
            return []
            
        try:
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "action": "getArticles",
                    "keyword": query,
                    "articlesPage": 1,
                    "articlesCount": count,
                    "articlesSortBy": "date",
                    "articlesSortByAsc": False,
                    "articlesArticleBodyLen": -1,
                    "resultType": "articles",
                    "dataType": ["news"],
                    "lang": "eng",
                    "ignoreSourceGroups": ["blog", "pressrelease"],
                    "isDuplicateFilter": "skip",
                    "apiKey": self.newsapi_ai_key,
                    "dateStart": yesterday.strftime("%Y-%m-%d"),
                    "dateEnd": today.strftime("%Y-%m-%d"),
                    "forceMaxDataTimeWindow": 1
                }
                
                response = await client.post(
                    "https://eventregistry.org/api/v1/article/getArticles",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles_data = data.get("articles", {}).get("results", [])
                    
                    articles = []
                    for article in articles_data:
                        body = article.get('body', '')
                        if not body or len(body.strip()) < 100:
                            continue
                            
                        category = self._categorize_article(body)
                            
                        articles.append({
                            'title': article.get('title', 'No title'),
                            'source': article.get('source', {}).get('title', 'Unknown'),
                            'date': article.get('date', '').split('T')[0],
                            'url': article.get('url', ''),
                            'body': body,
                            'category': category
                        })
                    
                    return articles
                else:
                    print(f"NewsAPI.ai error: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"NewsAPI.ai fetch failed: {e}")
            return []

    async def _fetch_newsapi(self, query: str, count: int = 5) -> List[Dict]:
        """Fetch from regular NewsAPI with recent articles."""
        if not self.newsapi_key:
            return []
            
        try:
            yesterday = datetime.now() - timedelta(days=1)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": query,
                        "apiKey": self.newsapi_key,
                        "pageSize": count,
                        "sortBy": "publishedAt",
                        "language": "en",
                        "from": yesterday.strftime("%Y-%m-%d"),
                        "to": datetime.now().strftime("%Y-%m-%d")
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles_data = data.get("articles", [])
                    
                    articles = []
                    for article in articles_data:
                        content = article.get('content', '') or article.get('description', '')
                        if len(content) < 100:
                            continue
                        
                        category = self._categorize_article(content)
                            
                        articles.append({
                            'title': article.get('title', ''),
                            'source': article.get('source', {}).get('name', ''),
                            'date': article.get('publishedAt', '').split('T')[0],
                            'url': article.get('url', ''),
                            'body': content,
                            'category': category
                        })
                    
                    return articles
        except Exception as e:
            print(f"NewsAPI fetch failed: {e}")
        return []

    def _categorize_article(self, text: str) -> str:
        """Categorize article content using EventRegistry analytics."""
        if not text or len(text.strip()) < 50:
            return "Uncategorized"

        url = "https://analytics.eventregistry.org/api/v1/categorize"
        payload = {
            "text": text[:5000],
            "taxonomy": "news",
            "apiKey": self.newsapi_ai_key or self.newsapi_key
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            if "categories" in data and data["categories"]:
                top = sorted(data["categories"], key=lambda x: x["score"], reverse=True)[0]
                label = top["label"].split("/")[-1]
                return label
        except Exception:
            pass
        return "Uncategorized"

    def _get_demo_articles(self) -> List[Dict]:
        """Fallback demo articles if no API results."""
        return [
            {
                "title": "Climate Change Study Shows Temperature Trends",
                "source": "Science Journal", 
                "date": datetime.now().strftime("%Y-%m-%d"),
                "url": "https://example.com/climate-study",
                "body": "A comprehensive new study published in Nature Climate Change reveals climate patterns and temperature trends across different regions.",
                "category": "Science"
            },
            {
                "title": "Renewable Energy Investments Reach New High", 
                "source": "Energy Times",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "url": "https://example.com/renewable-energy", 
                "body": "Global investments in renewable energy sources have reached record levels according to recent market analysis.",
                "category": "Energy"
            }
        ]