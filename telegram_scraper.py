import os
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import CreateChannelRequest, JoinChannelRequest
from telethon.sessions import StringSession
from dotenv import load_dotenv
import asyncio
import psycopg2
from database import store_scraped_news, create_tables, SCRAPE_LIMIT, clear_scraped_news

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
DATABASE_URL = os.getenv('DATABASE_URL')

AGGREGATOR_CHANNEL_NAME = "My News Aggregator"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def read_channels_from_file():
    with open('channels.txt', 'r') as file:
        return [line.strip() for line in file if line.strip()]

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

async def get_or_create_aggregator_channel(client):
    try:
        channel = await client.get_entity(AGGREGATOR_CHANNEL_NAME)
        print(f"Channel {AGGREGATOR_CHANNEL_NAME} found.")
        return channel
    except ValueError:
        print(f"Channel {AGGREGATOR_CHANNEL_NAME} not found. Creating it...")
        channel = await client(CreateChannelRequest(
            title=AGGREGATOR_CHANNEL_NAME,
            about="News aggregator channel"
        ))
        return channel.chats[0]

async def ensure_joined_channels(client, channels):
    for channel_link in channels:
        try:
            await client(JoinChannelRequest(channel_link))
            print(f"Joined channel: {channel_link}")
        except Exception as e:
            print(f"Failed to join channel {channel_link}: {str(e)}")

async def forward_messages_to_aggregator(client, aggregator_channel, channels):
    for channel_link in channels:
        try:
            from_channel = await client.get_entity(channel_link)
            messages = await client.get_messages(from_channel, limit=SCRAPE_LIMIT)
            for message in messages:
                await client.forward_messages(aggregator_channel, messages=message)
            print(f"Forwarded messages from {channel_link} to aggregator")
        except Exception as e:
            print(f"Error forwarding messages from {channel_link}: {str(e)}")

async def scrape_aggregator_channel(client, aggregator_channel):
    clear_scraped_news()  # Clear existing entries before scraping
    messages = await client.get_messages(aggregator_channel, limit=SCRAPE_LIMIT)
    for message in messages:
        image_url = None
        if message.photo:
            image_url = await client.download_media(message.photo, file=bytes)
        text = message.text if message.text else ""
        store_scraped_news(
            channel_name=aggregator_channel.title,
            message_id=message.id,
            date=message.date,
            text=text,
            image_url=image_url
        )
    print(f"Scraped {len(messages)} messages from aggregator channel")

async def main():
    create_tables()
    session = await get_session_from_database()
    client = TelegramClient(session, API_ID, API_HASH)

    await client.start()
    print("Client started successfully")

    channels = read_channels_from_file()
    aggregator_channel = await get_or_create_aggregator_channel(client)
    await ensure_joined_channels(client, channels)
    await forward_messages_to_aggregator(client, aggregator_channel, channels)
    await scrape_aggregator_channel(client, aggregator_channel)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())