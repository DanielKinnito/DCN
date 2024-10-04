# Daily Custom News Bot Documentation

## Overview
This Telegram bot allows users to receive customized news updates from their preferred Telegram news channels. The bot scrapes news from specified channels and sends updates to users twice a day.

## Features
- User preference selection for news channels
- Scheduled news updates at 1 PM and 7 PM (Moscow time, GMT+3)
- News displayed in headline mode with links to full articles
- Integration with Telegram's Instant View for article reading

## Setup
1. Install required packages: `pip install -r requirements.txt`
2. Set up PostgreSQL database and update `.env` file with credentials
3. Run `python main.py` to start the bot

## Usage
- Start the bot with `/start` command
- Select preferred news channels
- Receive news updates automatically at scheduled times

## File Structure
- `main.py`: Main bot script
- `database.py`: Database operations
- `news_scraper.py`: News scraping functionality
- `bot_handlers.py`: Bot command handlers
- `utils.py`: Utility functions

## Dependencies
- Telethon
- python-dotenv
- psycopg2-binary
- APScheduler

## Configuration
Update the `.env` file with your Telegram API credentials and database URL.

## Notes
- Ensure that the bot has permission to access the specified news channels
- The bot uses Moscow time (GMT+3) for scheduling news updates
