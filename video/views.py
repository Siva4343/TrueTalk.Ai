from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
import uuid
import logging

from .models import CallSession, CallLog
from .serializers import (
    CallSessionListSerializer, 
    CallSessionDetailSerializer,
    CallLogSerializer, 
    CallInitiateSerializer,
    CallActionSerializer,
    UserSerializer
)
from .permissions import IsCallParticipant, IsCallReceiver, CanEndCall

logger = logging.getLogger(__name__)


class CallSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing call sessions
    
    Provides endpoints for:
    - Listing call sessions (GET /call-sessions/)
    - Retrieving call details (GET /call-sessions/{id}/)
    - Initiating calls (POST /call-sessions/initiate_call/)
    - Accepting calls (POST /call-sessions/{id}/accept_call/)
    - Rejecting calls (POST /call-sessions/{id}/reject_call/)
    - Ending calls (POST /call-sessions/{id}/end_call/)
    - Getting active calls (GET /call-sessions/active_calls/)
    - Getting call history (GET /call-sessions/call_history/)
    """
    permission_classes = [AllowAny]  # Override in production to IsAuthenticated
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['call_type', 'status', 'caller', 'receiver']
    search_fields = ['call_id', 'room_name']
    ordering_fields = ['created_at', 'started_at', 'ended_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset to only include calls user is involved in"""
        user = self.request.user
        if not user.is_authenticated:
            return CallSession.objects.none()
        
        return CallSession.objects.filter(
            Q(caller=user) | Q(receiver=user)
        ).select_related('caller', 'receiver').prefetch_related('logs')
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return CallSessionListSerializer
        return CallSessionDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['accept_call', 'reject_call']:
            return [IsAuthenticated(), IsCallReceiver()]
        elif self.action == 'end_call':
            return [IsAuthenticated(), CanEndCall()]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return [IsAuthenticated(), IsCallParticipant()]
        return [AllowAny()]
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def initiate_call(self, request):
        """
        Initiate a new call
        
        Request body:
        {
            "receiver_id": 2,
            "call_type": "video",  // or "audio"
            "room_name": "optional_custom_room"  // optional
        }
        """
        serializer = CallInitiateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            receiver = User.objects.get(id=serializer.validated_data['receiver_id'])
        except User.DoesNotExist:
            return Response(
                {'error': 'Receiver not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if there's already an active call between these users
        active_call = CallSession.objects.filter(
            Q(caller=request.user, receiver=receiver) | 
            Q(caller=receiver, receiver=request.user),
            status__in=['initiated', 'ongoing']
        ).first()
        
        if active_call:
            return Response(
                {
                    'error': 'There is already an active call between you and this user',
                    'call_session': CallSessionDetailSerializer(active_call).data
                },
                status=status.HTTP_409_CONFLICT
            )
        
        # Create new call session
        call_session = CallSession.objects.create(
            call_id=f"call_{uuid.uuid4().hex}",
            caller=request.user,
            receiver=receiver,
            call_type=serializer.validated_data['call_type'],
            room_name=serializer.validated_data['room_name'],
            status='initiated'
        )
        
        # Log the action
        CallLog.objects.create(
            call_session=call_session,
            user=request.user,
            action='initiated'
        )
        
        logger.info(f"Call initiated: {call_session.call_id} from {request.user.username} to {receiver.username}")
        
        return Response(
            {
                'message': 'Call initiated successfully',
                'call_session': CallSessionDetailSerializer(call_session).data,
                'room_name': call_session.room_name,
                'websocket_url': f"ws://localhost:8000/ws/call/{call_session.room_name}/"
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsCallReceiver])
    def accept_call(self, request, pk=None):
        """
        Accept an incoming call
        Only the receiver can accept a call
        """
        call_session = self.get_object()
        
        # Validate call can be accepted
        if call_session.status != 'initiated':
            return Response(
                {
                    'error': f'Cannot accept call with status: {call_session.status}',
                    'current_status': call_session.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update call status
        call_session.status = 'ongoing'
        call_session.started_at = timezone.now()
        call_session.save()
        
        # Log the action
        CallLog.objects.create(
            call_session=call_session,
            user=request.user,
            action='accepted'
        )
        
        logger.info(f"Call accepted: {call_session.call_id} by {request.user.username}")
        
        return Response(
            {
                'message': 'Call accepted successfully',
                'call_session': CallSessionDetailSerializer(call_session).data,
                'room_name': call_session.room_name,
                'websocket_url': f"ws://localhost:8000/ws/call/{call_session.room_name}/"
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsCallReceiver])
    def reject_call(self, request, pk=None):
        """
        Reject an incoming call
        Only the receiver can reject a call
        """
        call_session = self.get_object()
        
        # Validate call can be rejected
        if call_session.status != 'initiated':
            return Response(
                {
                    'error': f'Cannot reject call with status: {call_session.status}',
                    'current_status': call_session.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional reason from request
        action_serializer = CallActionSerializer(data=request.data)
        action_serializer.is_valid()  # Don't fail if no reason provided
        
        # Update call status
        call_session.status = 'missed'
        call_session.ended_at = timezone.now()
        call_session.save()
        
        # Log the action
        CallLog.objects.create(
            call_session=call_session,
            user=request.user,
            action='rejected'
        )
        
        logger.info(f"Call rejected: {call_session.call_id} by {request.user.username}")
        
        return Response(
            {
                'message': 'Call rejected successfully',
                'call_session': CallSessionDetailSerializer(call_session).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanEndCall])
    def end_call(self, request, pk=None):
        """
        End an active call
        Both caller and receiver can end a call
        """
        call_session = self.get_object()
        
        # Validate call can be ended
        if call_session.status not in ['initiated', 'ongoing']:
            return Response(
                {
                    'error': f'Cannot end call with status: {call_session.status}',
                    'current_status': call_session.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional reason from request
        action_serializer = CallActionSerializer(data=request.data)
        action_serializer.is_valid()
        
        # Update call status
        call_session.status = 'ended'
        call_session.ended_at = timezone.now()
        
        # Set started_at if call was ended before it was answered
        if not call_session.started_at:
            call_session.started_at = call_session.created_at
        
        call_session.save()
        
        # Log the action
        CallLog.objects.create(
            call_session=call_session,
            user=request.user,
            action='ended'
        )
        
        logger.info(f"Call ended: {call_session.call_id} by {request.user.username}")
        
        return Response(
            {
                'message': 'Call ended successfully',
                'call_session': CallSessionDetailSerializer(call_session).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def active_calls(self, request):
        """Get all active calls for the current user"""
        active_calls = self.get_queryset().filter(
            status__in=['initiated', 'ongoing']
        )
        
        serializer = CallSessionListSerializer(active_calls, many=True)
        
        return Response(
            {
                'count': active_calls.count(),
                'results': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def call_history(self, request):
        """Get call history for the current user"""
        # Get query parameters
        call_type = request.query_params.get('call_type', None)
        limit = int(request.query_params.get('limit', 50))
        
        # Base queryset
        history = self.get_queryset().filter(
            status__in=['ended', 'missed']
        )
        
        # Filter by call type if provided
        if call_type in ['audio', 'video']:
            history = history.filter(call_type=call_type)
        
        # Limit results
        history = history[:limit]
        
        serializer = CallSessionListSerializer(history, many=True)
        
        return Response(
            {
                'count': history.count(),
                'results': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsCallParticipant])
    def logs(self, request, pk=None):
        """Get all logs for a specific call session"""
        call_session = self.get_object()
        logs = call_session.logs.all().order_by('timestamp')
        
        serializer = CallLogSerializer(logs, many=True)
        
        return Response(
            {
                'call_id': call_session.call_id,
                'count': logs.count(),
                'logs': serializer.data
            },
            status=status.HTTP_200_OK
        )


class CallLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing call logs
    Read-only access to call logs for the authenticated user
    """
    serializer_class = CallLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'call_session']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Return logs for calls the user participated in"""
        user = self.request.user
        
        # Get all call sessions user participated in
        user_calls = CallSession.objects.filter(
            Q(caller=user) | Q(receiver=user)
        ).values_list('id', flat=True)
        
        # Return logs for those calls
        return CallLog.objects.filter(
            call_session__id__in=user_calls
        ).select_related('call_session', 'user')


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing users
    Provides a simple endpoint to search and list users
    """
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user information"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
