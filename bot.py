import os
import datetime
import pytz
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Dictionary to store user preferences
user_data = {}

def scrape_jobs(keyword):
    """
    Scrapes job boards for the given keyword.
    Note: Real scraping for LinkedIn requires complex bypasses. 
    This uses a basic requests approach for MyJobMag and Jobberman.
    """
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    search_query = keyword.replace(" ", "+")

    # 1. Scrape MyJobMag
    try:
        url = f"https://www.myjobmag.com/search/jobs?q={search_query}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find job listings on the page
        for job_card in soup.select('.job-info')[:3]:
            title_element = job_card.select_one('h2 a')
            if title_element:
                title = title_element.text.strip()
                link = "https://www.myjobmag.com" + title_element['href']
                jobs.append(f"📌 *{title}*\n🔗 {link}")
    except Exception as e:
        print(f"MyJobMag scrape error: {e}")

    # 2. Scrape Jobberman (Placeholder logic for structure)
    try:
        url = f"https://www.jobberman.com/jobs?q={search_query}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for job_card in soup.select(r'.mx-5.md\:mx-0')[:2]:
            title_element = job_card.select_one('p.text-lg')
            link_element = job_card.select_one('a')
            if title_element and link_element:
                title = title_element.text.strip()
                link = link_element['href']
                jobs.append(f"📌 *{title}*\n🔗 {link}")
    except Exception as e:
        print(f"Jobberman scrape error: {e}")

    if not jobs:
        return ["No new jobs found today matching your skills."]
    return jobs

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Job Alert Bot!\n\n"
        "Send me your skills and preferred role like this:\n"
        "Example: *cybersecurity intern remote*",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.lower()
    
    # Save the user's preferred job title
    user_data[chat_id] = text
    
    await update.message.reply_text(
        f"✅ Got it! I will send you jobs matching: *{text}*\n\n"
        "Alerts will be sent every day at 8 AM.",
        parse_mode="Markdown"
    )

async def send_daily_alerts(context: ContextTypes.DEFAULT_TYPE):
    """Function that runs every day at 8 AM to send jobs to all saved users."""
    for chat_id, keyword in user_data.items():
        await context.bot.send_message(
            chat_id=chat_id, 
            text=f"🌅 Good morning! Searching for the latest *{keyword}* jobs...",
            parse_mode="Markdown"
        )
        
        # Fetch the jobs
        jobs = scrape_jobs(keyword)
        
        # Send each job as a separate message
        for job in jobs:
            await context.bot.send_message(chat_id=chat_id, text=job, parse_mode="Markdown")

async def test_scraper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to manually trigger the scraper for testing."""
    chat_id = update.message.chat_id
    keyword = user_data.get(chat_id, "python") # Uses your saved keyword, or defaults to python
    
    await update.message.reply_text("🔍 Manually triggering job search. Please wait...")
    
    jobs = scrape_jobs(keyword)
    
    for job in jobs:
        await update.message.reply_text(job, parse_mode="Markdown")

def main():
    request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    app = Application.builder().token(BOT_TOKEN).request(request).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_scraper))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Configure the 8 AM Scheduler (Set to Lagos Time)
    lagos_tz = pytz.timezone('Africa/Lagos')
    target_time = datetime.time(hour=8, minute=0, second=0, tzinfo=lagos_tz)
    
    app.job_queue.run_daily(send_daily_alerts, time=target_time)

    print("Bot is running with the 8 AM scraper active...")
    app.run_polling()

if __name__ == "__main__":
    main()