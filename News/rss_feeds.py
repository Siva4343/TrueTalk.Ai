# News/rss_feeds.py

RSS_FEEDS = {
    # Business
    "Economic Times": {
        "url": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
        "category": "Business",
    },

    # Telugu
    "Eenadu": {
        "url": "https://www.eenadu.net/rss/home.xml",
        "category": "Telugu",
    },

    # Hindi
    "Jagran": {
        "url": "https://www.jagran.com/rss/news-national.xml",
        "category": "Hindi",
    },

    # Tamil
    "Dinamani": {
        "url": "https://www.dinamani.com/rss/latest.xml",
        "category": "Tamil",
    },

    # Sports
    "IndiaToday-Sports": {
        "url": "https://www.indiatoday.in/rss/1206571",  # India Today sports RSS (works as general)
        "category": "Sports",
    },

    # Agriculture (3 feeds aggregated under same category)
    "KrishiJagran": {
        "url": "https://krishijagran.com/feed/",
        "category": "Agriculture",
    },
    "AgriTimes": {
        "url": "https://agritimes.co.in/feed/",
        "category": "Agriculture",
    },
    "IndianExpress-Agri": {
        "url": "https://indianexpress.com/section/india/feed/",  # Agriculture items may appear here
        "category": "Agriculture",
    },

    # World
    "BBC-World": {
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "World",
    },

    # India-general
    "TimesOfIndia": {
        "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "category": "India",
    }
}
