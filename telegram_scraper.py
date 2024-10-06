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

async def get_or_create_session():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT session_string FROM telethon_session LIMIT 1")
    result = cur.fetchone()
    if result:
        return StringSession(result[0])
    else:
        session = StringSession()
        cur.execute("INSERT INTO telethon_session (session_string) VALUES (%s)", (session.save(),))
        conn.commit()
        return session

async def main():
    session = await get_or_create_session()
    client = TelegramClient(session, API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)
    print("Retrieving session from database...")
    session_string = client.session.save()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE telethon_session SET session_string = %s", (session_string,))
    conn.commit()
    print("Session retrieved.")

    if not session_string:
        print("No session string found in database. Please run local_login.py first.")
        return

    print("Starting Telegram client...")
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    await client.start()
    print("Telegram client started.")

    print("Ensuring database tables are created...")
    create_tables()
    print("Database tables created/verified.")

    print("Scraping and storing news...")
    await scrape_all_channels(client)
    print("News scraping completed.")

    await client.disconnect()
    print("Telegram client disconnected.")

async def scrape_all_channels(client):
    channels = get_channels_from_file()
    for channel in channels:
        await scrape_channel(client, channel)

async def scrape_channel(client, channel_link):
    try:
        channel = await client.get_entity(channel_link)
        messages = await client.get_messages(channel, limit=SCRAPE_LIMIT)
        
        news_items = []
        for message in messages:
            headline = message.text[:170] if message.text else "No text content"
            post_link = f"https://t.me/{channel.username}/{message.id}"
            
            news_items.append({
                'channel': channel.title,
                'headline': headline,
                'link': post_link
            })
        
        store_news_items(news_items)
        print(f"Scraped {len(news_items)} messages from {channel.title}")
    except Exception as e:
        print(f"Error scraping channel {channel_link}: {e}")

def get_channels_from_file():
    with open('channels.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

if __name__ == '__main__':
    client.loop.run_until_complete(main())