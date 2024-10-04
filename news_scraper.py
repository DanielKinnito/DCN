from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

client = TelegramClient('news_scraper_session', API_ID, API_HASH)

async def get_latest_news(channel_name):
    async with client:
        entity = await client.get_entity(channel_name)
        messages = await client.get_messages(entity, limit=5)
        
        news_items = []
        for message in messages:
            if message.text:
                headline = message.text.split('\n')[0]
                news_items.append({
                    'headline': headline,
                    'link': f'https://t.me/{channel_name}/{message.id}'
                })
        
        return news_items
