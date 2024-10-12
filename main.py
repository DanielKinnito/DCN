import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from database import create_tables, get_news_for_channels, get_all_channels, get_or_create_bot_session

# Get credentials from environment variables
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

async def main():
    create_tables()
    print("Retrieving bot session from database...")
    session_string = get_or_create_bot_session()
    
    try:
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        print("Starting bot...")
        await client.start(bot_token=BOT_TOKEN)
        print("Bot started successfully")
    except Exception as e:
        print(f"Error starting the bot: {str(e)}")
        print("Attempting to create a new session...")
        new_session = StringSession.generate()
        client = TelegramClient(new_session, API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)
        print("Bot started with a new session")

    @client.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        await event.reply('Welcome to the News Aggregator Bot! Use /news to get the latest updates.')

    @client.on(events.NewMessage(pattern='/news'))
    async def news_handler(event):
        news = get_news_for_channels()
        if news:
            for item in news[:5]:  # Send the 5 most recent news items
                channel_name, text, image_url, date = item
                message = f"From {channel_name} on {date}:\n\n{text}"
                if image_url:
                    await client.send_file(event.chat_id, image_url, caption=message)
                else:
                    await client.send_message(event.chat_id, message)
        else:
            await event.reply("No news available at the moment. Please check back later.")

    # Run the bot for a fixed duration (e.g., 55 minutes)
    # This ensures the script ends before the next scraper run
    try:
        print("Bot is running. Press Ctrl+C to stop.")
        await asyncio.sleep(3300)  # Run for 55 minutes
    finally:
        print("Stopping bot...")
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
