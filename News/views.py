import feedparser
from bs4 import BeautifulSoup
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from .models import NewsArticle
from .serializers import NewsArticleSerializer
from .rss_feeds import RSS_FEEDS
import requests

# Fallback image uses your uploaded screenshot file (developer-provided path).
FALLBACK_IMAGE = "/mnt/data/Screenshot (19).png"

def extract_image(entry):
    """Attempt multiple strategies to find an image URL for an RSS entry."""
    try:
        # 1. media_content
        if hasattr(entry, "media_content") and entry.media_content:
            url = entry.media_content[0].get("url")
            if url:
                return url

        # 2. media_thumbnail
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            url = entry.media_thumbnail[0].get("url")
            if url:
                return url

        # 3. enclosure links
        if hasattr(entry, "links") and entry.links:
            for l in entry.links:
                if l.get("type", "").startswith("image"):
                    return l.get("href")

        # 4. <img> tag inside summary/description
        if hasattr(entry, "summary") and entry.summary:
            soup = BeautifulSoup(entry.summary, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                return img.get("src")
    except Exception:
        pass

    return FALLBACK_IMAGE

class FetchNewsAPI(APIView):
    """POST to fetch all RSS feeds and store new articles in DB."""

    def post(self, request):
        new_count = 0
        for source_name, meta in RSS_FEEDS.items():
            url = meta.get("url")
            category = meta.get("category", "General")
            try:
                feed = feedparser.parse(url)
                # proceed even if bozo; entries may be present
                for entry in feed.entries:
                    title = entry.get("title", "") or "No title"
                    link = entry.get("link", "")
                    if not link:
                        continue
                    summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text()
                    published = entry.get("published", "") or ""
                    image = extract_image(entry)

                    try:
                        NewsArticle.objects.create(
                            title=title[:800],
                            summary=summary,
                            link=link,
                            published=published,
                            image=image,
                            source=source_name,
                            category=category
                        )
                        new_count += 1
                    except IntegrityError:
                        # duplicate based on unique link
                        continue
                    except Exception:
                        continue
            except Exception as e:
                print("Error fetching", source_name, e)
                continue

        return Response({"new_articles": new_count}, status=status.HTTP_201_CREATED)

class CategoryNewsAPI(APIView):
    """GET /api/news/?category=Business&offset=0&limit=12"""
    def get(self, request):
        q = request.query_params
        category = q.get("category")
        offset = int(q.get("offset", 0))
        limit = int(q.get("limit", 12))

        if not category:
            return Response({"error": "category param required"}, status=400)

        # filter by category (case insensitive) or by source name
        qs = NewsArticle.objects.filter(category__iexact=category)
        if not qs.exists():
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
    """GET /api/weather/?lat=..&lon=.. -> fetch from Open-Meteo (no API key)"""
    def get(self, request):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        if not lat or not lon:
            return Response({"error": "lat and lon required"}, status=400)
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            r = requests.get(url, timeout=6)
            payload = r.json()
            return Response(payload)
        except Exception as e:
            return Response({"error": "weather fetch failed", "detail": str(e)}, status=500)
