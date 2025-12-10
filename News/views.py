# News/views.py

import feedparser
from bs4 import BeautifulSoup
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.conf import settings
from .models import NewsArticle
from .serializers import NewsArticleSerializer
from .rss_feeds import RSS_FEEDS
import requests
import time
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

# Fallback image - using a placeholder image service
FALLBACK_IMAGE = "https://via.placeholder.com/800x450/1a1a2e/eee?text=News+Image"

# Optional overrides: some publishers use non-standard or moved feed URLs.
# You can add known-good alternate endpoints here for problem sources.
FEED_OVERRIDES = {
    "KrishiJagran": ["https://krishijagran.com/rss/"],  # add known-good URL
}

def extract_image(entry):
    """
    Try multiple strategies to extract an image URL from a feed entry.
    Returns fallback image path when nothing found.
    """
    try:
        # 1) media_content (common in RSS feeds)
        if hasattr(entry, "media_content") and entry.media_content:
            for m in entry.media_content:
                url = m.get("url")
                if url and url.startswith("http"):
                    return url

        # 2) media_thumbnail
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            thumb = entry.media_thumbnail[0].get("url")
            if thumb and thumb.startswith("http"):
                return thumb

        # 3) enclosures (common in RSS 2.0)
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if enc.get("type", "").startswith("image") and enc.get("href"):
                    return enc.get("href")

        # 4) enclosure links (images)
        if hasattr(entry, "links"):
            for l in entry.links:
                if l.get("type", "").startswith("image") and l.get("href"):
                    return l.get("href")

        # 5) <img> tag inside summary/description (common in Indian news sites)
        summary_html = entry.get("summary", "") or entry.get("description", "") or entry.get("content", [{}])[0].get("value", "")
        if summary_html:
            soup = BeautifulSoup(summary_html, "html.parser")
            img = soup.find("img")
            if img:
                src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if src and src.startswith("http"):
                    return src
        
        # 6) Check for image in content field
        if hasattr(entry, "content") and entry.content:
            for content_item in entry.content:
                content_html = content_item.get("value", "")
                if content_html:
                    soup = BeautifulSoup(content_html, "html.parser")
                    img = soup.find("img")
                    if img:
                        src = img.get("src") or img.get("data-src")
                        if src and src.startswith("http"):
                            return src

    except Exception as e:
        logger.debug("extract_image error: %s", e)

    return FALLBACK_IMAGE

