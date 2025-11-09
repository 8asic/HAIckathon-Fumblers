# src/services/news_client.py

import os
import requests
from typing import Dict, List
import httpx
from dotenv import load_dotenv

load_dotenv()


class NewsClient:
    def __init__(self) -> None:
        self.newsapi_ai_key = os.getenv("NEWSAPI_AI_KEY")
        self.newsapi_key = os.getenv("NEWS_API_KEY")

    async def fetch_articles(self, query: str = "climate change", count: int = 5) -> List[Dict]:
        """Fetch articles - returns only: title, source, date, url, body, category"""
        articles = await self._fetch_newsapi_ai(query, count)
        if articles:
            return articles
            
        articles = await self._fetch_newsapi(query, count)
        if articles:
            return articles
            
        return self._get_demo_articles()

    async def _fetch_newsapi_ai(self, query: str, count: int = 5) -> List[Dict]:
        if not self.newsapi_ai_key:
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
                return []
                    
        except Exception:
            return []

    async def _fetch_newsapi(self, query: str, count: int = 5) -> List[Dict]:
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
        except Exception:
            pass
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
                # Pick top scoring category (highest confidence)
                top = sorted(data["categories"], key=lambda x: x["score"], reverse=True)[0]
                # Strip prefix: "news/Business" -> "Business"
                label = top["label"].split("/")[-1]
                return label
        except Exception as e:
            print(f"Categorization error: {e}")
        return "Uncategorized"

    def _get_demo_articles(self) -> List[Dict]:
        return [
            {
                "title": "New Climate Study Shows Temperature Trends",
                "source": "Science Journal", 
                "date": "2024-01-15",
                "url": "https://example.com/climate-study",
                "body": "A comprehensive new study published in Nature Climate Change reveals climate patterns.",
                "category": "Science"
            },
            {
                "title": "Renewable Energy Investments Increase", 
                "source": "Energy Times",
                "date": "2024-01-14",
                "url": "https://example.com/renewable-energy", 
                "body": "Global investments in renewable energy sources have reached significant levels.",
                "category": "Energy"
            }
        ]