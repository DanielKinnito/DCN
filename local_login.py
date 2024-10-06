import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os
from database import get_or_create_session, create_tables

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

async def main():
    print("Creating tables...")
    create_tables()
    print("Tables created successfully.")

    print("Starting Telegram client...")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)
    
    print("Generating session string...")
    session_string = client.session.save()
    print("Session string generated.")
    
    print("Saving session string to database...")
    get_or_create_session(session_string)
    print("Session string saved to database.")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())