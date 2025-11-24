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
import logging

logger = logging.getLogger(__name__)

# Fallback image - using the user-uploaded screenshot path
FALLBACK_IMAGE = "/mnt/data/Screenshot (19).png"

def extract_image(entry):
    """
    Try multiple strategies to extract an image URL from a feed entry.
    Returns fallback image path when nothing found.
    """
    try:
        # 1) media_content (common)
        if hasattr(entry, "media_content") and entry.media_content:
            for m in entry.media_content:
                url = m.get("url")
                if url:
                    return url

        # 2) media_thumbnail
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            thumb = entry.media_thumbnail[0].get("url")
            if thumb:
                return thumb

        # 3) enclosure links (images)
        if hasattr(entry, "links"):
            for l in entry.links:
                if l.get("type", "").startswith("image"):
                    return l.get("href")

        # 4) <img> tag inside summary/description
        summary_html = entry.get("summary", "") or entry.get("description", "")
        if summary_html:
            soup = BeautifulSoup(summary_html, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                return img.get("src")
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
                feed = feedparser.parse(url)
                if getattr(feed, "bozo", False):
                    # feed.bozo indicates parse issues; still proceed if entries exist
                    logger.warning("Feed parse issue for %s (%s)", source, url)

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
