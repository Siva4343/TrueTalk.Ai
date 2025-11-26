# calendarapp/views.py
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from .models import Event, Reminder
from .serializers import EventSerializer, ReminderSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow safe methods for anyone, write methods only for the owner.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, "owner", None) == request.user


class EventViewSet(viewsets.ModelViewSet):
    """
    Event endpoints: list, retrieve, create, update, delete.
    For development we allow anonymous writes; in production change this to
    IsAuthenticatedOrReadOnly and require authentication on the frontend.
    """
    queryset = Event.objects.all().order_by("start_time")
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]  # dev only

    def perform_create(self, serializer):
        """
        Save owner as the authenticated user when present.
        If the request is anonymous (no authenticated user), fall back to
        the first superuser (development convenience) so tests and the UI
        can create events without authentication.
        """
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            serializer.save(owner=user)
            return

        # dev fallback: attach first superuser if available
        User = get_user_model()
        admin = User.objects.filter(is_superuser=True).first()
        if admin:
            serializer.save(owner=admin)
            return

        # last resort: attempt to save without owner (might fail if owner is required)
        serializer.save()


class ReminderViewSet(viewsets.ModelViewSet):
    """
    Reminder endpoints. Creates/updates reminders tied to an Event.
    We override create() to return clearer validation errors if the event
    id is missing or invalid.
    """
    queryset = Reminder.objects.all().order_by("remind_at")
    serializer_class = ReminderSerializer
    permission_classes = [permissions.AllowAny]  # dev only
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["event"]

    def create(self, request, *args, **kwargs):
        """
        Ensure we return a helpful error when 'event' is missing/invalid.
        Accepts payload like: {"event": <id>, "remind_at": "...", "message": "..."}
        """
        data = request.data
        # quick validation: event present
        event_id = data.get("event")
        if event_id is None:
            return Response({"event": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        # delegate to serializer (this will validate remind_at, FK etc.)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # keep default perform_create from ModelViewSet (it will call serializer.save())


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def due_reminders(request):
    """
    Returns reminders that are due and not yet sent.

    Accepts optional query param:
      - since=<ISO8601 timestamp> : only return reminders with remind_at > since and remind_at <= now

    If `since` is not provided, default window is `now - DEFAULT_WINDOW` to now (prevents firing very old reminders).
    """
    DEFAULT_WINDOW_MINUTES = 2  # adjust as you prefer

    now = timezone.now()

    since_param = request.GET.get("since")
    if since_param:
        try:
            since = timezone.datetime.fromisoformat(since_param)
            # if naive, assume timezone-aware using Django settings
            if timezone.is_naive(since):
                since = timezone.make_aware(since, timezone.get_default_timezone())
            since = timezone.localtime(since)  # normalize
        except Exception:
            return Response({"detail": "Invalid 'since' parameter; expected ISO8601."},
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        since = now - timedelta(minutes=DEFAULT_WINDOW_MINUTES)

    # Only reminders with remind_at in (since, now] and not yet sent
    due_qs = Reminder.objects.filter(remind_at__gt=since, remind_at__lte=now, is_sent=False)
    serializer = ReminderSerializer(due_qs, many=True)
    return Response(serializer.data)

