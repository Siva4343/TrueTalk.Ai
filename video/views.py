from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
import uuid
from .models import CallSession, CallLog
from .serializers import CallSessionSerializer, CallLogSerializer, CallInitiateSerializer


class CallSessionViewSet(viewsets.ModelViewSet):
    queryset = CallSession.objects.all()
    serializer_class = CallSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CallSession.objects.filter(caller=user) | CallSession.objects.filter(receiver=user)

    @action(detail=False, methods=['post'])
    def initiate_call(self, request):
        serializer = CallInitiateSerializer(data=request.data)
        if serializer.is_valid():
            receiver_id = serializer.validated_data['receiver_id']
            call_type = serializer.validated_data['call_type']
            room_name = serializer.validated_data.get('room_name', f"room_{uuid.uuid4().hex}")
            
            try:
                receiver = User.objects.get(id=receiver_id)
                
                # Create call session
                call_session = CallSession.objects.create(
                    call_id=f"call_{uuid.uuid4().hex}",
                    caller=request.user,
                    receiver=receiver,
                    call_type=call_type,
                    room_name=room_name,
                    status='initiated'
                )
                
                # Log action
                CallLog.objects.create(
                    call_session=call_session,
                    user=request.user,
                    action='initiated'
                )
                
                return Response({
                    'message': 'Call initiated successfully',
                    'call_session': CallSessionSerializer(call_session).data,
                    'room_name': room_name
                }, status=status.HTTP_201_CREATED)
                
            except User.DoesNotExist:
                return Response({'error': 'Receiver not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def accept_call(self, request, pk=None):
        call_session = self.get_object()
        
        if call_session.receiver != request.user:
            return Response({'error': 'Not authorized to accept this call'},
                            status=status.HTTP_403_FORBIDDEN)
        
        call_session.status = 'ongoing'
        call_session.save()
        
        CallLog.objects.create(call_session=call_session, user=request.user, action='accepted')
        
        return Response({'message': 'Call accepted', 'room_name': call_session.room_name})

    @action(detail=True, methods=['post'])
    def end_call(self, request, pk=None):
        call_session = self.get_object()
        
        if call_session.caller != request.user and call_session.receiver != request.user:
            return Response({'error': 'Not authorized to end this call'},
                            status=status.HTTP_403_FORBIDDEN)
        
        call_session.status = 'ended'
        call_session.save()
        
        CallLog.objects.create(call_session=call_session, user=request.user, action='ended')
        
        return Response({'message': 'Call ended'})

    @action(detail=True, methods=['post'])
    def reject_call(self, request, pk=None):
        call_session = self.get_object()
        
        if call_session.receiver != request.user:
            return Response({'error': 'Not authorized to reject this call'},
                            status=status.HTTP_403_FORBIDDEN)
        
        call_session.status = 'missed'
        call_session.save()
        
        CallLog.objects.create(call_session=call_session, user=request.user, action='rejected')
        
        return Response({'message': 'Call rejected'})


class CallLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CallLog.objects.all()  # Required for DRF
    serializer_class = CallLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CallLog.objects.filter(user=self.request.user)
