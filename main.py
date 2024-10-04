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
    print("Retrieving session from database...")
    session_string = await get_or_create_session()
    print("Session retrieved.")

    print("Starting Telegram bot...")
    bot = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)
    print("Telegram bot started.")

    @bot.on(events.NewMessage(pattern='/start'))
    async def start_command(event):
        await event.reply("Welcome to the Daily Custom News Bot!")

    @bot.on(events.NewMessage(pattern='/news'))
    async def news_command(event):
        channels = get_all_channels()
        news = get_news_for_channels(channels)
        
        if news:
            message = "Here are the latest news:\n\n"
            for channel, headline, link in news:
                message += f"{channel}: {headline}\n{link}\n\n"
        else:
            message = "No news available at the moment."
        
        await event.reply(message)

    print("Bot is running...")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    create_tables()  # Ensure tables are created before running the bot
    asyncio.run(main())