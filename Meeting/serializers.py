# Meeting/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import (
    Meeting,
    Participant,
    ChatMessage,
    Reaction,
    Notepad,
    ScreenShareSession,
    Reminder,
    MeetingRecording,
)

# Meeting serializer (was missing)
class MeetingSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'description', 'organizer',
            'start_at', 'end_at', 'timezone', 'is_public',
            'max_participants', 'created_at', 'updated_at', 'participants'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_participants(self, obj):
        qs = obj.participants.all()
        return ParticipantSerializer(qs, many=True).data

class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = '__all__'
        read_only_fields = ('id', 'joined_at', 'left_at')

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class NotepadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notepad
        fields = '__all__'
        read_only_fields = ('id', 'updated_at')

class ScreenShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreenShareSession
        fields = '__all__'

class ReminderSerializer(serializers.ModelSerializer):
    scheduled_time = serializers.SerializerMethodField()

    class Meta:
        model = Reminder
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'status')

    def get_scheduled_time(self, obj):
        if obj.absolute_at:
            st = obj.absolute_at
        elif obj.offset_minutes is not None and obj.meeting and obj.meeting.start_at:
            st = obj.meeting.start_at - timezone.timedelta(minutes=obj.offset_minutes)
        else:
            st = None
        return st.isoformat() if st else None

class RecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingRecording
        fields = '__all__'
        read_only_fields = ('id', 'uploaded_at')
