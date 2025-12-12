"""
Django REST Framework Serializers for Video Meeting System
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Meeting, MeetingParticipant, ChatMessage,
    MeetingRecording, MeetingReaction, MeetingInvitation,
    MeetingAnalytics, Team, TeamMembership, Channel,
    ChannelMembership, ChannelTab, Organization, OrganizationMembership,
    UserProfile, AuditLog
)


class UserSerializer(serializers.ModelSerializer):
    """User Serializer"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """User Profile Serializer"""
    
    user = UserSerializer(read_only=True)
    is_online = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'avatar_url', 'bio', 'phone_number',
            'timezone', 'location', 'status', 'status_message',
            'preferences', 'last_seen', 'is_online',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'last_seen', 'created_at', 'updated_at']


class OrganizationSerializer(serializers.ModelSerializer):
    """Organization Serializer"""
    
    member_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description', 'logo_url', 'website',
            'subscription_tier', 'max_members', 'max_teams',
            'is_active', 'features', 'member_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'member_count']


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Organization Membership Serializer"""
    
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = OrganizationMembership
        fields = [
            'id', 'organization', 'user', 'user_id', 'role',
            'is_active', 'invited_by', 'joined_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'joined_at', 'created_at', 'updated_at']


class OrganizationDetailSerializer(serializers.ModelSerializer):
    """Detailed Organization Serializer with members"""
    
    member_count = serializers.ReadOnlyField()
    members = OrganizationMembershipSerializer(source='memberships', many=True, read_only=True)
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description', 'logo_url', 'website',
            'subscription_tier', 'max_members', 'max_teams',
            'is_active', 'features', 'member_count', 'members',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'member_count']


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit Log Serializer"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'organization', 'action', 'resource_type',
            'resource_id', 'details', 'ip_address', 'user_agent',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User Registration Serializer"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        # Create user profile
        UserProfile.objects.create(user=user)
        return user


