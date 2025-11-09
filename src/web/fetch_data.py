from dotenv import load_dotenv
import os
from eventregistry import *
import requests
import json 


load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def categorize_article_domain(text):
    if not text or len(text.strip()) < 50:
        return "Uncategorized"

    url = "https://analytics.eventregistry.org/api/v1/categorize"
    payload = {
        "text": text[:5000],
        "taxonomy": "news",
        "apiKey": NEWS_API_KEY
    }
    headers = {"Content-Type": "application/json"}

    try:
        res = requests.post(url, json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()

        if "categories" in data and data["categories"]:
            # pick top scoring category (highest confidence)
            top = sorted(data["categories"], key=lambda x: x["score"], reverse=True)[0]
            # strip prefix: "news/Business" -> "Business"
            label = top["label"].split("/")[-1]
            return label
    except Exception as e:
        print("Categorization error:", e)
    return "Uncategorized"

def fetch_news():
    er = EventRegistry(apiKey=NEWS_API_KEY)
    q = QueryArticlesIter(lang="eng", dataType=["news"])
    articles = []

    for art in q.execQuery(er, sortBy="date", maxItems=1):
        articles.append({
            "title": art["title"],
            "source":art["source"],
            "date":art["date"],
            "url": art["url"],
            "body": art["body"] ,
            "category":categorize_article_domain(art["body"])
        })

    return (articles)

a =fetch_news()

print(type(json.dumps(a)))

