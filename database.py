import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
SCRAPE_LIMIT = 5

def create_tables():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS scraped_news (
            id SERIAL PRIMARY KEY,
            channel_name TEXT NOT NULL,
            headline TEXT NOT NULL,
            photo_url TEXT,
            post_link TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        print("Tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        cur.close()
        conn.close()

def store_scraped_news(channel_name, headline, photo_url, post_link):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO scraped_news (channel_name, headline, photo_url, post_link) VALUES (%s, %s, %s, %s)",
            (channel_name, headline, photo_url, post_link)
        )
        conn.commit()
    except Exception as e:
        print(f"Error storing scraped news: {e}")
    finally:
        cur.close()
        conn.close()

def get_news_for_channels(channels):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute("""
        SELECT channel_name, headline, photo_url, post_link
        FROM scraped_news
        WHERE channel_name = ANY(%s)
        ORDER BY created_at DESC
        LIMIT 20
        """, (channels,))
        return cur.fetchall()
    except Exception as e:
        print(f"Error getting news for channels: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def get_all_channels():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT channel_name FROM scraped_news")
        return [channel[0] for channel in cur.fetchall()]
    except Exception as e:
        print(f"Error getting all channels: {e}")
        return []
    finally:
        cur.close()
        conn.close()