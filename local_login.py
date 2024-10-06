import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import asyncio
import psycopg2
from database import create_tables

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

async def get_or_create_session(session_string=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if session_string:
        cur.execute("INSERT INTO telethon_session (session_string) VALUES (%s) ON CONFLICT (id) DO UPDATE SET session_string = EXCLUDED.session_string", (session_string,))
        conn.commit()
    else:
        cur.execute("SELECT session_string FROM telethon_session LIMIT 1")
        result = cur.fetchone()
        if result:
            session_string = result[0]
    cur.close()
    conn.close()
    return StringSession(session_string) if session_string else StringSession()

async def main():
    print("Creating tables...")
    create_tables()
    print("Tables created successfully.")

    print("Starting Telegram client...")
    session = await get_or_create_session()
    client = TelegramClient(session, API_ID, API_HASH)
    
    await client.start(phone=PHONE_NUMBER)
    print("Signed in successfully as", await client.get_me())

    print("Generating session string...")
    session_string = client.session.save()
    print("Session string generated.")

    print("Saving session string to database...")
    await get_or_create_session(session_string)
    print("Session string saved to database.")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())