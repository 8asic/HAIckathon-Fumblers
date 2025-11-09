import os
import sqlite3
from src.services.news_client import NewsClient
import asyncio

news_DB = "data/databases/news.db"

# Create NewsClient instance and fetch data
news_client = NewsClient()

# Use asyncio to run the async function
data = asyncio.run(news_client.fetch_articles())


def get_connection_to_news_db():
    """Create and connect to the database, creating table if it doesn't exist."""
    try:
        # Get connection
        conn = sqlite3.connect(news_DB)
        cur = conn.cursor()
        
        # Create table with columns
        cur.execute("""
            CREATE TABLE IF NOT EXISTS data_news (
                title TEXT,
                source TEXT,
                date DATE,
                url TEXT,
                body TEXT,
                category TEXT,
                bias TEXT,
                rewritten_article TEXT
            )
        """)
        conn.commit()
        print("Connected to DB successfully")
    finally:
        conn.close()


def add_news(db=news_DB, data=data):
    """Fill values in the data_news table."""
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    
    try:
        # Insert data into columns
        cur.executemany(
            """
            INSERT INTO data_news 
            (title, source, date, url, body, category, bias, rewritten_article) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    d['title'], d['source'], d['date'], d['url'], 
                    d['body'], d['category'], None, None
                ) for d in data
            ]
        )
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        # Save changes and close
        conn.commit()
        conn.close()


def prepare_data_for_llm():
    """
    Select title and body from data_news table, ordered by date (freshest news).
    Returns the 2 newest articles for LLM processing.
    """
    conn = sqlite3.connect(news_DB)
    cur = conn.cursor()
    
    try:
        # Select 2 newest articles by date
        cur.execute("""
            SELECT title, body 
            FROM data_news 
            ORDER BY date DESC 
            LIMIT 2
        """)
        
        # Fetch results from cursor buffer
        rows = cur.fetchall()
        
        # Convert list of tuples to list of dictionaries
        articles = [{"title": row[0], "body": row[1]} for row in rows]
        return articles

    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()


def add_bias(llm_data, db=news_DB):
    """Update table with LLM analysis results in bias and rewritten_article columns."""
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        
        for data in llm_data:
            # Update corresponding row by title
            cur.execute("""
                UPDATE data_news
                SET bias = ?, rewritten_article = ?
                WHERE title = ?
            """, (data["bias"], data["rewritten_article"], data["title"]))

        conn.commit()
        print(f"Updated {len(llm_data)} records with LLM bias & rewritten text.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()