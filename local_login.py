import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os
from database import get_or_create_session

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

async def main():
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)
    
    session_string = client.session.save()
    await get_or_create_session(session_string)
    
    print("Session string saved to database. You can now run the scraper in GitHub Actions.")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())