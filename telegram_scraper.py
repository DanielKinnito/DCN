import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
from database import store_news_items, create_tables, get_or_create_session
import asyncio

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SCRAPE_LIMIT = 10

async def main():
    print("Retrieving session from database...")
    session_string = await get_or_create_session()
    print("Session retrieved.")

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
    asyncio.run(main())