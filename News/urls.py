# News/urls.py

from django.urls import path
from .views import CategoryNewsAPI, FetchNewsAPI, WeatherAPI, StocksAPI

urlpatterns = [
    path("news/", CategoryNewsAPI.as_view(), name="category-news"),
    path("fetch-news/", FetchNewsAPI.as_view(), name="fetch-news"),
    path("weather/", WeatherAPI.as_view(), name="weather"),
    path("stocks/", StocksAPI.as_view(), name="stocks"),
]
