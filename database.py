import os
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER REFERENCES users(id),
        channel VARCHAR(255),
        PRIMARY KEY (user_id, channel)
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news_items (
        id SERIAL PRIMARY KEY,
        channel VARCHAR(255),
        headline TEXT,
        link TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(channel, headline)
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS telethon_session (
        id SERIAL PRIMARY KEY,
        session_string TEXT
    )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

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
    cur.execute("INSERT INTO users (telegram_id) VALUES (%s) ON CONFLICT (telegram_id) DO NOTHING", (user_id,))
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
    ON CONFLICT (channel, headline) DO NOTHING
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

async def get_or_create_session(new_session_string=None):
    conn = get_db_connection()
    cur = conn.cursor()
    
    result = None  # Initialize result to None
    
    if new_session_string:
        cur.execute("INSERT INTO telethon_session (id, session_string) VALUES (1, %s) ON CONFLICT (id) DO UPDATE SET session_string = EXCLUDED.session_string", (new_session_string,))
        conn.commit()
    else:
        cur.execute("SELECT session_string FROM telethon_session WHERE id = 1")
        result = cur.fetchone()
        
        if not result:
            cur.execute("INSERT INTO telethon_session (id, session_string) VALUES (1, '')")
            conn.commit()
            result = ('',)
    
    cur.close()
    conn.close()
    
    return result[0] if result else ''