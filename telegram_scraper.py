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

AGGREGATOR_CHANNEL_INVITE = "https://t.me/+jHTdGWaAcok3ODhk"

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

async def get_aggregator_channel(client):
    try:
        channel = await client(JoinChannelRequest(AGGREGATOR_CHANNEL_INVITE))
        print(f"Successfully joined the aggregator channel.")
        return channel.chats[0]
    except Exception as e:
        print(f"Error joining the aggregator channel: {str(e)}")
        return None

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
            try:
                image_url = await client.download_media(message.photo, file=bytes)
            except Exception as e:
                print(f"Error downloading media for message {message.id}: {str(e)}")
        text = message.text if message.text else ""
        try:
            store_scraped_news(
                channel_name=aggregator_channel.title,
                message_id=message.id,
                date=message.date,
                text=text,
                image_url=image_url
            )
        except Exception as e:
            print(f"Error storing message {message.id}: {str(e)}")
            print(f"Message details: channel_name={aggregator_channel.title}, message_id={message.id}, date={message.date}, text={text[:50]}...")
    print(f"Attempted to scrape {len(messages)} messages from aggregator channel")

async def main():
    create_tables()
    session = await get_session_from_database()
    client = TelegramClient(session, API_ID, API_HASH)

    await client.start()
    print("Client started successfully")

    channels = read_channels_from_file()
    aggregator_channel = await get_aggregator_channel(client)
    
    if aggregator_channel:
        await ensure_joined_channels(client, channels)
        await forward_messages_to_aggregator(client, aggregator_channel, channels)
        await scrape_aggregator_channel(client, aggregator_channel)
    else:
        print("Failed to join the aggregator channel. Exiting.")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
