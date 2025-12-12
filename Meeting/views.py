"""
Django REST Framework Views for Video Meeting System
Complete API implementation for TrueTalk.AI Meeting App
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import jwt
from datetime import datetime, timedelta

from .models import (
    Meeting, MeetingParticipant, ChatMessage,
    MeetingRecording, MeetingReaction, MeetingInvitation,
    MeetingAnalytics, Team, TeamMembership, Channel,
    ChannelMembership, ChannelTab, Organization,
    OrganizationMembership, UserProfile, AuditLog
)
from .serializers import (
    MeetingSerializer, MeetingCreateSerializer, MeetingDetailSerializer,
    MeetingParticipantSerializer, ChatMessageSerializer, ChatMessageCreateSerializer,
    MeetingRecordingSerializer, MeetingReactionSerializer,
    MeetingInvitationSerializer, MeetingAnalyticsSerializer,
    TeamSerializer, TeamDetailSerializer, TeamMembershipSerializer,
    ChannelSerializer, ChannelDetailSerializer, ChannelMembershipSerializer,
    ChannelTabSerializer, OrganizationSerializer,
    OrganizationDetailSerializer, OrganizationMembershipSerializer,
    UserProfileSerializer, AuditLogSerializer, UserRegistrationSerializer
)
from .permissions import (
    IsTeamMember, IsTeamAdmin, IsChannelMember,
    IsOrganizationAdmin, IsOrganizationMember
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@method_decorator(csrf_exempt, name='dispatch')
class MeetingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Meeting CRUD operations
    
    list: Get all meetings (filtered by user)
    create: Create a new meeting
    retrieve: Get meeting details
    update: Update meeting settings
    destroy: Delete meeting
    
    Custom actions:
    - join: Join a meeting
    - start: Start a meeting (host only)
    - end: End a meeting (host only)
    - lock: Lock/unlock meeting (host only)
    """
    permission_classes = [permissions.AllowAny]  # Allow anyone to create meetings for testing
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Filter meetings based on user role and query params"""
        user = self.request.user
        queryset = Meeting.objects.all()

        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by user's meetings (hosted or participated)
        my_meetings = self.request.query_params.get('my_meetings', None)
        if my_meetings:
            queryset = queryset.filter(
                Q(host=user) | Q(participants__user=user)
            ).distinct()

        # Filter by upcoming meetings
        upcoming = self.request.query_params.get('upcoming', None)
        if upcoming:
            queryset = queryset.filter(
                scheduled_start__gte=timezone.now(),
                status='scheduled'
            )

        return queryset.select_related('host').prefetch_related('participants')

    def get_serializer_class(self):
        if self.action == 'create':
            return MeetingCreateSerializer
        elif self.action == 'retrieve':
            return MeetingDetailSerializer
        return MeetingSerializer

    def create(self, request):
        """Create a new meeting"""
        serializer = MeetingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or create user (for anonymous access)
        if request.user.is_authenticated:
            user = request.user
        else:
            # Create/get default user for testing
            user, _ = User.objects.get_or_create(
                username='guest_user',
                defaults={
                    'email': 'guest@truetalk.ai',
                    'first_name': 'Guest',
                    'last_name': 'User'
                }
            )
        
        # Create meeting with user as host
        meeting = serializer.save(host=user)

        # Create host participant
        MeetingParticipant.objects.create(
            meeting=meeting,
            user=user,
            role='host',
            status='admitted'
        )

        # Return detailed response
        response_serializer = MeetingSerializer(meeting)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Get meeting details"""
        meeting = get_object_or_404(Meeting, pk=pk)
        
        # Check if user has access
        is_host = meeting.host == request.user
        is_participant = meeting.participants.filter(user=request.user).exists()
        
        if not (is_host or is_participant):
            return Response(
                {'error': 'You do not have access to this meeting'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MeetingDetailSerializer(meeting)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Join a meeting
        
        Request body:
        {
            "password": "optional_password"
        }
        """
        meeting = get_object_or_404(Meeting, pk=pk)
        user = request.user

        # Check if meeting is locked
        if meeting.is_locked and meeting.host != user:
            return Response(
                {'error': 'Meeting is locked'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check password if required
        if meeting.password_hash:
            password = request.data.get('password')
            if not password or not check_password(password, meeting.password_hash):
                return Response(
                    {'error': 'Invalid password'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        # Check participant limit
        current_participants = meeting.participants.filter(
            status__in=['admitted', 'joined']
        ).count()
        
        if current_participants >= meeting.max_participants:
            return Response(
                {'error': 'Meeting is full'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get or create participant
        participant, created = MeetingParticipant.objects.get_or_create(
            meeting=meeting,
            user=user,
            defaults={
                'role': 'participant',
                'status': 'lobby' if meeting.is_lobby_enabled else 'admitted'
            }
        )

        if not created:
            # Update existing participant
            participant.status = 'lobby' if meeting.is_lobby_enabled else 'admitted'
            participant.save()

        # Generate WebRTC token
        webrtc_token = self._generate_webrtc_token(meeting, user)

        return Response({
            'participant_id': str(participant.id),
            'status': participant.status,
            'role': participant.role,
            'webrtc_token': webrtc_token,
            'meeting': MeetingSerializer(meeting).data
        })

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a meeting (host only)"""
        meeting = get_object_or_404(Meeting, pk=pk)
        
        if meeting.host != request.user:
            return Response(
                {'error': 'Only the host can start the meeting'},
                status=status.HTTP_403_FORBIDDEN
            )

        if meeting.status == 'active':
            return Response({'message': 'Meeting is already active'})

        meeting.start_meeting()

        return Response({
            'message': 'Meeting started',
            'started_at': meeting.started_at
        })

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a meeting (host only)"""
        meeting = get_object_or_404(Meeting, pk=pk)
        
        if meeting.host != request.user:
            return Response(
                {'error': 'Only the host can end the meeting'},
                status=status.HTTP_403_FORBIDDEN
            )

        meeting.end_meeting()

        # Update analytics
        if hasattr(meeting, 'analytics'):
            analytics = meeting.analytics
            analytics.actual_duration_minutes = meeting.duration_minutes
            analytics.save()

        return Response({
            'message': 'Meeting ended',
            'ended_at': meeting.ended_at,
            'duration_minutes': meeting.duration_minutes
        })

    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        """Lock/unlock meeting (host only)"""
        meeting = get_object_or_404(Meeting, pk=pk)
        
        if meeting.host != request.user:
            return Response(
                {'error': 'Only the host can lock the meeting'},
                status=status.HTTP_403_FORBIDDEN
            )

        meeting.is_locked = not meeting.is_locked
        meeting.save()

        return Response({
            'is_locked': meeting.is_locked
        })

    def _generate_webrtc_token(self, meeting, user):
        """Generate WebRTC access token"""
        from django.conf import settings
        
        payload = {
            'meeting_id': str(meeting.id),
            'user_id': str(user.id),
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=4),
            'iat': datetime.utcnow()
        }
        
        secret_key = getattr(settings, 'SECRET_KEY', 'your-secret-key')
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token


class ParticipantViewSet(viewsets.ViewSet):
    """
    ViewSet for Participant Management
    
    list: Get all participants in a meeting
    
    Custom actions:
    - admit: Admit participant from lobby
    - remove: Remove participant from meeting
    - mute: Mute participant
    - mute_all: Mute all participants
    - make_cohost: Make participant a co-host
    - raise_hand: Raise/lower hand
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, meeting_pk=None):
        """List all participants in a meeting"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        participants = meeting.participants.select_related('user').all()

        serializer = MeetingParticipantSerializer(participants, many=True)
        return Response({'participants': serializer.data})

    @action(detail=True, methods=['post'])
    def admit(self, request, meeting_pk=None, pk=None):
        """Admit participant from lobby (host/co-host only)"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        participant = get_object_or_404(MeetingParticipant, pk=pk, meeting=meeting)

        # Check if requester is host or co-host
        requester_participant = meeting.participants.filter(user=request.user).first()
        if not requester_participant or requester_participant.role not in ['host', 'co_host']:
            return Response(
                {'error': 'Only host or co-host can admit participants'},
                status=status.HTTP_403_FORBIDDEN
            )

        participant.status = 'admitted'
        participant.save()

        return Response({'message': 'Participant admitted'})

    @action(detail=True, methods=['post'])
    def remove(self, request, meeting_pk=None, pk=None):
        """Remove participant from meeting (host/co-host only)"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        participant = get_object_or_404(MeetingParticipant, pk=pk, meeting=meeting)

        # Check if requester is host or co-host
        requester_participant = meeting.participants.filter(user=request.user).first()
        if not requester_participant or requester_participant.role not in ['host', 'co_host']:
            return Response(
                {'error': 'Only host or co-host can remove participants'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Cannot remove host
        if participant.role == 'host':
            return Response(
                {'error': 'Cannot remove the host'},
                status=status.HTTP_403_FORBIDDEN
            )

        participant.status = 'removed'
        participant.left_at = timezone.now()
        participant.save()

        return Response({'message': 'Participant removed'})

    @action(detail=True, methods=['post'])
    def mute(self, request, meeting_pk=None, pk=None):
        """Mute participant (host/co-host only)"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        participant = get_object_or_404(MeetingParticipant, pk=pk, meeting=meeting)

        # Check if requester is host or co-host
        requester_participant = meeting.participants.filter(user=request.user).first()
        if not requester_participant or requester_participant.role not in ['host', 'co_host']:
            return Response(
                {'error': 'Only host or co-host can mute participants'},
                status=status.HTTP_403_FORBIDDEN
            )

        participant.is_audio_muted = True
        participant.save()

        return Response({'message': 'Participant muted'})

    @action(detail=False, methods=['post'])
    def mute_all(self, request, meeting_pk=None):
        """Mute all participants (host/co-host only)"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)

        # Check if requester is host or co-host
        requester_participant = meeting.participants.filter(user=request.user).first()
        if not requester_participant or requester_participant.role not in ['host', 'co_host']:
            return Response(
                {'error': 'Only host or co-host can mute all participants'},
                status=status.HTTP_403_FORBIDDEN
            )

        meeting.participants.exclude(role='host').update(is_audio_muted=True)

        return Response({'message': 'All participants muted'})

    @action(detail=True, methods=['post'])
    def make_cohost(self, request, meeting_pk=None, pk=None):
        """Make participant a co-host (host only)"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        participant = get_object_or_404(MeetingParticipant, pk=pk, meeting=meeting)

        # Check if requester is host
        if meeting.host != request.user:
            return Response(
                {'error': 'Only the host can make co-hosts'},
                status=status.HTTP_403_FORBIDDEN
            )

        participant.role = 'co_host'
        participant.save()

        return Response({'message': 'Participant is now a co-host'})

    @action(detail=True, methods=['post'])
    def raise_hand(self, request, meeting_pk=None, pk=None):
        """Raise/lower hand"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        participant = get_object_or_404(
            MeetingParticipant,
            pk=pk,
            meeting=meeting,
            user=request.user
        )

        is_raised = request.data.get('is_raised', True)
        
        if is_raised:
            participant.raise_hand()
        else:
            participant.lower_hand()

        return Response({
            'is_hand_raised': participant.is_hand_raised,
            'hand_raised_at': participant.hand_raised_at
        })


class ChatViewSet(viewsets.ViewSet):
    """
    ViewSet for Chat Messages
    
    list: Get chat messages for a meeting
    create: Send a chat message
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def list(self, request, meeting_pk=None):
        """List chat messages"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        
        # Check if user is participant
        if not meeting.participants.filter(user=request.user).exists():
            return Response(
                {'error': 'You are not a participant in this meeting'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = meeting.chat_messages.filter(
            deleted_at__isnull=True
        ).select_related('sender', 'recipient').order_by('created_at')

        # Filter private messages
        messages = messages.filter(
            Q(is_private=False) |
            Q(sender=request.user) |
            Q(recipient=request.user)
        )

        serializer = ChatMessageSerializer(messages, many=True)
        return Response({'messages': serializer.data})

    def create(self, request, meeting_pk=None):
        """Send a chat message"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        
        if not meeting.is_chat_enabled:
            return Response(
                {'error': 'Chat is disabled for this meeting'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if user is participant
        if not meeting.participants.filter(user=request.user).exists():
            return Response(
                {'error': 'You are not a participant in this meeting'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create message
        message = serializer.save(
            meeting=meeting,
            sender=request.user
        )

        # Update analytics
        if hasattr(meeting, 'analytics'):
            analytics = meeting.analytics
            analytics.total_messages += 1
            analytics.save()

        response_serializer = ChatMessageSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class RecordingViewSet(viewsets.ViewSet):
    """
    ViewSet for Meeting Recordings
    
    list: Get recordings for a meeting
    
    Custom actions:
    - start: Start recording
    - stop: Stop recording
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, meeting_pk=None):
        """List recordings for a meeting"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        
        # Check if user has access
        if meeting.host != request.user:
            participant = meeting.participants.filter(user=request.user).first()
            if not participant:
                return Response(
                    {'error': 'You do not have access to this meeting'},
                    status=status.HTTP_403_FORBIDDEN
                )

        recordings = meeting.recordings.all()
        serializer = MeetingRecordingSerializer(recordings, many=True)
        return Response({'recordings': serializer.data})

    @action(detail=False, methods=['post'])
    def start(self, request, meeting_pk=None):
        """Start recording (host/co-host only)"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        
        # Check permissions
        participant = meeting.participants.filter(user=request.user).first()
        if not participant or participant.role not in ['host', 'co_host']:
            return Response(
                {'error': 'Only host or co-host can start recording'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not meeting.is_recording_enabled:
            return Response(
                {'error': 'Recording is not enabled for this meeting'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create recording
        recording = MeetingRecording.objects.create(
            meeting=meeting,
            started_by=request.user,
            started_at=timezone.now(),
            file_url='',  # Will be updated when recording is processed
            status='recording'
        )

        serializer = MeetingRecordingSerializer(recording)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def stop(self, request, meeting_pk=None, pk=None):
        """Stop recording"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        recording = get_object_or_404(MeetingRecording, pk=pk, meeting=meeting)

        # Check permissions
        participant = meeting.participants.filter(user=request.user).first()
        if not participant or participant.role not in ['host', 'co_host']:
            return Response(
                {'error': 'Only host or co-host can stop recording'},
                status=status.HTTP_403_FORBIDDEN
            )

        recording.ended_at = timezone.now()
        recording.status = 'processing'
        recording.save()

        # Calculate duration
        if recording.started_at and recording.ended_at:
            delta = recording.ended_at - recording.started_at
            recording.duration_seconds = int(delta.total_seconds())
            recording.save()

        serializer = MeetingRecordingSerializer(recording)
        return Response(serializer.data)


class ReactionViewSet(viewsets.ViewSet):
    """
    ViewSet for Meeting Reactions
    
    create: Send a reaction
    """
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, meeting_pk=None):
        """Send a reaction"""
        meeting = get_object_or_404(Meeting, pk=meeting_pk)
        
        # Check if user is participant
        if not meeting.participants.filter(user=request.user).exists():
            return Response(
                {'error': 'You are not a participant in this meeting'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MeetingReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reaction = serializer.save(
            meeting=meeting,
            user=request.user
        )

        # Update analytics
        if hasattr(meeting, 'analytics'):
            analytics = meeting.analytics
            analytics.total_reactions += 1
            analytics.save()

        response_serializer = MeetingReactionSerializer(reaction)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# Simplified Meeting Endpoints (No Auth Required)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def create_meeting_simple(request):
    """Create a new meeting - simplified version"""
    title = request.data.get('title', 'Untitled Meeting')
    
    # Get or create a default user
    user, _ = User.objects.get_or_create(
        username='default_user',
        defaults={'email': 'default@example.com', 'password': 'unused'}
    )
    
    meeting = Meeting.objects.create(
        title=title,
        host=user,
        max_participants=300,
        duration_limit_minutes=180,
        is_lobby_enabled=False
    )
    
    return Response({
        'meeting_id': str(meeting.id),
        'join_url': f'/meeting/room/{meeting.id}/',
        'title': meeting.title
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def join_meeting_simple(request, meeting_id):
    """Join a meeting - simplified version"""
    try:
        meeting = Meeting.objects.get(id=meeting_id)
    except Meeting.DoesNotExist:
        return Response({'error': 'Meeting not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if meeting is full
    active_participants = meeting.participants.filter(left_at__isnull=True).count()
    if active_participants >= meeting.max_participants:
        return Response({'error': 'Meeting is full'}, status=status.HTTP_403_FORBIDDEN)
    
    name = request.data.get('name', 'Guest')
    client_id = request.data.get('client_id')
    
    if not client_id:
        return Response({'error': 'client_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create default user
    user, _ = User.objects.get_or_create(
        username='default_user',
        defaults={'email': 'default@example.com', 'password': 'unused'}
    )
    
    # Create participant
    participant = MeetingParticipant.objects.create(
        meeting=meeting,
        user=user,
        peer_id=client_id,
        role='participant',
        status='admitted'
    )
    
    # Start meeting if first participant
    if active_participants == 0 and meeting.status != 'active':
        meeting.start_meeting()
    
    return Response({
        'participant_id': str(participant.id),
        'meeting_id': str(meeting.id),
        'name': name
    }, status=status.HTTP_201_CREATED)


class TeamViewSet(viewsets.ModelViewSet):
    """
    Team ViewSet
    CRUD operations for teams
    """
    
    queryset = Team.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['organization', 'privacy', 'is_archived']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TeamDetailSerializer
        return TeamSerializer
    
    def get_queryset(self):
        """Filter teams where user is a member"""
        user = self.request.user
        return Team.objects.filter(
            memberships__user=user,
            memberships__is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Create team and add creator as owner"""
        team = serializer.save(created_by=self.request.user)
        
        # Add creator as owner
        TeamMembership.objects.create(
            team=team,
            user=self.request.user,
            role='owner'
        )
        
        # Create default "General" channel
        general_channel = Channel.objects.create(
            team=team,
            name='General',
            description='General discussion',
            channel_type='standard',
            is_general=True,
            created_by=self.request.user
        )
        
        # Add creator to general channel
        ChannelMembership.objects.create(
            channel=general_channel,
            user=self.request.user,
            role='owner'
        )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List team members"""
        team = self.get_object()
        memberships = team.memberships.filter(is_active=True)
        serializer = TeamMembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTeamAdmin])
    def add_member(self, request, pk=None):
        """Add member to team"""
        team = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists and is in same organization
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            
            # Verify user is in same organization
            if not OrganizationMembership.objects.filter(
                organization=team.organization,
                user=user,
                is_active=True
            ).exists():
                return Response(
                    {'error': 'User is not a member of this organization'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already a member
        if TeamMembership.objects.filter(
            team=team,
            user=user,
            is_active=True
        ).exists():
            return Response(
                {'error': 'User is already a team member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create membership
        membership = TeamMembership.objects.create(
            team=team,
            user=user,
            role=role,
            invited_by=request.user
        )
        
        # Add to all public channels
        public_channels = team.channels.filter(channel_type='standard', is_archived=False)
        for channel in public_channels:
            ChannelMembership.objects.get_or_create(
                channel=channel,
                user=user,
                defaults={'role': 'member'}
            )
        
        serializer = TeamMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated, IsTeamAdmin])
    def remove_member(self, request, pk=None):
        """Remove member from team"""
        team = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        membership = get_object_or_404(
            TeamMembership,
            team=team,
            user_id=user_id,
            is_active=True
        )
        
        # Prevent removing the last owner
        if membership.role == 'owner':
            owner_count = TeamMembership.objects.filter(
                team=team,
                role='owner',
                is_active=True
            ).count()
            if owner_count <= 1:
                return Response(
                    {'error': 'Cannot remove the last owner'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        membership.is_active = False
        membership.save()
        
        # Remove from all channels
        ChannelMembership.objects.filter(
            channel__team=team,
            user_id=user_id
        ).update(is_active=False)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def channels(self, request, pk=None):
        """List team channels"""
        team = self.get_object()
        channels = team.channels.filter(is_archived=False)
        
        # Filter private channels (only show if user is member)
        user_channel_ids = ChannelMembership.objects.filter(
            user=request.user,
            is_active=True
        ).values_list('channel_id', flat=True)
        
        channels = channels.filter(
            models.Q(channel_type='standard') | models.Q(id__in=user_channel_ids)
        )
        
        serializer = ChannelSerializer(channels, many=True)
        return Response(serializer.data)


class ChannelViewSet(viewsets.ModelViewSet):
    """
    Channel ViewSet
    CRUD operations for channels
    """
    
    queryset = Channel.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['team', 'channel_type', 'is_archived']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ChannelDetailSerializer
        return ChannelSerializer
    
    def get_queryset(self):
        """Filter channels where user is a member"""
        user = self.request.user
        return Channel.objects.filter(
            memberships__user=user,
            memberships__is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Create channel and add creator as owner"""
        channel = serializer.save(created_by=self.request.user)
        
        # Add creator as owner
        ChannelMembership.objects.create(
            channel=channel,
            user=self.request.user,
            role='owner'
        )
        
        # If standard channel, add all team members
        if channel.channel_type == 'standard':
            team_members = TeamMembership.objects.filter(
                team=channel.team,
                is_active=True
            ).exclude(user=self.request.user)
            
            for membership in team_members:
                ChannelMembership.objects.create(
                    channel=channel,
                    user=membership.user,
                    role='member'
                )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List channel members"""
        channel = self.get_object()
        memberships = channel.memberships.filter(is_active=True)
        serializer = ChannelMembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add member to channel"""
        channel = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is team member
        from django.contrib.auth.models import User
        user = get_object_or_404(User, id=user_id)
        
        if not TeamMembership.objects.filter(
            team=channel.team,
            user=user,
            is_active=True
        ).exists():
            return Response(
                {'error': 'User is not a team member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create channel membership
        membership, created = ChannelMembership.objects.get_or_create(
            channel=channel,
            user=user,
            defaults={'role': 'member'}
        )
        
        if not created:
            membership.is_active = True
            membership.save()
        
        serializer = ChannelMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark channel as read"""
        channel = self.get_object()
        membership = get_object_or_404(
            ChannelMembership,
            channel=channel,
            user=request.user,
            is_active=True
        )
        
        membership.mark_as_read()
        serializer = ChannelMembershipSerializer(membership)
        return Response(serializer.data)


class ChannelTabViewSet(viewsets.ModelViewSet):
    """
    Channel Tab ViewSet
    """
    
    queryset = ChannelTab.objects.all()
    serializer_class = ChannelTabSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter tabs for channels user has access to"""
        user = self.request.user
        channel_ids = ChannelMembership.objects.filter(
            user=user,
            is_active=True
        ).values_list('channel_id', flat=True)
        
        return ChannelTab.objects.filter(channel_id__in=channel_ids)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    Organization ViewSet
    CRUD operations for organizations
    """
    
    queryset = Organization.objects.all()
    # permission_classes = [permissions.IsAuthenticated] # Already imported permissions
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrganizationDetailSerializer
        return OrganizationSerializer
    
    def get_queryset(self):
        """Filter organizations where user is a member"""
        user = self.request.user
        return Organization.objects.filter(
            memberships__user=user,
            memberships__is_active=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Create organization and add creator as owner"""
        organization = serializer.save()
        OrganizationMembership.objects.create(
            organization=organization,
            user=self.request.user,
            role='owner'
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=self.request.user,
            organization=organization,
            action='org.created',
            resource_type='organization',
            resource_id=str(organization.id),
            details={'name': organization.name}
        )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List organization members"""
        organization = self.get_object()
        memberships = organization.memberships.filter(is_active=True)
        serializer = OrganizationMembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsOrganizationAdmin])
    def add_member(self, request, pk=None):
        """Add member to organization"""
        organization = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already a member
        if OrganizationMembership.objects.filter(
            organization=organization,
            user=user,
            is_active=True
        ).exists():
            return Response(
                {'error': 'User is already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check member limit
        if organization.member_count >= organization.max_members:
            return Response(
                {'error': 'Organization has reached maximum member limit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=user,
            role=role,
            invited_by=request.user
        )
        
        serializer = OrganizationMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsOrganizationAdmin])
    def remove_member(self, request, pk=None):
        """Remove member from organization"""
        organization = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        membership = get_object_or_404(
            OrganizationMembership,
            organization=organization,
            user_id=user_id,
            is_active=True
        )
        
        # Prevent removing the last owner
        if membership.role == 'owner':
            owner_count = OrganizationMembership.objects.filter(
                organization=organization,
                role='owner',
                is_active=True
            ).count()
            if owner_count <= 1:
                return Response(
                    {'error': 'Cannot remove the last owner'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        membership.is_active = False
        membership.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    User Profile ViewSet
    """
    
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see profiles in their organizations"""
        user = self.request.user
        # Get all users in same organizations
        org_ids = OrganizationMembership.objects.filter(
            user=user,
            is_active=True
        ).values_list('organization_id', flat=True)
        
        user_ids = OrganizationMembership.objects.filter(
            organization_id__in=org_ids,
            is_active=True
        ).values_list('user_id', flat=True)
        
        return UserProfile.objects.filter(user_id__in=user_ids)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_status(self, request):
        """Update user status"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        status_value = request.data.get('status')
        status_message = request.data.get('status_message', '')
        
        if status_value:
            profile.status = status_value
        profile.status_message = status_message
        profile.save()
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit Log ViewSet (Read-only)
    """
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]
    
    def get_queryset(self):
        """Filter audit logs by organization"""
        user = self.request.user
        org_id = self.request.query_params.get('organization_id')
        
        if org_id:
            # Check if user is admin of this organization
            membership = OrganizationMembership.objects.filter(
                organization_id=org_id,
                user=user,
                is_active=True
            ).first()
            
            if membership and membership.is_admin():
                return AuditLog.objects.filter(organization_id=org_id)
        
        return AuditLog.objects.none()


class RegisterView(APIView):
    """
    User Registration View
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'User registered successfully',
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    """
    Get current authenticated user
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        profile_serializer = UserProfileSerializer(request.user.profile)
        
        return Response({
            'user': serializer.data,
            'profile': profile_serializer.data
        })
