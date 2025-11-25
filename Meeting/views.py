# meetings/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import Meeting, Participant, ChatMessage, Reminder, Notepad, ScreenShareSession, MeetingRecording
from .serializers import (MeetingSerializer, ParticipantSerializer,
                          ChatMessageSerializer, ReminderSerializer,
                          NotepadSerializer, ScreenShareSerializer, RecordingSerializer)

class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all().order_by('start_at')
    serializer_class = MeetingSerializer

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        meeting = self.get_object()
        user = request.user if request.user.is_authenticated else None
        name = request.data.get('name') or (user.username if user else 'guest')
        participant, created = Participant.objects.get_or_create(meeting=meeting, user=user, name=name)
        if created:
            participant.joined_at = timezone.now()
            participant.status = 'waiting'
            participant.save()
        serializer = ParticipantSerializer(participant)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        meeting = self.get_object()
        user = request.user if request.user.is_authenticated else None
        name = request.data.get('name') or (user.username if user else None)
        qs = Participant.objects.filter(meeting=meeting)
        if user:
            qs = qs.filter(user=user)
        elif name:
            qs = qs.filter(name=name)
        p = qs.first()
        if not p:
            return Response({'detail':'participant not found'}, status=status.HTTP_404_NOT_FOUND)
        p.left_at = timezone.now()
        p.status = 'left'
        p.save()
        return Response({'detail':'left'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def start_screenshare(self, request, pk=None):
        meeting = self.get_object()
        participant_id = request.data.get('participant')
        p = Participant.objects.filter(id=participant_id, meeting=meeting).first()
        if not p:
            return Response({'detail': 'participant not found'}, status=status.HTTP_404_NOT_FOUND)
        ss = ScreenShareSession.objects.create(meeting=meeting, owner=p, is_active=True, started_at=timezone.now())
        return Response({'id': str(ss.id), 'is_active': ss.is_active}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def stop_screenshare(self, request, pk=None):
        meeting = self.get_object()
        ss_id = request.data.get('screenshare_id')
        ss = ScreenShareSession.objects.filter(id=ss_id, meeting=meeting).first()
        if not ss:
            return Response({'detail':'screenshare not found'}, status=status.HTTP_404_NOT_FOUND)
        ss.is_active = False
        ss.stopped_at = timezone.now()
        ss.save()
        return Response({'detail':'stopped'})

class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all().order_by('-joined_at')
    serializer_class = ParticipantSerializer

class ChatMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.all().order_by('created_at')
    serializer_class = ChatMessageSerializer

class ReminderViewSet(viewsets.ModelViewSet):
    queryset = Reminder.objects.all().order_by('created_at')
    serializer_class = ReminderSerializer

class NotepadViewSet(viewsets.ModelViewSet):
    queryset = Notepad.objects.all()
    serializer_class = NotepadSerializer

class RecordingViewSet(viewsets.ModelViewSet):
    queryset = MeetingRecording.objects.all().order_by('-uploaded_at')
    serializer_class = RecordingSerializer

@api_view(['POST'])
def process_due_reminders(request):
    now = timezone.now()
    processed = []
    qs = Reminder.objects.filter(status='scheduled')
    for r in qs:
        st = r.scheduled_time()
        if st and st <= now:
            r.status = 'sent'
            r.metadata.setdefault('delivered_at', now.isoformat())
            r.save(update_fields=['status','metadata'])
            processed.append(r)
            # In production: trigger actual channels/email/sms here
    serializer = ReminderSerializer(processed, many=True)
    return Response(serializer.data)
