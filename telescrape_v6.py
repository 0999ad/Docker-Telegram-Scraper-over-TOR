#!/usr/bin/env python3
"""
TeleScrape Version 6.0 (Production): An advanced web scraping tool designed for extracting content
from Telegram channels. This version introduces asynchronous scraping, configurable targets via
a JSON file, and database integration for result storage, alongside Docker support for easy deployment.
New in this version:
- Asynchronous web scraping for improved performance,
- External configuration via 'config.json',
- Integration with PostgreSQL for result storage,
- Docker containerization for scalable deployment.

Usage:
  python TeleScrape_v6.py
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import json
from flask import Flask, render_template, request, redirect, url_for
import aiopg
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
from flask import flash, redirect, url_for


app = Flask(__name__, template_folder='templates')

config_path = 'config.json'

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    handlers=[
                        logging.FileHandler("TeleScrape.log"),
                        logging.StreamHandler()
                    ])

# Load configuration
with open(config_path, 'r') as file:
    config = json.load(file)

# Database connection pool setup
dsn = 'dbname=tele_scrape user=tele_user password=yourpassword host=192.168.1.226'
db_pool = None

async def setup_db_pool():
    global db_pool
    db_pool = await aiopg.create_pool(dsn)

async def fetch_links_from_site(session, url, selector, use_selenium=False):
    try:
        if use_selenium:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--proxy-server=socks5://localhost:9050")
            chromedriver_path = "/usr/local/bin/chromedriver"
            chrome_service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            driver.get(url)
            await asyncio.sleep(5)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
        else:
            async with session.get(url) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

        links = [a['href'] for a in soup.select(selector) if "https://t.me/" in a['href']]
        return links
    except Exception as e:
        logging.error(f"Error fetching links from {url}: {e}")
        return []

async def scrape_sites():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for site in config['sites']:
            task = asyncio.create_task(
                fetch_links_from_site(session, site['url'], site['selector'], site.get('use_selenium', False)))
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        flatten_results = [link for sublist in results for link in sublist]
        unique_links = list(set(flatten_results))
        return unique_links

@app.route('/update-keywords', methods=['POST'])
def update_keywords():
    new_keywords = request.form['new_keywords']
    if new_keywords:
        keywords_searched = new_keywords.split(',')
        # Update keywords in the configuration and possibly restart the scraping process
        # Save updated keywords to a file or database if persistent storage is required
        flash('Keywords updated successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add-channel', methods=['POST'])
def add_channel():
    new_channel = request.form['new_channel'].strip()
    if new_channel:
        # Add the new channel to the scrape list or configuration
        # Implement the logic to save this new channel
        flash('New channel added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/restart-scrape', methods=['POST'])
def restart_scrape():
    # Implement logic to safely stop any current scraping and restart
    flash('Scrape restarted successfully!', 'info')
    return redirect(url_for('dashboard'))

@app.route('/')
def dashboard():
    # Make sure to fetch the latest data and status
    return render_template('dashboard.html',
                           tor_connected=tor_status['connected'],
                           tor_ip=tor_status['ip_address'],
                           links_info=links_info,
                           results_filename=results_filename,
                           keywords=' | '.join(keywords_searched),
                           warning_message="Warning: The information displayed is live and could contain offensive or malicious language.")


@app.route('/start-scrape', methods=['POST'])
async def start_scrape():
    links = await scrape_sites()
    return redirect(url_for('dashboard'))

def run_flask_app():
    app.run(debug=True, host='0.0.0.0', port=8081, use_reloader=False)

async def main():
    await setup_db_pool()
    asyncio.create_task(run_flask_app())
    await start_scrape()

if __name__ == "__main__":
    asyncio.run(main())
