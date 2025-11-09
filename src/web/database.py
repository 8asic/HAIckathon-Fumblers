import os 
import sqlite3
from eventregistry import *
#from fetch import fetch_news


news_DB="News.db"

#fetch_news() will be imported from another python file
data = fetch_news()


#create, get connection to the database and executing sql statements such creating columns to the table data_news
def get_connection_to_news_db():
    try:
        #get connection
        conn = sqlite3.connect(news_DB)
        #to execute SQL statements
        cur = conn.cursor()
        #create columns
        cur.execute("""
    CREATE TABLE IF NOT EXISTS data_news (
        title TEXT,
        source TEXT,
        date date,
        url TEXT,
        body TEXT,
        category TEXT,
        bias TEXT,
        rewritten_article TEXT  
    )
    """)
        conn.commit()
        print("connected to DB succesfully")
    finally:
        conn.close()
        
        

#filling values in the table data_news
def add_news(db=news_DB,data=data):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    try:
        #retriving data from newsapi and inserting to columns
        cur.executemany(    
            "INSERT INTO data_news (title, source, date, url, body, category, bias, rewritten_article) VALUES (?, ?, ?, ?, ?, ?,?, ?)",
            [(d['title'], d['source'], d['date'], d['url'], d['body'], d['category'], None, None) for d in data]
        )
    except sqlite3.Error as er:
        print({f"Error":{er}})
    finally:
        #save changes and close
        conn.commit()
        conn.close() 

#we select title and text from specified columns(title, body) and order by date(take the freshest news) to feed to llm
def prepare_data_for_llm():
    conn = sqlite3.connect(news_DB)
    cur = conn.cursor()
    try:
        #select title,body from data_news table and order descendently(freshest news), limit sets that only 2 articles are taken
        #find the 2 newest rows (by date) and return their title and body columns
        #results are not yet in python memory, because they are still inside SQLite's internal cursor buffer
        columns = cur.execute("SELECT title,body FROM data_news ORDER BY date DESC limit 2 ")
        #gives the selected rows into the list of tuples from database cursor
        rows = columns.fetchall()
        #from list of tuples to list of dicts
        articles = [{"title":r[0], 'body':r[1]} for r in rows]
        return articles 

    except sqlite3.Error as er:
        print({f'Error':{er}})
    finally:
        conn.close()    

#after llm made an analysis we store them in the table to corresponding columns(bias, rewritten_article)
def add_bias(llm_data, db=news_DB):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        for d in llm_data:
            #update the table by inserting values to bias and rewritten_artircle columns, to coressponding row by specifying title
            cur.execute("""
                UPDATE data_news
                SET bias = ?, rewritten_article = ?
                WHERE title = ?
            """, (d["bias"], d["rewritten_article"], d["title"]))

        conn.commit()
        print(f"Updated {len(llm_data)} records with LLM bias & rewritten text.")

    except sqlite3.Error as er:
        print(f"Database error: {er}")
    finally:
        conn.close()

