# 🚀 Telegram Job Alert Bot

An automated Telegram bot that helps users find jobs by scraping popular Nigerian job boards. Users can input their skills and preferred roles, and the bot will automatically fetch matching job listings and deliver them straight to their Telegram chat every morning.

## ✨ Features

* **Custom Job Preferences:** Users can set their desired job titles, skills, and locations (e.g., "python developer lagos" or "remote cybersecurity intern").
* **Automated Daily Alerts:** Runs a scheduled background job every day at 8:00 AM (West Africa Time) to deliver fresh job listings.
* **Live Web Scraping:** Uses `BeautifulSoup` to pull real-time job postings directly from MyJobMag and Jobberman.
* **On-Demand Searching:** Includes a `/test` command so users can manually trigger a job search at any time without waiting for the morning alert.
* **Cloud-Ready:** Configured to be deployed as a 24/7 background worker on platforms like Render.

## 🛠️ Tech Stack

* **Language:** Python 3
* **Libraries:** 
  * `python-telegram-bot[job-queue]` (for the Telegram interface and task scheduling)
  * `BeautifulSoup4` & `requests` (for web scraping)
  * `pytz` (for timezone management)
  * `python-dotenv` (for environment variable security)
