# meetings/admin.py
from django.contrib import admin
from .models import (Meeting, Participant, ChatMessage, Reaction,
                     Notepad, ScreenShareSession, Reminder, MeetingRecording)

admin.site.register(Meeting)
admin.site.register(Participant)
admin.site.register(ChatMessage)
admin.site.register(Reaction)
admin.site.register(Notepad)
admin.site.register(ScreenShareSession)
admin.site.register(Reminder)
admin.site.register(MeetingRecording)

