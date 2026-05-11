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
DB_FILE = "jobs_done.txt"

def get_sent_jobs():
    if not os.path.exists(DB_FILE):
        return set()
    with open(DB_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_sent_job(link):
    with open(DB_FILE, "a") as f:
        f.write(link + "\n")

def scrape_jobs(keyword):
    jobs = []
    sent_jobs = get_sent_jobs()
    
    # Upgraded headers to bypass basic bot-blockers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    search_query = keyword.replace(" ", "+")

    # 1. MyJobMag
    try:
        url = f"https://www.myjobmag.com/search/jobs?q={search_query}"
        soup = BeautifulSoup(requests.get(url, headers=headers, timeout=10).text, 'html.parser')
        mj_count = 0
        for a in soup.find_all('a', href=True):
            if '/job/' in a['href'] and mj_count < 3:
                link = "https://www.myjobmag.com" + a['href'] if not a['href'].startswith('http') else a['href']
                if link not in sent_jobs:
                    title = a.text.strip() or "New Job Lead"
                    if len(title) > 5: # Filters out blank image links
                        jobs.append(f"📌 *{title}*\n🏢 MyJobMag\n🔗 {link}")
                        save_sent_job(link)
                        mj_count += 1
    except: pass

    # 2. Jobberman
    try:
        url = f"https://www.jobberman.com/jobs?q={search_query}"
        soup = BeautifulSoup(requests.get(url, headers=headers, timeout=10).text, 'html.parser')
        jb_count = 0
        for a in soup.find_all('a', href=True):
            if '/jobs/' in a['href'] and 'jobberman.com' in a['href'] and jb_count < 3:
                link = a['href']
                if link not in sent_jobs:
                    jobs.append(f"📌 *Job Opportunity*\n🏢 Jobberman\n🔗 {link}")
                    save_sent_job(link)
                    jb_count += 1
    except: pass

    # 3. HotNigerianJobs (Fixed Selectors)
    try:
        url = f"https://www.hotnigerianjobs.com/search/?q={search_query}"
        soup = BeautifulSoup(requests.get(url, headers=headers, timeout=10).text, 'html.parser')
        hnj_count = 0
        for a in soup.find_all('a', href=True):
            if '/hotjobs/' in a['href'] and hnj_count < 3:
                link = "https://www.hotnigerianjobs.com" + a['href'] if not a['href'].startswith('http') else a['href']
                if link not in sent_jobs:
                    title = a.text.strip() or "New HotNigerianJob"
                    if len(title) > 5:
                        jobs.append(f"📌 *{title}*\n🏢 HotNigerianJobs\n🔗 {link}")
                        save_sent_job(link)
                        hnj_count += 1
    except: pass

    # 4. Jobgurus (New Source!)
    try:
        url = f"https://www.jobgurus.com.ng/jobs/search?keyword={search_query}"
        soup = BeautifulSoup(requests.get(url, headers=headers, timeout=10).text, 'html.parser')
        jg_count = 0
        for a in soup.find_all('a', href=True):
            if '/job/' in a['href'] and jg_count < 3:
                link = a['href'] if a['href'].startswith('http') else "https://www.jobgurus.com.ng" + a['href']
                if link not in sent_jobs:
                    title = a.text.strip() or "New Jobgurus Lead"
                    if len(title) > 5:
                        jobs.append(f"📌 *{title}*\n🏢 Jobgurus\n🔗 {link}")
                        save_sent_job(link)
                        jg_count += 1
    except: pass

    # 5. LinkedIn (Direct Search Link)
    linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={search_query}&location=Nigeria&f_TPR=r86400"
    jobs.append(f"🔍 *Fresh LinkedIn Results (Last 24h)*\n🏢 LinkedIn\n🔗 {linkedin_url}")

    return jobs


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
        if len(jobs) <= 1:
            continue 
        for job in jobs:
            await context.bot.send_message(chat_id=chat_id, text=job, parse_mode="Markdown")

async def test_scraper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    keyword = user_data.get(chat_id, "python")
    await update.message.reply_text(f"🔍 Scanning all 5 sites for NEW *{keyword}* leads...")
    jobs = scrape_jobs(keyword)
    
    if len(jobs) <= 1:
        await update.message.reply_text("No totally new jobs found right now. I'll keep monitoring!")
    
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