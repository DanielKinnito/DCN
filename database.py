import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
from psycopg2.extras import execute_values

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

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def get_all_news_channels():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT channel FROM user_preferences")
    channels = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return channels

def add_user_preference(user_id, channels):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (telegram_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
    cur.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
    db_user_id = cur.fetchone()[0]
    
    cur.execute("DELETE FROM user_preferences WHERE user_id = %s", (db_user_id,))
    execute_values(cur, "INSERT INTO user_preferences (user_id, channel) VALUES %s",
                   [(db_user_id, channel) for channel in channels])
    conn.commit()
    cur.close()
    conn.close()

def get_user_preferences(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT channel FROM user_preferences
    JOIN users ON user_preferences.user_id = users.id
    WHERE users.telegram_id = %s
    """, (user_id,))
    preferences = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return preferences

def store_news_items(news_items):
    conn = get_db_connection()
    cur = conn.cursor()
    execute_values(cur, """
    INSERT INTO news_items (channel, headline, link)
    VALUES %s
    ON CONFLICT DO NOTHING
    """, [(item['channel'], item['headline'], item['link']) for item in news_items])
    conn.commit()
    cur.close()
    conn.close()

def get_news_for_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT news_items.channel, news_items.headline, news_items.link
    FROM news_items
    JOIN user_preferences ON news_items.channel = user_preferences.channel
    JOIN users ON user_preferences.user_id = users.id
    WHERE users.telegram_id = %s
    ORDER BY news_items.created_at DESC
    LIMIT 20
    """, (user_id,))
    news = cur.fetchall()
    cur.close()
    conn.close()
    return news