class FetchNewsAPI(APIView):
    """
    POST /api/fetch-news/
    Crawls each RSS feed and inserts new articles (deduplicated by link).
    Use this endpoint to seed DB or schedule it via cron/management command.
    """
    def post(self, request):
        new_count = 0
        errors = []

        for source, meta in RSS_FEEDS.items():
            url = meta.get("url")
            category = meta.get("category", "General")
            try:
                # Use a robust fetcher that tries multiple candidate URLs (fallbacks)
                # and performs retries with a real User-Agent. This helps against
                # sites that block non-browser clients, return HTML pages or moved feeds.
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36 TrueTalkBot/1.0"
                }

                def generate_candidate_urls(u):
                    # Generate sensible variations (http/https, feed/rss endpoints)
                    candidates = []
                    parsed = urlparse(u)
                    base = f"{parsed.scheme}://{parsed.netloc}"
                    path = parsed.path or ""

                    # Start with the provided URL
                    candidates.append(u)

                    # Add http variant if original is https
                    if parsed.scheme == "https":
                        candidates.append(u.replace("https://", "http://", 1))

                    # If path looks like a file, try /feed and /rss versions on the site root
                    if not path.endswith('/') and not path.endswith('.xml'):
                        candidates.append(base + path + '/rss')
                        candidates.append(base + path + '/feed')
                    # Generic feed endpoints at root
                    candidates.append(base + '/feed/')
                    candidates.append(base + '/rss')
                    candidates.append(base + '/rss.xml')

                    # Try replacing common segments
                    if '/feed/' in u:
                        candidates.append(u.replace('/feed/', '/rss/'))
                    if '/rss/' in u:
                        candidates.append(u.replace('/rss/', '/feed/'))

                    # Deduplicate while preserving order
                    seen = set()
                    result = []
                    for c in candidates:
                        if c and c not in seen:
                            seen.add(c)
                            result.append(c)
                    return result

                def try_fetch_and_parse(u):
                    max_retries = 2
                    last_exc = None
                    for attempt in range(max_retries + 1):
                        try:
                                resp = requests.get(u, headers=headers, timeout=10)
                                # raise_for_status will convert 4xx/5xx to HTTPError
                                resp.raise_for_status()
                                feed = feedparser.parse(resp.content)
                                # If the response is HTML (not an RSS/atom), look for
                                # a <link rel="alternate" type="application/rss+xml"> tag
                                # and try that URL as a fallback.
                                if not getattr(feed, 'entries', None):
                                    content_type = resp.headers.get('content-type', '').lower()
                                    if 'html' in content_type or b'<html' in resp.content[:200].lower():
                                        soup = BeautifulSoup(resp.content, 'html.parser')
                                        link_tag = soup.find('link', attrs={'type': 'application/rss+xml'}) or soup.find('link', attrs={'type': 'application/atom+xml'})
                                        if link_tag and link_tag.get('href'):
                                            candidate_feed = urljoin(u, link_tag.get('href'))
                                            # try fetching the discovered feed
                                            try:
                                                r2 = requests.get(candidate_feed, headers=headers, timeout=8)
                                                r2.raise_for_status()
                                                feed2 = feedparser.parse(r2.content)
                                                if getattr(feed2, 'entries', None):
                                                    return feed2, r2
                                            except Exception:
                                                # if this fails, fallthrough and let the caller continue
                                                pass
                                return feed, resp
                        except requests.exceptions.HTTPError as he:
                            # return the error so caller can report detailed message
                            last_exc = he
                            # don't retry for 4xx other than 429
                            if getattr(he.response, 'status_code', 0) in (429, 503):
                                # wait briefly and retry
                                time.sleep(1 + attempt)
                                continue
                            break
                        except Exception as e:
                            last_exc = e
                            time.sleep(1 + attempt)
                            continue
                    return None, last_exc

                # Allow per-source overrides to be tried before generated candidates
                candidate_urls = []
                if source in FEED_OVERRIDES:
                    candidate_urls.extend(FEED_OVERRIDES[source])
                candidate_urls.extend(generate_candidate_urls(url))
                feed = None
                resp = None
                debug_attempts = []

                for candidate in candidate_urls:
                    parsed_feed, parsed_resp = try_fetch_and_parse(candidate)
                    debug_attempts.append((candidate, parsed_resp, parsed_feed))
                    if parsed_feed and getattr(parsed_feed, 'entries', None):
                        feed = parsed_feed
                        resp = parsed_resp
                        break

                if not feed:
                    # No candidate produced entries — include detailed debug info
                    details = []
                    for c, r, f in debug_attempts:
                        if isinstance(r, requests.Response):
                            snippet = r.content[:500].decode(errors='replace')
                            details.append(f"{c} -> {r.status_code}: {snippet[:140]}")
                        else:
                            details.append(f"{c} -> exception: {r}")

                    msg = f"no usable feed for {source} ({url}) — tried: " + "; ".join(details)
                    logger.warning(msg)
                    errors.append({source: msg})
                    continue

                # feed parsed — but still check for bozo
                if getattr(feed, "bozo", False):
                    bozo_exc = getattr(feed, "bozo_exception", None)
                    logger.warning("Feed parse issue for %s (%s) — %s", source, url, bozo_exc)

                for entry in feed.entries:
                    title = entry.get("title", "") or "No title"
                    link = entry.get("link")
                    if not link:
                        continue

                    summary = BeautifulSoup(entry.get("summary", "") or entry.get("description", ""), "html.parser").get_text()
                    published = entry.get("published", "")
                    image = extract_image(entry)

                    try:
                        NewsArticle.objects.create(
                            title=title[:800],
                            summary=summary,
                            link=link,
                            published=published,
                            image=image,
                            source=source,
                            category=category
                        )
                        new_count += 1
                    except IntegrityError:
                        # duplicate link (skip)
                        continue
                    except Exception as err_inner:
                        logger.exception("Error saving article from %s: %s", source, err_inner)
                        continue

            except Exception as e:
                logger.exception("Error fetching feed %s: %s", source, e)
                errors.append({source: str(e)})
                continue

        return Response({"new_articles": new_count, "errors": errors}, status=status.HTTP_201_CREATED)


