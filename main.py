import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from database import create_tables, get_news_for_channels, get_all_channels, get_or_create_session
import asyncio

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

async def main():
    create_tables()
    print("Retrieving session from database...")
    session_string = get_or_create_session()  # This is no longer an async call
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)

    await client.start(bot_token=BOT_TOKEN)
    print("Bot started successfully")

    # Your main bot logic here
    # For example:
    # await handle_commands(client)

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())