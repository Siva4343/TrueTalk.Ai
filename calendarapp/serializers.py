# calendarapp/serializers.py
from rest_framework import serializers
from .models import Event, Reminder

class EventNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("id", "title", "start_time", "end_time")

class ReminderSerializer(serializers.ModelSerializer):
    # keep event writable for create/update via PrimaryKey
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all(), write_only=True)
    event_detail = EventNestedSerializer(source="event", read_only=True)

    class Meta:
        model = Reminder
        fields = ("id", "event", "event_detail", "remind_at", "message", "is_sent", "created_at")
        read_only_fields = ("id", "is_sent", "created_at")

class EventSerializer(serializers.ModelSerializer):
    # mark owner read-only so DRF does not expect it in POST body;
    # view.perform_create will set owner=request.user
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    reminders = ReminderSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ("created_at", "owner")
