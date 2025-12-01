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

# Fallback image - using the user-uploaded screenshot path
FALLBACK_IMAGE = "/mnt/data/Screenshot (19).png"

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
