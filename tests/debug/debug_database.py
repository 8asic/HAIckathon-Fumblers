import os
import sys
import sqlite3
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

load_dotenv()

def inspect_database():
    """Inspect what's actually stored in the database."""
    db_path = "data/databases/news.db"
    
    if not os.path.exists(db_path):
        print("Database file does not exist")
        return
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check table structure
    cur.execute("PRAGMA table_info(data_news)")
    columns = cur.fetchall()
    print("Table structure:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check a few records with bias analysis
    print("\nSample records with bias analysis:")
    cur.execute("""
        SELECT title, bias, rewritten_article, length(bias) as bias_len, length(rewritten_article) as rewrite_len
        FROM data_news 
        WHERE bias IS NOT NULL 
        LIMIT 3
    """)
    
    records = cur.fetchall()
    for i, record in enumerate(records):
        title, bias, rewritten, bias_len, rewrite_len = record
        print(f"\nRecord {i+1}:")
        print(f"  Title: {title[:50]}...")
        print(f"  Bias length: {bias_len} chars")
        print(f"  Rewritten length: {rewrite_len} chars")
        print(f"  Bias preview: {str(bias)[:100]}...")
        print(f"  Rewritten preview: {str(rewritten)[:100]}...")
    
    # Check if bias column contains actual JSON or just strings
    print("\nChecking bias column content type:")
    cur.execute("""
        SELECT bias 
        FROM data_news 
        WHERE bias IS NOT NULL 
        LIMIT 1
    """)
    sample_bias = cur.fetchone()
    if sample_bias:
        bias_content = sample_bias[0]
        print(f"First 200 chars of bias content:")
        print(bias_content[:200])
        print(f"Type: {type(bias_content)}")
    
    conn.close()

if __name__ == "__main__":
    inspect_database()