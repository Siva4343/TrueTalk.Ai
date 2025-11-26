# calendarapp/urls.py
from rest_framework import routers
from django.urls import path, include
from .views import EventViewSet, ReminderViewSet, due_reminders

router = routers.DefaultRouter()
router.register(r"events", EventViewSet, basename="event")
router.register(r"reminders", ReminderViewSet, basename="reminder")

urlpatterns = [
    # place the explicit endpoint before the router so 'reminders/due/' doesn't get
    # interpreted as a 'reminder' pk by the router's detail route.
    path("reminders/due/", due_reminders, name="reminders-due"),

    # then include router urls (events, reminders list/detail)
    path("", include(router.urls)),
]