class CategoryNewsAPI(APIView):
    """
    GET /api/news/?category=Business&offset=0&limit=12
    Returns paginated results for given category (case-insensitive).
    If no matching category by field, fallback to source name filter.
    """
    def get(self, request):
        category = request.query_params.get("category")
        if not category:
            return Response({"error": "category param required"}, status=400)

        try:
            offset = int(request.query_params.get("offset", 0))
            limit = int(request.query_params.get("limit", 12))
        except ValueError:
            return Response({"error": "offset and limit must be integers"}, status=400)

        qs = NewsArticle.objects.filter(category__iexact=category)
        if not qs.exists():
            # fallback to source matching if category didn't match
            qs = NewsArticle.objects.filter(source__iexact=category)

        total = qs.count()
        items = qs.order_by("-created_at")[offset: offset + limit]
        serializer = NewsArticleSerializer(items, many=True)
        return Response({
            "total": total,
            "offset": offset,
            "limit": limit,
            "results": serializer.data
        })


class WeatherAPI(APIView):
    """
    GET /api/weather/?lat=...&lon=...
    Uses Open-Meteo (no API key). Returns current_weather object.
    """
    def get(self, request):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        if not lat or not lon:
            return Response({"error": "lat and lon required"}, status=400)
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            r = requests.get(url, timeout=6)
            r.raise_for_status()
            return Response(r.json())
        except Exception as e:
            logger.exception("Weather fetch failed: %s", e)
            return Response({"error": "weather fetch failed", "detail": str(e)}, status=500)


class StocksAPI(APIView):
    """
    GET /api/stocks/?symbol=...  (simple placeholder)
    Note: Reliable stock APIs are usually paid. This endpoint is a placeholder
    which returns 'not implemented' or you can wire in a free source if available.
    """
    def get(self, request):
        symbol = request.query_params.get("symbol")
        # For production, integrate a paid/authorized stock API.
        # Return clear response now:
        if not symbol:
            return Response({"error": "symbol required (e.g. NIFTY, RELIANCE)"}, status=400)
        return Response({"error": "stocks endpoint not implemented (use a market data API)"}, status=501)


