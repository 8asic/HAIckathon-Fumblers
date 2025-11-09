# src/agents/database/news_db.py

import os
import sqlite3
from typing import List, Dict, Any
import hashlib


news_DB = "data/databases/news.db"


def get_connection_to_news_db():
    """Create and connect to the database, creating table if it doesn't exist."""
    os.makedirs(os.path.dirname(news_DB), exist_ok=True)
    
    conn = sqlite3.connect(news_DB)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS data_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            source TEXT,
            date DATE,
            url TEXT,
            body TEXT,
            category TEXT,
            bias TEXT,
            rewritten_article TEXT,
            content_hash TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON data_news(content_hash)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_date ON data_news(date)")
    
    conn.commit()
    conn.close()


def _generate_content_hash(article: Dict[str, Any]) -> str:
    """Generate a hash based on title and body content for deduplication."""
    content = f"{article.get('title', '')}{article.get('body', '')}"
    return hashlib.md5(content.encode()).hexdigest()


def add_news(data: List[Dict[str, Any]]) -> int:
    """
    Add news articles with content-based deduplication.
    
    Returns:
        Number of actually new articles added
    """
    conn = sqlite3.connect(news_DB)
    cur = conn.cursor()
    
    actually_added = 0
    duplicates_found = 0
    
    for article in data:
        content_hash = _generate_content_hash(article)
        
        try:
            cur.execute("SELECT id FROM data_news WHERE content_hash = ?", (content_hash,))
            existing = cur.fetchone()
            
            if existing:
                duplicates_found += 1
                continue
            
            cur.execute("""
                INSERT INTO data_news 
                (title, source, date, url, body, category, bias, rewritten_article, content_hash) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.get('title', ''),
                article.get('source', ''),
                article.get('date', ''),
                article.get('url', ''),
                article.get('body', ''),
                article.get('category', ''),
                None,
                None,
                content_hash
            ))
            actually_added += 1
            
        except sqlite3.Error as e:
            print(f"Error adding article: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"Articles processed: {len(data)}")
    print(f"New articles added: {actually_added}")
    print(f"Duplicates skipped: {duplicates_found}")
    
    return actually_added


def prepare_data_for_llm(limit: int = 5, processed_only: bool = False) -> List[Dict[str, str]]:
    """
    Select articles for LLM processing.
    
    Args:
        limit: Number of articles to return
        processed_only: If True, only return unprocessed articles
    """
    conn = sqlite3.connect(news_DB)
    cur = conn.cursor()
    
    try:
        if processed_only:
            cur.execute("""
                SELECT title, body 
                FROM data_news 
                WHERE bias IS NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        else:
            cur.execute("""
                SELECT title, body 
                FROM data_news 
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cur.fetchall()
        articles = [{"title": row[0], "body": row[1]} for row in rows]
        return articles

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()


def add_bias(llm_data: List[Dict[str, Any]]):
    """Update table with LLM analysis results."""
    try:
        conn = sqlite3.connect(news_DB)
        cur = conn.cursor()
        
        for data in llm_data:
            cur.execute("""
                UPDATE data_news
                SET bias = ?, rewritten_article = ?
                WHERE title = ?
            """, (data["bias"], data["rewritten_article"], data["title"]))

        conn.commit()
        print(f"Updated {len(llm_data)} records with bias analysis")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def clear_old_articles(days_old: int = 1):
    """Clear articles older than specified days."""
    conn = sqlite3.connect(news_DB)
    cur = conn.cursor()
    
    try:
        cur.execute("""
            DELETE FROM data_news 
            WHERE date < date('now', ?)
        """, (f'-{days_old} days',))
        
        deleted_count = cur.rowcount
        conn.commit()
        print(f"Cleared {deleted_count} articles older than {days_old} days")
    except sqlite3.Error as e:
        print(f"Error clearing old articles: {e}")
    finally:
        conn.close()


def clear_processed_articles():
    """Clear already processed articles to make room for new ones."""
    conn = sqlite3.connect(news_DB)
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM data_news WHERE bias IS NOT NULL")
        deleted_count = cur.rowcount
        conn.commit()
        print(f"Cleared {deleted_count} processed articles")
        return deleted_count
    except sqlite3.Error as e:
        print(f"Error clearing processed articles: {e}")
        return 0
    finally:
        conn.close()


def get_article_stats():
    """Get detailed statistics about articles in database."""
    conn = sqlite3.connect(news_DB)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM data_news")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM data_news WHERE bias IS NOT NULL")
        processed = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT content_hash) FROM data_news")
        unique_content = cur.fetchone()[0]
        
        cur.execute("SELECT MIN(date), MAX(date) FROM data_news")
        min_date, max_date = cur.fetchone()
        
        print(f"Database Statistics:")
        print(f"  Total articles: {total}")
        print(f"  Processed articles: {processed}")
        print(f"  Unique content items: {unique_content}")
        print(f"  Date range: {min_date} to {max_date}")
        
        if total > 0:
            duplicate_rate = ((total - unique_content) / total) * 100
            print(f"  Duplicate rate: {duplicate_rate:.1f}%")
        
        return total, processed, unique_content
        
    except sqlite3.Error as e:
        print(f"Error getting stats: {e}")
        return 0, 0, 0
    finally:
        conn.close()