class TeamSerializer(serializers.ModelSerializer):
    """Team Serializer"""
    
    member_count = serializers.ReadOnlyField()
    channel_count = serializers.ReadOnlyField()
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Team
        fields = [
            'id', 'organization', 'name', 'description', 'avatar_url',
            'privacy', 'is_archived', 'settings',
            'member_count', 'channel_count', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Team Membership Serializer"""
    
    user = UserSerializer(read_only=True)
    team = TeamSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = TeamMembership
        fields = [
            'id', 'team', 'user', 'user_id', 'role',
            'is_active', 'is_favorite', 'notification_settings',
            'invited_by', 'joined_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'joined_at', 'created_at', 'updated_at']


class ChannelSerializer(serializers.ModelSerializer):
    """Channel Serializer"""
    
    member_count = serializers.ReadOnlyField()
    is_private = serializers.ReadOnlyField()
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Channel
        fields = [
            'id', 'team', 'name', 'description', 'channel_type',
            'is_archived', 'is_general', 'settings',
            'member_count', 'is_private', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChannelMembershipSerializer(serializers.ModelSerializer):
    """Channel Membership Serializer"""
    
    user = UserSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ChannelMembership
        fields = [
            'id', 'channel', 'user', 'user_id', 'role',
            'is_active', 'is_muted', 'is_pinned',
            'last_read_at', 'unread_count',
            'joined_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'joined_at', 'created_at', 'updated_at']


class ChannelTabSerializer(serializers.ModelSerializer):
    """Channel Tab Serializer"""
    
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ChannelTab
        fields = [
            'id', 'channel', 'name', 'tab_type', 'icon_url',
            'config', 'order', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeamDetailSerializer(serializers.ModelSerializer):
    """Detailed Team Serializer with members and channels"""
    
    member_count = serializers.ReadOnlyField()
    channel_count = serializers.ReadOnlyField()
    created_by = UserSerializer(read_only=True)
    members = TeamMembershipSerializer(source='memberships', many=True, read_only=True)
    channels = ChannelSerializer(many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = [
            'id', 'organization', 'name', 'description', 'avatar_url',
            'privacy', 'is_archived', 'settings',
            'member_count', 'channel_count', 'created_by',
            'members', 'channels',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChannelDetailSerializer(serializers.ModelSerializer):
    """Detailed Channel Serializer with members and tabs"""
    
    member_count = serializers.ReadOnlyField()
    is_private = serializers.ReadOnlyField()
    created_by = UserSerializer(read_only=True)
    members = ChannelMembershipSerializer(source='memberships', many=True, read_only=True)
    tabs = ChannelTabSerializer(many=True, read_only=True)
    
    class Meta:
        model = Channel
        fields = [
            'id', 'team', 'name', 'description', 'channel_type',
            'is_archived', 'is_general', 'settings',
            'member_count', 'is_private', 'created_by',
            'members', 'tabs',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MeetingSerializer(serializers.ModelSerializer):
    """Meeting Serializer"""
    host = UserSerializer(read_only=True)
    join_url = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    duration_minutes = serializers.ReadOnlyField()
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = [
            'id', 'meeting_code', 'title', 'description', 'host',
            'team', 'channel',  # Team context
            'max_participants', 'duration_limit_minutes',
            'is_lobby_enabled', 'is_recording_enabled',
            'is_chat_enabled', 'is_screen_share_enabled', 'is_locked',
            'status', 'started_at', 'ended_at',
            'scheduled_start', 'scheduled_end',
            'is_recurring', 'recurrence_pattern',
            'join_url', 'is_active', 'duration_minutes',
            'participants_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'meeting_code', 'host', 'status',
            'started_at', 'ended_at', 'created_at', 'updated_at'
        ]

    def get_participants_count(self, obj):
        return obj.participants.filter(status__in=['admitted', 'joined']).count()


class MeetingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating meetings"""
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Meeting
        fields = [
            'title', 'description', 'password',
            'team', 'channel',  # Team context
            'max_participants', 'duration_limit_minutes',
            'is_lobby_enabled', 'is_recording_enabled',
            'is_chat_enabled', 'is_screen_share_enabled',
            'scheduled_start', 'scheduled_end',
            'is_recurring', 'recurrence_pattern'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        meeting = Meeting.objects.create(**validated_data)
        
        if password:
            from django.contrib.auth.hashers import make_password
            meeting.password_hash = make_password(password)
            meeting.save()
        
        # Create analytics record
        MeetingAnalytics.objects.create(meeting=meeting)
        
        return meeting


class MeetingParticipantSerializer(serializers.ModelSerializer):
    """Meeting Participant Serializer"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = MeetingParticipant
        fields = [
            'id', 'user', 'role', 'status',
            'is_audio_muted', 'is_video_off', 'is_hand_raised',
            'hand_raised_at', 'is_screen_sharing',
            'connection_quality', 'joined_at', 'left_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Chat Message Serializer"""
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'sender', 'recipient', 'message_type',
            'content', 'is_private', 'file_url', 'file_name',
            'file_size', 'file_type', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at']


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat messages"""
    recipient_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = ChatMessage
        fields = ['content', 'message_type', 'is_private', 'recipient_id']

    def create(self, validated_data):
        recipient_id = validated_data.pop('recipient_id', None)
        if recipient_id:
            validated_data['recipient_id'] = recipient_id
        return ChatMessage.objects.create(**validated_data)


class MeetingRecordingSerializer(serializers.ModelSerializer):
    """Meeting Recording Serializer"""
    started_by = UserSerializer(read_only=True)

    class Meta:
        model = MeetingRecording
        fields = [
            'id', 'file_url', 'file_size', 'duration_seconds',
            'format', 'started_at', 'ended_at', 'started_by',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'started_by', 'created_at']


class MeetingReactionSerializer(serializers.ModelSerializer):
    """Meeting Reaction Serializer"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = MeetingReaction
        fields = ['id', 'user', 'reaction_type', 'created_at', 'expires_at']
        read_only_fields = ['id', 'user', 'created_at', 'expires_at']


class MeetingInvitationSerializer(serializers.ModelSerializer):
    """Meeting Invitation Serializer"""
    invited_by = UserSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = MeetingInvitation
        fields = [
            'id', 'email', 'user', 'status',
            'invited_by', 'created_at', 'responded_at'
        ]
        read_only_fields = ['id', 'user', 'invited_by', 'created_at', 'responded_at']


class MeetingAnalyticsSerializer(serializers.ModelSerializer):
    """Meeting Analytics Serializer"""
    
    class Meta:
        model = MeetingAnalytics
        fields = [
            'id', 'total_participants', 'peak_participants',
            'average_participants', 'actual_duration_minutes',
            'total_messages', 'total_reactions', 'total_hand_raises',
            'screen_shares_count', 'average_connection_quality',
            'disconnect_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MeetingDetailSerializer(serializers.ModelSerializer):
    """Detailed Meeting Serializer with nested data"""
    host = UserSerializer(read_only=True)
    participants = MeetingParticipantSerializer(many=True, read_only=True)
    analytics = MeetingAnalyticsSerializer(read_only=True)
    join_url = serializers.ReadOnlyField()

    class Meta:
        model = Meeting
        fields = [
            'id', 'meeting_code', 'title', 'description', 'host',
            'max_participants', 'duration_limit_minutes',
            'is_lobby_enabled', 'is_recording_enabled',
            'is_chat_enabled', 'is_screen_share_enabled', 'is_locked',
            'status', 'started_at', 'ended_at',
            'scheduled_start', 'scheduled_end',
            'join_url', 'participants', 'analytics',
            'created_at', 'updated_at'
        ]
