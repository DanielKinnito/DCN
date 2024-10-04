import os
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import CreateChannelRequest, InviteToChannelRequest
from dotenv import load_dotenv
from database import store_scraped_news, SCRAPE_LIMIT, create_tables
import asyncio

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

client = TelegramClient('user_session', API_ID, API_HASH)

async def get_or_create_news_channel():
    # First, try to find an existing channel
    async for dialog in client.iter_dialogs():
        if dialog.is_channel and dialog.entity.title == "My News Aggregator":
            print(f"Existing channel found: https://t.me/{dialog.entity.username}")
            return dialog.entity

    # If no existing channel is found, create a new one
    result = await client(CreateChannelRequest(
        title="My News Aggregator",
        about="This channel aggregates news from various sources.",
        megagroup=False  # Set to True if you want a supergroup instead of a channel
    ))
    channel = result.chats[0]
    print(f"Created new channel: https://t.me/{channel.username}")
    return channel

async def forward_message_to_channel(message, source_channel, target_channel):
    await client.forward_messages(target_channel, message, source_channel)

async def join_channel(channel_link):
    try:
        await client(functions.channels.JoinChannelRequest(channel=channel_link))
        print(f"Successfully joined channel: {channel_link}")
    except Exception as e:
        print(f"Error joining channel {channel_link}: {e}")

async def scrape_channel(channel_link, news_channel):
    try:
        channel = await client.get_entity(channel_link)
        
        messages = await client(GetHistoryRequest(
            peer=channel,
            limit=SCRAPE_LIMIT,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        
        for message in messages.messages:
            headline = message.message[:170] if message.message else "No text content"
            photo_url = message.media.photo.id if message.media and hasattr(message.media, 'photo') else None
            post_link = f"{channel_link}/{message.id}"
            
            # Forward the message to our news channel
            await forward_message_to_channel(message, channel, news_channel)
            
            # Store in database
            store_scraped_news(channel.title, headline, photo_url, post_link)
        
        print(f"Scraped and forwarded {len(messages.messages)} messages from {channel.title}")
    except Exception as e:
        print(f"Error scraping channel {channel_link}: {e}")

async def scrape_all_channels(news_channel):
    channels = get_channels_from_file()
    join_tasks = [join_channel(channel) for channel in channels]
    await asyncio.gather(*join_tasks)
    
    scrape_tasks = [scrape_channel(channel, news_channel) for channel in channels]
    await asyncio.gather(*scrape_tasks)

def get_channels_from_file():
    with open('channels.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

async def main():
    await client.start(phone=PHONE_NUMBER)
    print("Client Created")
    
    # Get or create the news channel
    news_channel = await get_or_create_news_channel()
    
    # Create database tables
    create_tables()
    
    # Scrape and forward messages
    await scrape_all_channels(news_channel)
    
    await client.disconnect()

if __name__ == '__main__':
    client.loop.run_until_complete(main())