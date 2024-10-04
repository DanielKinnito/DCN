from telethon import Button
from database import get_all_news_channels, add_user_preference, get_user_preferences
from news_scraper import get_latest_news

async def start_command(event):
    sender = await event.get_sender()
    await event.reply("Welcome to Daily Custom News Bot! Let's customize your news channels.")
    await show_channel_categories(event)

async def show_channel_categories(event):
    categories = ["News Channels", "Sport Channels"]
    buttons = [[Button.inline(category, f"category:{category}")] for category in categories]
    buttons.append([Button.inline("Finish Selection", "finish_selection")])
    await event.reply("Please select a category:", buttons=buttons)

async def show_channels_for_category(event, category):
    if category == "News Channels":
        channels = ["CNN", "BBC", "Al Jazeera", "Reuters", "Associated Press"]
    elif category == "Sport Channels":
        channels = ["ESPN", "Sky Sports", "Eurosport", "BBC Sport", "Fox Sports"]
    else:
        channels = []

    buttons = [[Button.inline(channel, f"channel:{channel}")] for channel in channels]
    buttons.append([Button.inline("Back to Categories", "back_to_categories")])
    await event.edit("Select channels to subscribe:", buttons=buttons)

async def channel_selection(event):
    sender = await event.get_sender()
    user_id = sender.id
    data = event.data.decode()

    if data.startswith("category:"):
        category = data.split(":")[1]
        await show_channels_for_category(event, category)
    elif data.startswith("channel:"):
        channel = data.split(":")[1]
        await toggle_channel_subscription(event, user_id, channel)
    elif data == "back_to_categories":
        await show_channel_categories(event)
    elif data == "finish_selection":
        await show_user_preferences(event, user_id)

async def toggle_channel_subscription(event, user_id, channel):
    current_preferences = get_user_preferences(user_id)
    if channel in current_preferences:
        current_preferences.remove(channel)
        message = f"Unsubscribed from {channel}"
    else:
        current_preferences.append(channel)
        message = f"Subscribed to {channel}"
    
    add_user_preference(user_id, current_preferences)
    await event.answer(message)

async def show_user_preferences(event, user_id):
    preferences = get_user_preferences(user_id)
    if preferences:
        message = "Your subscribed channels:\n" + "\n".join(preferences)
    else:
        message = "You haven't subscribed to any channels yet."
    
    buttons = [[Button.inline("Modify Selections", "back_to_categories")]]
    await event.edit(message, buttons=buttons)

async def send_news_update(bot, user_id, preferred_channels):
    for channel in preferred_channels:
        news_items = await get_latest_news(channel)
        for item in news_items:
            await bot.send_message(
                user_id,
                f"[{item['headline']}]({item['link']})",
                link_preview=True
            )
