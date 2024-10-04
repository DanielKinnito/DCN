import os
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from telethon.tl.types import InputPeerUser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import create_tables, get_news_for_channels, get_all_channels
from telegram_scraper import scrape_all_channels
from telegraph import Telegraph
import re

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
telegraph = Telegraph()
telegraph.create_account(short_name='news_bot')

# Store user preferences in memory (you might want to use a more persistent storage in production)
user_preferences = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()
    await show_main_menu(sender)

async def show_main_menu(user):
    buttons = [
        [Button.inline("📰 View News", b"view_news")],
        [Button.inline("🔧 Preferences", b"preferences")],
        [Button.inline("ℹ️ About", b"about")]
    ]
    await bot.send_message(user, "Welcome to the News Bot! Please choose an option:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"view_news"))
async def view_news(event):
    user_id = event.sender_id
    if user_id not in user_preferences or not user_preferences[user_id]:
        await event.answer("You haven't selected any channels. Please update your preferences.")
        return

    news = get_news_for_channels(user_preferences[user_id])
    if not news:
        await event.answer("There's no news available for your selected channels.")
        return

    content = ""
    for channel_name, headline, photo_url, post_link in news:
        content += f'<h3>{channel_name}</h3>'
        
        if photo_url:
            content += f'<img src="{photo_url}">'
        
        if headline:
            cleaned_headline = clean_text(headline)
            content += f'<p>{cleaned_headline}</p>'
        
        content += f'<a href="{post_link}">View original post</a><br><br>'

    if not content:
        await event.answer("No valid news content available.")
        return

    response = telegraph.create_page(
        title="Your Personalized News Feed",
        html_content=content,
        author_name="News Bot"
    )

    selected_channels = ", ".join(user_preferences[user_id])
    message = f"Selected channels: {selected_channels}\n\nClick the button below to view your personalized news feed:"
    buttons = [[Button.url("📰 View News Feed", response['url'])]]
    await event.edit(message, buttons=buttons)

def clean_text(text):
    # Remove hashtags, mentions, and URLs
    text = re.sub(r'#\w+|@\w+|http\S+', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

@bot.on(events.CallbackQuery(pattern=b"preferences"))
async def preferences(event):
    user_id = event.sender_id
    all_channels = get_all_channels()

    if user_id not in user_preferences:
        user_preferences[user_id] = []

    buttons = []
    for channel in all_channels:
        status = "✅" if channel in user_preferences[user_id] else "❌"
        buttons.append([Button.inline(f"{status} {channel}", f"toggle:{channel}")])

    buttons.append([Button.inline("🔙 Back to Main Menu", b"main_menu")])
    await event.edit("Select channels to follow:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"toggle:"))
async def toggle_channel(event):
    user_id = event.sender_id
    channel = event.data.decode().split(':')[1]

    if user_id not in user_preferences:
        user_preferences[user_id] = []

    if channel in user_preferences[user_id]:
        user_preferences[user_id].remove(channel)
        await event.answer(f"Channel '{channel}' has been unselected.")
    else:
        user_preferences[user_id].append(channel)
        await event.answer(f"Channel '{channel}' has been selected.")

    # Update the message with new button states
    all_channels = get_all_channels()
    buttons = []
    for ch in all_channels:
        status = "✅" if ch in user_preferences[user_id] else "❌"
        buttons.append([Button.inline(f"{status} {ch}", f"toggle:{ch}")])

    buttons.append([Button.inline("🔙 Back to Main Menu", b"main_menu")])
    await event.edit("Select channels to follow:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"about"))
async def about(event):
    about_text = "This bot provides personalized news updates from various Telegram channels. Use the preferences menu to customize your feed."
    buttons = [[Button.inline("🔙 Back to Main Menu", b"main_menu")]]
    await event.edit(about_text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"main_menu"))
async def main_menu(event):
    await event.edit("Welcome to the News Bot! Please choose an option:", buttons=[
        [Button.inline("📰 View News", b"view_news")],
        [Button.inline("🔧 Preferences", b"preferences")],
        [Button.inline("ℹ️ About", b"about")]
    ])

async def scheduled_news_update():
    await scrape_all_channels()

if __name__ == '__main__':
    create_tables()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_news_update, 'interval', minutes=30)
    scheduler.start()

    print("Bot is running...")
    bot.run_until_disconnected()