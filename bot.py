from keep_alive import keep_alive
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

user_data = {}
sent_jobs = set()  # Keeps track of sent links to avoid duplicates

def scrape_jobs(keyword):
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    search_query = keyword.replace(" ", "+")

    # --- 1. MyJobMag ---
    try:
        url = f"https://www.myjobmag.com/search/jobs?q={search_query}"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html.parser')
        for job_card in soup.select('.job-info')[:3]:
            title_el = job_card.select_one('h2 a')
            if title_el:
                link = "https://www.myjobmag.com" + title_el['href']
                if link not in sent_jobs:
                    jobs.append(f"📌 *{title_el.text.strip()}*\n🏢 MyJobMag\n🔗 {link}")
                    sent_jobs.add(link)
    except: pass

    # --- 2. Jobberman ---
    try:
        url = f"https://www.jobberman.com/jobs?q={search_query}"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html.parser')
        for job_card in soup.select(r'.mx-5.md\:mx-0')[:3]:
            title_el = job_card.select_one('p.text-lg')
            link_el = job_card.select_one('a')
            if title_el and link_el:
                link = link_el['href']
                if link not in sent_jobs:
                    jobs.append(f"📌 *{title_el.text.strip()}*\n🏢 Jobberman\n🔗 {link}")
                    sent_jobs.add(link)
    except: pass

    # --- 3. HotNigerianJobs ---
    try:
        url = f"https://www.hotnigerianjobs.com/search/?q={search_query}"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html.parser')
        for link_el in soup.select('.job_title_link')[:3]:
            link = link_el['href']
            if link not in sent_jobs:
                jobs.append(f"📌 *{link_el.text.strip()}*\n🏢 HotNigerianJobs\n🔗 {link}")
                sent_jobs.add(link)
    except: pass

    # --- 4. JoblistNigeria ---
    try:
        url = f"https://www.joblistnigeria.com/search-jobs/{search_query}"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html.parser')
        for title_el in soup.select('.job-title a')[:3]:
            link = title_el['href']
            if link not in sent_jobs:
                jobs.append(f"📌 *{title_el.text.strip()}*\n🏢 JoblistNigeria\n🔗 {link}")
                sent_jobs.add(link)
    except: pass

    # --- 5. LinkedIn (Web Search Shortcut) ---
    # LinkedIn blocks standard scraping, so we provide a direct filtered search link
    linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={search_query}&location=Nigeria&refresh=true"
    jobs.append(f"🔍 *Live LinkedIn Results*\n🏢 LinkedIn\n🔗 {linkedin_url}")

    if not jobs or len(jobs) == 1: # Only LinkedIn link found
        return ["No fresh jobs found in the last 24 hours. Check back later!"]
    
    return jobs

# Keep all your other Telegram functions (start, handle_message, send_daily_alerts, etc.) exactly as they were

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Send me your skills (e.g., Python Developer) to start.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.lower()
    user_data[chat_id] = text
    await update.message.reply_text(f"✅ Monitoring *{text}*. Daily alerts at 8 AM.")

async def send_daily_alerts(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, keyword in user_data.items():
        jobs = scrape_jobs(keyword)
        for job in jobs:
            await context.bot.send_message(chat_id=chat_id, text=job, parse_mode="Markdown")

async def test_scraper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    keyword = user_data.get(chat_id, "python")
    await update.message.reply_text("🔍 Scanning 5 job sites...")
    jobs = scrape_jobs(keyword)
    for job in jobs:
        await update.message.reply_text(job, parse_mode="Markdown")

def main():
    keep_alive() 
    request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    app = Application.builder().token(BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_scraper))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    lagos_tz = pytz.timezone('Africa/Lagos')
    target_time = datetime.time(hour=8, minute=0, second=0, tzinfo=lagos_tz)
    app.job_queue.run_daily(send_daily_alerts, time=target_time)
    app.run_polling()

if __name__ == "__main__":
    main()