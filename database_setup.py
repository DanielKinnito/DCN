import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')

def setup_database():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Create tables
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

if __name__ == "__main__":
    setup_database()