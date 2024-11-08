import os
import psycopg2
from psycopg2.extras import execute_values
from telethon.sessions import StringSession
import secrets
from telethon import TelegramClient
import base64

DATABASE_URL = os.getenv('DATABASE_URL')
SCRAPE_LIMIT = 100  # Define SCRAPE_LIMIT here

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create a version table if it doesn't exist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    )
    """)
    
    # Check current schema version
    cur.execute("SELECT version FROM schema_version")
    result = cur.fetchone()
    current_version = result[0] if result else 0
    
    if current_version < 1:
        # Perform schema updates
        cur.execute("DROP TABLE IF EXISTS scraped_news")
        cur.execute("""
        CREATE TABLE scraped_news (
            id SERIAL PRIMARY KEY,
            channel_name TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            date TIMESTAMP NOT NULL,
            text TEXT,
            image_url TEXT,
            UNIQUE(channel_name, message_id)
        )
        """)
        
        # Update schema version
        cur.execute("INSERT INTO schema_version (version) VALUES (1) ON CONFLICT (version) DO UPDATE SET version = 1")
    
    conn.commit()
    cur.close()
    conn.close()

def clear_scraped_news():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM scraped_news")
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

def get_or_create_scraper_session():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT session_string FROM telethon_session WHERE id IN (1, 2) ORDER BY id LIMIT 1")
    result = cur.fetchone()
    if result:
        session_string = result[0]
    else:
        session_string = StringSession.generate()
        cur.execute("INSERT INTO telethon_session (id, session_string) VALUES (1, %s) ON CONFLICT (id) DO UPDATE SET session_string = EXCLUDED.session_string", (session_string,))
        conn.commit()
    cur.close()
    conn.close()
    return session_string

def get_or_create_bot_session():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT session_string FROM telethon_session WHERE id = 3")
    result = cur.fetchone()
    if result and result[0]:
        try:
            # Try to decode the stored string
            session_string = base64.b64decode(result[0]).decode('utf-8')
        except UnicodeDecodeError:
            # If decoding fails, generate a new session
            print("Failed to decode existing session. Generating a new one.")
            session_string = StringSession().save()
            # Encode the new session string to base64 for storage
            encoded_session = base64.b64encode(session_string.encode('utf-8')).decode('utf-8')
            cur.execute("UPDATE telethon_session SET session_string = %s WHERE id = 3", (encoded_session,))
            conn.commit()
    else:
        # Generate a new session string
        session_string = StringSession().save()
        # Encode the session string to base64 for storage
        encoded_session = base64.b64encode(session_string.encode('utf-8')).decode('utf-8')
        cur.execute("INSERT INTO telethon_session (id, session_string) VALUES (3, %s) ON CONFLICT (id) DO UPDATE SET session_string = EXCLUDED.session_string", (encoded_session,))
        conn.commit()
    
    cur.close()
    conn.close()
    return session_string

def store_scraped_news(channel_name, message_id, date, text, image_url):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO scraped_news (channel_name, message_id, date, text, image_url)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (channel_name, message_id) DO NOTHING
    """, (channel_name, message_id, date, text, image_url))
    conn.commit()
    cur.close()
    conn.close()

def get_news_for_channels():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT channel_name, text, image_url, date FROM scraped_news ORDER BY date DESC")
    news = cur.fetchall()
    cur.close()
    conn.close()
    return news

def get_all_channels():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT channel_name FROM scraped_news")
    channels = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return channels
