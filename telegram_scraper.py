import os
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import CreateChannelRequest, InviteToChannelRequest
from dotenv import load_dotenv
from database import store_scraped_news, SCRAPE_LIMIT, create_tables
import asyncio
import psycopg2
from telethon.sessions import StringSession

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

async def get_session_from_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT session_string FROM telethon_session LIMIT 1")
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return StringSession(result[0])
    else:
        raise Exception("No session found in the database. Please run local_login.py first.")

async def main():
    create_tables()
    session = await get_session_from_database()
    client = TelegramClient(session, API_ID, API_HASH)

    await client.start()
    print("Client started successfully")

    # Your existing scraping logic here
    # For example:
    # await scrape_channels(client)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())