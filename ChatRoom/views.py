from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User
from .models import ChatRoom, Message, MessageReaction, ArchivedChat, ChatBackup, UserStatus
from .serializers import ChatRoomSerializer, MessageSerializer, MessageReactionSerializer
from django.db.models import Q
import json
from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os
from datetime import datetime

class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()   # ✔ required for DRF router
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(participants=user).prefetch_related('participants')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['post'])
    def create_direct_chat(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if direct chat already exists
        existing_chat = ChatRoom.objects.filter(
            room_type='direct',
            participants=request.user
        ).filter(participants=other_user).distinct()
        
        if existing_chat.exists():
            return Response(ChatRoomSerializer(existing_chat.first(), context={'request': request}).data)
        
        # Create new direct chat
        chat = ChatRoom.objects.create(
            name=f"{request.user.username} - {other_user.username}",
            room_type='direct',
            created_by=request.user
        )
        chat.participants.add(request.user, other_user)
        
        return Response(ChatRoomSerializer(chat, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        chat = self.get_object()
        ArchivedChat.objects.get_or_create(user=request.user, room=chat)
        return Response({'message': 'Chat archived successfully'})
    
    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        chat = self.get_object()
        ArchivedChat.objects.filter(user=request.user, room=chat).delete()
        return Response({'message': 'Chat unarchived successfully'})

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        return Message.objects.filter(room_id=room_id, is_deleted=False).select_related('sender')
    
    def perform_create(self, serializer):
        room_id = self.kwargs.get('room_id')
        room = ChatRoom.objects.get(id=room_id)
        serializer.save(sender=self.request.user, room=room)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, room_id=None, pk=None):
        message = self.get_object()
        message.read_by.add(request.user)
        return Response({'message': 'Message marked as read'})
    
    @action(detail=True, methods=['post'])
    def react(self, request, room_id=None, pk=None):
        message = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response({'error': 'Emoji is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        reaction, created = MessageReaction.objects.update_or_create(
            message=message,
            user=request.user,
            defaults={'emoji': emoji}
        )
        
        return Response(MessageReactionSerializer(reaction).data)
    
    @action(detail=True, methods=['post'])
    def delete_for_me(self, request, room_id=None, pk=None):
        message = self.get_object()
        message.is_deleted = True
        message.save()
        return Response({'message': 'Message deleted for you'})
    
    @action(detail=True, methods=['post'])
    def delete_for_everyone(self, request, room_id=None, pk=None):
        message = self.get_object()
        if message.sender == request.user:
            message.deleted_for_all = True
            message.is_deleted = True
            message.deleted_by = request.user
            message.save()
            return Response({'message': 'Message deleted for everyone'})
        return Response({'error': 'You can only delete your own messages for everyone'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'])
    def forward(self, request, room_id=None, pk=None):
        message = self.get_object()
        target_room_ids = request.data.get('room_ids', [])
        
        forwarded_messages = []
        for target_room_id in target_room_ids:
            try:
                target_room = ChatRoom.objects.get(id=target_room_id, participants=request.user)
                forwarded_msg = Message.objects.create(
                    room=target_room,
                    sender=request.user,
                    message_type=message.message_type,
                    content=f"Forwarded: {message.content}",
                    file=message.file,
                    voice_note=message.voice_note,
                    is_forwarded=True,
                    original_sender=message.sender
                )
                forwarded_messages.append(forwarded_msg)
            except ChatRoom.DoesNotExist:
                continue
        
        return Response(MessageSerializer(forwarded_messages, many=True).data)

class SearchView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        
        # Search in messages
        messages = Message.objects.filter(
            Q(content__icontains=query) | 
            Q(sender__username__icontains=query),
            room__participants=request.user,
            is_deleted=False
        ).select_related('sender', 'room')[:50]
        
        # Search in users
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(business_profile__business_name__icontains=query)
        ).exclude(id=request.user.id)[:20]
        
        return Response({
            'messages': MessageSerializer(messages, many=True).data,
            'users': UserWithProfileSerializer(users, many=True).data
        })

class BackupChatsView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        format = request.data.get('format', 'pdf')
        email = request.data.get('email', request.user.email)
        
        # Create PDF backup
        if format == 'pdf':
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            title = Paragraph(f"Chat Backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Get all user's chats
            chats = ChatRoom.objects.filter(participants=request.user)
            
            for chat in chats:
                chat_title = Paragraph(f"Chat: {chat.name}", styles['Heading2'])
                story.append(chat_title)
                
                messages = chat.messages.filter(is_deleted=False).order_by('created_at')
                for message in messages:
                    msg_text = f"{message.sender.username} ({message.created_at}): {message.content}"
                    story.append(Paragraph(msg_text, styles['Normal']))
                    story.append(Spacer(1, 6))
                
                story.append(Spacer(1, 12))
            
            doc.build(story)
            
            # Send email
            email_msg = EmailMessage(
                'Your Chat Backup',
                'Please find attached your chat backup.',
                settings.EMAIL_HOST_USER,
                [email]
            )
            email_msg.attach(f'chat_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf', 
                           buffer.getvalue(), 'application/pdf')
            email_msg.send()
            
            # Save backup record
            ChatBackup.objects.create(
                user=request.user,
                backup_file=f'backups/backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                status='completed'
            )
            
            return Response({'message': 'Backup sent to email'})
        
        return Response({'error': 'Invalid format'}, status=status.HTTP_400_BAD_REQUEST)