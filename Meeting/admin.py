"""
Admin Configuration for Video Meeting System
"""

from django.contrib import admin
from .models import (
    Meeting, MeetingParticipant, ChatMessage,
    MeetingRecording, MeetingReaction, MeetingInvitation,
    MeetingAnalytics, Team, TeamMembership, Channel,
    ChannelMembership, ChannelTab, Organization, OrganizationMembership,
    UserProfile, AuditLog
)


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'meeting_code', 'host', 'status', 'started_at', 'created_at']
    list_filter = ['status', 'is_lobby_enabled', 'is_recording_enabled', 'created_at']
    search_fields = ['title', 'meeting_code', 'host__username']
    readonly_fields = ['id', 'meeting_code', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'meeting_code', 'title', 'description', 'host')
        }),
        ('Settings', {
            'fields': (
                'max_participants', 'duration_limit_minutes',
                'is_lobby_enabled', 'is_recording_enabled',
                'is_chat_enabled', 'is_screen_share_enabled',
                'is_locked', 'password_hash'
            )
        }),
        ('Status', {
            'fields': ('status', 'started_at', 'ended_at')
        }),
        ('Schedule', {
            'fields': ('scheduled_start', 'scheduled_end', 'is_recurring', 'recurrence_pattern')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'meeting', 'role', 'status', 'is_audio_muted', 'is_video_off', 'joined_at']
    list_filter = ['role', 'status', 'is_audio_muted', 'is_video_off', 'is_hand_raised']
    search_fields = ['user__username', 'meeting__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'meeting', 'user', 'role')
        }),
        ('Status', {
            'fields': (
                'status', 'is_audio_muted', 'is_video_off',
                'is_hand_raised', 'hand_raised_at', 'is_screen_sharing'
            )
        }),
        ('Connection', {
            'fields': ('connection_quality', 'peer_id', 'joined_at', 'left_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'meeting', 'message_type', 'is_private', 'created_at']
    list_filter = ['message_type', 'is_private', 'created_at']
    search_fields = ['sender__username', 'content', 'meeting__title']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(MeetingRecording)
class MeetingRecordingAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'status', 'duration_seconds', 'started_at', 'started_by']
    list_filter = ['status', 'format', 'created_at']
    search_fields = ['meeting__title', 'started_by__username']
    readonly_fields = ['id', 'created_at']


@admin.register(MeetingReaction)
class MeetingReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'meeting', 'reaction_type', 'created_at', 'expires_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__username', 'meeting__title']
    readonly_fields = ['id', 'created_at']


@admin.register(MeetingInvitation)
class MeetingInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'meeting', 'status', 'invited_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['email', 'meeting__title', 'invited_by__username']
    readonly_fields = ['id', 'created_at']


@admin.register(MeetingAnalytics)
class MeetingAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'meeting', 'total_participants', 'peak_participants',
        'total_messages', 'actual_duration_minutes'
    ]
    search_fields = ['meeting__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Meeting', {
            'fields': ('id', 'meeting')
        }),
        ('Participant Stats', {
            'fields': ('total_participants', 'peak_participants', 'average_participants')
        }),
        ('Engagement Stats', {
            'fields': (
                'total_messages', 'total_reactions',
                'total_hand_raises', 'screen_shares_count'
            )
        }),
        ('Quality Stats', {
            'fields': ('average_connection_quality', 'disconnect_count')
        }),
        ('Duration', {
            'fields': ('actual_duration_minutes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'privacy', 'is_archived', 'member_count', 'created_at']
    list_filter = ['privacy', 'is_archived', 'created_at']
    search_fields = ['name', 'organization__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'name', 'description', 'avatar_url')
        }),
        ('Settings', {
            'fields': ('privacy', 'is_archived', 'settings')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'is_active', 'is_favorite', 'joined_at']
    list_filter = ['role', 'is_active', 'is_favorite', 'joined_at']
    search_fields = ['user__username', 'team__name']
    readonly_fields = ['id', 'joined_at', 'created_at', 'updated_at']


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'channel_type', 'is_general', 'is_archived', 'member_count', 'created_at']
    list_filter = ['channel_type', 'is_general', 'is_archived', 'created_at']
    search_fields = ['name', 'team__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'team', 'name', 'description')
        }),
        ('Settings', {
            'fields': ('channel_type', 'is_general', 'is_archived', 'settings')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(ChannelMembership)
class ChannelMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'channel', 'role', 'is_active', 'is_muted', 'is_pinned', 'unread_count']
    list_filter = ['role', 'is_active', 'is_muted', 'is_pinned']
    search_fields = ['user__username', 'channel__name']
    readonly_fields = ['id', 'joined_at', 'created_at', 'updated_at']


@admin.register(ChannelTab)
class ChannelTabAdmin(admin.ModelAdmin):
    list_display = ['name', 'channel', 'tab_type', 'order', 'created_at']
    list_filter = ['tab_type', 'created_at']
    search_fields = ['name', 'channel__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'subscription_tier', 'member_count', 'is_active', 'created_at']
    list_filter = ['subscription_tier', 'is_active', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'description', 'logo_url', 'website')
        }),
        ('Subscription', {
            'fields': ('subscription_tier', 'max_members', 'max_teams', 'features')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'organization__name']
    readonly_fields = ['id', 'joined_at', 'created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'timezone', 'is_online', 'last_seen']
    list_filter = ['status', 'timezone']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['user', 'created_at', 'updated_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'organization', 'resource_type', 'created_at']
    list_filter = ['action', 'resource_type', 'created_at']
    search_fields = ['user__username', 'organization__name', 'resource_id']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
