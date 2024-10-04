import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from database import create_tables, get_news_for_channels, get_all_channels

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Initialize the Telegram client
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

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

if __name__ == "__main__":
    create_tables()  # Ensure tables are created before running the bot
    print("Bot is running...")
    bot.run_until_disconnected()