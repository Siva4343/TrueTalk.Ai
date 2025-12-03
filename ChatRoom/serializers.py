from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatRoom, Message, MessageReaction, UserStatus, ArchivedChat
from app.serializers import UserWithProfileSerializer
import base64
from django.core.files.base import ContentFile

class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserWithProfileSerializer(many=True, read_only=True)
    created_by = UserWithProfileSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    is_archived = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = '__all__'
    
    def get_last_message(self, obj):
        last_msg = obj.messages.filter(is_deleted=False).last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_deleted=False).exclude(read_by=request.user).count()
        return 0
    
    def get_is_archived(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ArchivedChat.objects.filter(user=request.user, room=obj).exists()
        return False

class MessageSerializer(serializers.ModelSerializer):
    sender = UserWithProfileSerializer(read_only=True)
    reactions = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    is_forwarded = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['sender', 'created_at', 'updated_at', 'read_by']
    
    def get_reactions(self, obj):
        return MessageReactionSerializer(obj.message_reactions.all(), many=True).data
    
    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.read_by.filter(id=request.user.id).exists()
        return False
    
    def create(self, validated_data):
        # Handle base64 file uploads
        file_data = validated_data.pop('file_data', None)
        voice_data = validated_data.pop('voice_data', None)
        
        if file_data and validated_data.get('message_type') in ['image', 'file']:
            format, file_str = file_data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f"file_{validated_data['sender'].id}_{uuid.uuid4()}.{ext}"
            data = ContentFile(base64.b64decode(file_str), name=file_name)
            validated_data['file'] = data
        
        if voice_data and validated_data.get('message_type') == 'voice':
            format, voice_str = voice_data.split(';base64,')
            file_name = f"voice_{validated_data['sender'].id}_{uuid.uuid4()}.mp3"
            data = ContentFile(base64.b64decode(voice_str), name=file_name)
            validated_data['voice_note'] = data
        
        return super().create(validated_data)

class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserWithProfileSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = '__all__'

class UserStatusSerializer(serializers.ModelSerializer):
    user = UserWithProfileSerializer(read_only=True)
    
    class Meta:
        model = UserStatus
        fields = '__all__'