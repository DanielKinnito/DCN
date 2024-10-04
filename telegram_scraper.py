import os
from telethon import TelegramClient, functions
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import CreateChannelRequest
from dotenv import load_dotenv
from database import store_news_items, create_tables
import asyncio

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
SCRAPE_LIMIT = 10  # Adjust this value as needed

client = TelegramClient('user_session', API_ID, API_HASH)

async def get_or_create_news_channel():
    async for dialog in client.iter_dialogs():
        if dialog.is_channel and dialog.entity.title == "My News Aggregator":
            return dialog.entity

    result = await client(CreateChannelRequest(
        title="My News Aggregator",
        about="This channel aggregates news from various sources.",
        megagroup=False
    ))
    return result.chats[0]

async def join_channel(channel_link):
    try:
        await client(functions.channels.JoinChannelRequest(channel=channel_link))
        print(f"Successfully joined channel: {channel_link}")
    except Exception as e:
        print(f"Error joining channel {channel_link}: {e}")

async def scrape_channel(channel_link):
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
        
        news_items = []
        for message in messages.messages:
            headline = message.message[:170] if message.message else "No text content"
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

async def scrape_all_channels():
    channels = get_channels_from_file()
    join_tasks = [join_channel(channel) for channel in channels]
    await asyncio.gather(*join_tasks)
    
    scrape_tasks = [scrape_channel(channel) for channel in channels]
    await asyncio.gather(*scrape_tasks)

def get_channels_from_file():
    with open('channels.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

async def main():
    await client.start(phone=PHONE_NUMBER)
    print("Client Created")
    
    # Ensure database tables are created
    create_tables()
    
    # Scrape and store news
    await scrape_all_channels()
    
    await client.disconnect()

if __name__ == '__main__':
    client.loop.run_until_complete(main())