from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
import logging
import requests

logger = logging.getLogger(__name__)

def fetch_news_job():
    """
    Job function that calls the fetch news API endpoint.
    This runs every hour to keep news fresh.
    """
    try:
        logger.info("Starting scheduled news fetch...")
        # Call the internal API endpoint
        response = requests.post('http://127.0.0.1:8000/api/fetch-news/', timeout=120)
        if response.status_code == 201:
            data = response.json()
            logger.info(f"News fetch completed: {data.get('new_articles', 0)} new articles added")
        else:
            logger.error(f"News fetch failed with status {response.status_code}")
    except Exception as e:
        logger.exception(f"Error in scheduled news fetch: {e}")

def start_scheduler():
    """
    Start the background scheduler for automatic news fetching.
    """
    scheduler = BackgroundScheduler()
    
    # Schedule the job to run every hour
    scheduler.add_job(
        fetch_news_job,
        trigger=IntervalTrigger(hours=1),
        id='fetch_news_hourly',
        name='Fetch news articles every hour',
        replace_existing=True
    )
    
    # Also run immediately on startup
    scheduler.add_job(
        fetch_news_job,
        id='fetch_news_startup',
        name='Fetch news on startup',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("News scheduler started - fetching news every hour")
    
    return scheduler
