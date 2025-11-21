from django.urls import path
from .views import CategoryNewsAPI, FetchNewsAPI, WeatherAPI

urlpatterns = [
    path("news/<str:category>/", CategoryNewsAPI.as_view(), name="category-news"),
    path("fetch-news/", FetchNewsAPI.as_view(), name="fetch-news"),
    path("weather/", WeatherAPI.as_view(), name="weather"),
]