class NewsChatbotAPI(APIView):
    """
    POST /api/news-chat/
    Chat with the news assistant about news articles
    
    Request body:
    {
        "message": "What's the latest tech news?",
        "category": "Technology" (optional - to provide context)
    }
    """
    
    SYSTEM_PROMPT = """You are an AI Assistant inside the News Section of an application.

Your job is to answer questions, summarize news, provide agriculture market prices, commodity prices, and help users navigate to different news sections based ONLY on the RSS feed articles provided to you.

You must NOT guess or create information. Everything must come from the RSS data.

CAPABILITIES:

1. General News (RSS-Based)
   - Summarize any news article
   - Provide 3-5 bullet points and short explanation
   - Show latest articles from requested category (Sports, World, Business, India, Telugu, Hindi, Tamil, Technology, Stock Market, Agriculture)
   - If date mentioned, filter articles from that date only

2. Agriculture Prices (RSS-Based)
   - Extract crop prices, mandi rates, vegetable prices, fruit prices from Agriculture RSS feeds
   - If exact price NOT found in RSS, say: "No price information available for this item."

3. Gold & Silver Prices (RSS-Based)
   - Extract gold (22K/24K) and silver prices from RSS feeds if available
   - Provide per gram, per 10 grams, per kg ONLY if RSS contains it
   - If city-based prices not in RSS, do NOT guess them

4. Price Trends
   - Identify words like "increase", "decrease", "rise", "fall", "stable"
   - Explain trend simply
   - If trend unclear, say: "Trend information not available."

5. Date-Based News (NEW!)
   - When user mentions a date like "December 10", "10-12-2025", "today", "yesterday", show news from that date
   - Examples: "news from December 10", "what happened on 10th Dec", "today's news", "yesterday's headlines"
   - Filter articles by the specified date
   - If no news found for that date, say: "No news articles found for that date."

6. Navigation
   - When user says "go to agriculture", "show tech news", "sports section" etc., navigate to that category
   - Available categories: Business, Telugu, Hindi, Tamil, Sports, Agriculture, World, India, Stock Market, Technology, Agriculture Business, Commodities


RESPONSE FORMAT - MUST BE VALID JSON:

For navigation requests:
{
  "action": "navigate",
  "category": "Agriculture",
  "message": "Sure! Taking you to Agriculture news section.",
  "reply": "Sure! Taking you to Agriculture news section."
}

For news/price requests:
{
  "action": "chat",
  "reply": "Here are the latest agriculture prices...",
  "message": "Here are the latest agriculture prices...",
  "articles": [
    {
      "title": "Article title",
      "summary": "Brief summary",
      "category": "Agriculture"
    }
  ],
  "prices": [
    {
      "item": "Tomato",
      "price": "₹40",
      "unit": "per kg",
      "location": "Delhi",
      "trend": "up",
      "source": "AgriWatch"
    }
  ]
}

NAVIGATION DETECTION:
- "go to agriculture" / "show agriculture news" → Navigate to Agriculture
- "show tech news" / "technology section" → Navigate to Technology
- "business news" / "show business" → Navigate to Business
- "sports news" / "go to sports" → Navigate to Sports
- "stock market" / "show stocks" → Navigate to Stock Market
- "telugu news" / "go to telugu" → Navigate to Telugu
- "hindi news" / "show hindi" → Navigate to Hindi
- "tamil news" / "go to tamil" → Navigate to Tamil
- "world news" / "international news" → Navigate to World
- "india news" / "indian news" → Navigate to India

STRICT RULES:
- Never invent prices or news
- Never assume values not present in RSS
- If no matching article or price found, say: "No relevant information found in current RSS data."
- Always return valid JSON
- Use "navigate" action when user wants to go to a section
- Use "chat" action for information requests
- Category names must match exactly: Business, Telugu, Hindi, Tamil, Sports, Agriculture, World, India, Stock Market, Technology
- Stay neutral, factual, and helpful

YOUR GOAL: Act as a unified assistant for news summaries, category navigation, agriculture market prices, and commodity updates using ONLY the RSS feed content."""
    
    
    def post(self, request):
        user_message = request.data.get('message')
        category = request.data.get('category', None)
        
        if not user_message:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get GROQ API key from environment variable
            import os
            from dotenv import load_dotenv
            
            # Load .env file (fallback if not loaded in settings)
            load_dotenv()
            
            groq_api_key = os.environ.get('GROQ_API_KEY')
            if not groq_api_key:
                logger.error("GROQ_API_KEY not found in environment")
                return Response(
                    {
                        "error": "GROQ_API_KEY not configured",
                        "response": "Sorry, the chatbot is not configured properly. Please contact support.",
                        "success": False
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Initialize Groq client
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            
            # Detect date in user message
            date_filter = self._extract_date_from_message(user_message)
            
            # Get recent news for context (with optional date filter)
            news_context = self._get_news_context(category, date_filter)
            
            # Create messages for the chat
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "system", "content": f"Current news context:\n{news_context}"},
                {"role": "user", "content": user_message}
            ]
            
            # Call Groq API
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=500,
                top_p=1,
                stream=False
            )
            
            # Extract response
            assistant_response = chat_completion.choices[0].message.content
            
            # Try to parse JSON response
            import json
            try:
                # Clean the response (remove markdown code blocks if present)
                cleaned_response = assistant_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                # Parse JSON
                parsed_response = json.loads(cleaned_response)
                
                # Return structured response (backward compatible)
                message_text = parsed_response.get("message") or parsed_response.get("reply", assistant_response)
                return Response({
                    "action": parsed_response.get("action", "chat"),
                    "category": parsed_response.get("category"),
                    "message": message_text,
                    "response": message_text,  # Backward compatibility
                    "reply": message_text,  # Alternative field
                    "articles": parsed_response.get("articles", []),
                    "prices": parsed_response.get("prices", []),
                    "success": True
                })
            except json.JSONDecodeError:
                # If not JSON, treat as regular chat response
                return Response({
                    "action": "chat",
                    "message": assistant_response,
                    "response": assistant_response,  # Backward compatibility
                    "reply": assistant_response,
                    "articles": [],
                    "prices": [],
                    "success": True
                })
            
        except Exception as e:
            logger.exception(f"Error in news chatbot: {e}")
            return Response(
                {
                    "error": "Failed to process chat request",
                    "response": "Sorry, I encountered an error. Please try again.",
                    "detail": str(e),
                    "success": False
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_news_context(self, category=None, date_filter=None):
        """Get recent news articles to provide context to the chatbot"""
        try:
            from datetime import datetime, timedelta
            
            # Start with all articles
            queryset = NewsArticle.objects.all()
            
            # Filter by category if provided
            if category:
                queryset = queryset.filter(category__iexact=category)
            
            # Filter by date if provided
            if date_filter:
                try:
                    # Parse the date (supports formats like "2025-12-10", "10-12-2025", "Dec 10", etc.)
                    from dateutil import parser
                    target_date = parser.parse(date_filter).date()
                    
                    # Get articles from that specific date
                    queryset = queryset.filter(
                        created_at__date=target_date
                    )
                except:
                    # If date parsing fails, try to get articles from today
                    pass
            
            # Order by most recent and limit
            articles = queryset.order_by('-created_at')[:10]
            
            if not articles:
                if date_filter:
                    return f"No news articles found for date: {date_filter}"
                return "No recent news articles available."
            
            # Build context
            context_lines = []
            if date_filter:
                context_lines.append(f"News articles from {date_filter}:")
            else:
                context_lines.append("Recent news headlines:")
            
            for article in articles:
                date_str = article.created_at.strftime("%Y-%m-%d")
                context_lines.append(f"- [{article.category}] ({date_str}) {article.title[:100]}")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"Error getting news context: {e}")
            return "Unable to fetch recent news."
    
    def _extract_date_from_message(self, message):
        """Extract date from user message if present"""
        try:
            from datetime import datetime, timedelta
            import re
            
            message_lower = message.lower()
            
            # Check for "today"
            if "today" in message_lower:
                return datetime.now().strftime("%Y-%m-%d")
            
            # Check for "yesterday"
            if "yesterday" in message_lower:
                yesterday = datetime.now() - timedelta(days=1)
                return yesterday.strftime("%Y-%m-%d")
            
            # Try to find date patterns
            # Pattern 1: YYYY-MM-DD or DD-MM-YYYY
            date_patterns = [
                r'\d{4}-\d{1,2}-\d{1,2}',  # 2025-12-10
                r'\d{1,2}-\d{1,2}-\d{4}',  # 10-12-2025
                r'\d{1,2}/\d{1,2}/\d{4}',  # 10/12/2025
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, message)
                if match:
                    return match.group(0)
            
            # Pattern 2: Month names (December 10, Dec 10, 10 December)
            month_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}|\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*'
            match = re.search(month_pattern, message_lower)
            if match:
                return match.group(0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting date: {e}")
            return None
