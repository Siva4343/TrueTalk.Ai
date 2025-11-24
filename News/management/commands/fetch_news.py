# News/management/commands/fetch_news.py

from django.core.management.base import BaseCommand
from News.views import FetchNewsAPI
from rest_framework.test import APIRequestFactory

class Command(BaseCommand):
    help = "Fetch RSS feeds and store new news articles"

    def handle(self, *args, **options):
        factory = APIRequestFactory()
        request = factory.post('/api/fetch-news/')
        view = FetchNewsAPI.as_view()
        response = view(request)
        # response.data contains result
        self.stdout.write(self.style.SUCCESS(f"Fetch finished: {response.data}"))
