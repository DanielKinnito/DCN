import os
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import CreateChannelRequest, InviteToChannelRequest
from dotenv import load_dotenv
from database import store_scraped_news, create_tables, SCRAPE_LIMIT
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

async def scrape_channels(client):
    # Add your channel usernames or IDs here
    channels = ['@channel1', '@channel2', '@channel3']

    for channel in channels:
        print(f"Scraping channel: {channel}")
        try:
            entity = await client.get_entity(channel)
            messages = await client.get_messages(entity, limit=SCRAPE_LIMIT)
            
            for message in messages:
                store_scraped_news(
                    channel_id=str(entity.id),
                    message_id=message.id,
                    date=message.date,
                    text=message.text
                )
            print(f"Scraped {len(messages)} messages from {channel}")
        except Exception as e:
            print(f"Error scraping {channel}: {str(e)}")

async def main():
    create_tables()
    session = await get_session_from_database()
    client = TelegramClient(session, API_ID, API_HASH)

    await client.start()
    print("Client started successfully")

    await scrape_channels(client)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())