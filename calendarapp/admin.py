# calendarapp/admin.py
from django.contrib import admin
from django.apps import apps

# Lazy model retrieval avoids import-time errors if models can't be imported immediately.
Event = apps.get_model('calendarapp', 'Event')
Reminder = apps.get_model('calendarapp', 'Reminder')

if Event is not None:
    try:
        admin.site.register(Event)
    except Exception:
        # If the model registration fails, ignore — we'll debug the models separately.
        pass

if Reminder is not None:
    try:
        admin.site.register(Reminder)
    except Exception:
        pass

