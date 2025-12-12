"""
Video Meeting System Models
Complete implementation for TrueTalk.AI Meeting App
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import secrets
import string



def generate_meeting_code():
    """Generate unique 12-character meeting code (e.g., abc-defg-hij)"""
    chars = string.ascii_lowercase + string.digits
    return '-'.join([''.join(secrets.choice(chars) for _ in range(4)) for _ in range(3)])




class Organization(models.Model):
    """
    Organization Model - Multi-tenant support
    Each organization represents a separate workspace/company
    """
    
    SUBSCRIPTION_TIERS = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    
    # Organization Settings
    logo_url = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Subscription
    subscription_tier = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TIERS,
        default='free'
    )
    max_members = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)]
    )
    max_teams = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)]
    )
    
    # Features
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=dict, blank=True)
    # Example: {"video_meetings": true, "file_storage_gb": 10, "recording": false}
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()


class OrganizationMembership(models.Model):
    """
    Organization Membership Model
    Links users to organizations with roles
    """
    
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('guest', 'Guest'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organization_memberships'
    )
    
    # Role & Permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Status
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_org_invitations'
    )
    
    # Timestamps
    joined_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organization_memberships'
        unique_together = ['organization', 'user']
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.organization.name} ({self.role})"
    
    def is_owner(self):
        return self.role == 'owner'
    
    def is_admin(self):
        return self.role in ['owner', 'admin']
    
    def can_manage_members(self):
        return self.role in ['owner', 'admin']


class UserProfile(models.Model):
    """
    Extended User Profile
    Additional user information beyond Django's default User model
    """
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('away', 'Away'),
        ('do_not_disturb', 'Do Not Disturb'),
        ('offline', 'Offline'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True
    )
    
    # Profile Information
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Location & Timezone
    timezone = models.CharField(max_length=50, default='UTC')
    location = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )
    status_message = models.CharField(max_length=100, blank=True)
    
    # Preferences
    preferences = models.JSONField(default=dict, blank=True)
    # Example: {"theme": "dark", "notifications": {"email": true, "push": true}}
    
    # Activity
    last_seen = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen', 'updated_at'])
    
    @property
    def is_online(self):
        """Check if user is online (seen in last 5 minutes)"""
        if not self.last_seen:
            return False
        from datetime import timedelta
        return timezone.now() - self.last_seen < timedelta(minutes=5)


class AuditLog(models.Model):
    """
    Audit Log Model
    Track important actions for compliance and security
    """
    
    ACTION_TYPES = [
        ('user.login', 'User Login'),
        ('user.logout', 'User Logout'),
        ('user.created', 'User Created'),
        ('user.updated', 'User Updated'),
        ('user.deleted', 'User Deleted'),
        ('org.created', 'Organization Created'),
        ('org.updated', 'Organization Updated'),
        ('org.deleted', 'Organization Deleted'),
        ('team.created', 'Team Created'),
        ('team.updated', 'Team Updated'),
        ('team.deleted', 'Team Deleted'),
        ('meeting.created', 'Meeting Created'),
        ('meeting.started', 'Meeting Started'),
        ('meeting.ended', 'Meeting Ended'),
        ('file.uploaded', 'File Uploaded'),
        ('file.downloaded', 'File Downloaded'),
        ('file.deleted', 'File Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who & Where
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    # What
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=50)  # e.g., 'team', 'meeting', 'file'
    resource_id = models.CharField(max_length=255, blank=True)
    
    # Details
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # When
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user.username if self.user else 'System'} at {self.created_at}"


class Team(models.Model):
    """
    Team Model - Groups within an organization
    """
    
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='teams'
    )
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    
    # Settings
    privacy = models.CharField(
        max_length=20,
        choices=PRIVACY_CHOICES,
        default='private'
    )
    is_archived = models.BooleanField(default=False)
    
    # Team Settings
    settings = models.JSONField(default=dict, blank=True)
    # Example: {"allow_guests": true, "allow_member_create_channels": false}
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_teams'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teams'
        ordering = ['name']
        unique_together = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization', 'is_archived']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()
    
    @property
    def channel_count(self):
        return self.channels.filter(is_archived=False).count()


class TeamMembership(models.Model):
    """
    Team Membership Model
    Links users to teams with roles
    """
    
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('guest', 'Guest'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    
    # Role & Permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_favorite = models.BooleanField(default=False)
    
    # Notifications
    notification_settings = models.JSONField(default=dict, blank=True)
    # Example: {"mentions": true, "all_messages": false, "channel_updates": true}
    
    # Metadata
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_team_invitations'
    )
    joined_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'team_memberships'
        unique_together = ['team', 'user']
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['team', 'is_active']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.team.name} ({self.role})"
    
    def is_owner(self):
        return self.role == 'owner'
    
    def is_admin(self):
        return self.role in ['owner', 'admin']
    
    def can_manage_channels(self):
        return self.role in ['owner', 'admin']


class Channel(models.Model):
    """
    Channel Model - Communication channels within teams
    """
    
    TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('private', 'Private'),
        ('shared', 'Shared'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='channels'
    )
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Channel Type
    channel_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='standard'
    )
    
    # Settings
    is_archived = models.BooleanField(default=False)
    is_general = models.BooleanField(default=False)  # Default channel for team
    
    # Channel Settings
    settings = models.JSONField(default=dict, blank=True)
    # Example: {"allow_reactions": true, "allow_file_upload": true, "moderation": false}
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_channels'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'channels'
        ordering = ['name']
        unique_together = ['team', 'name']
        indexes = [
            models.Index(fields=['team', 'is_archived']),
            models.Index(fields=['channel_type']),
        ]
    
    def __str__(self):
        return f"#{self.name} ({self.team.name})"
    
    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()
    
    @property
    def is_private(self):
        return self.channel_type == 'private'


class ChannelMembership(models.Model):
    """
    Channel Membership Model
    Links users to channels with permissions
    """
    
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='channel_memberships'
    )
    
    # Role
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_muted = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    # Read Status
    last_read_at = models.DateTimeField(null=True, blank=True)
    unread_count = models.IntegerField(default=0)
    
    # Metadata
    joined_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'channel_memberships'
        unique_together = ['channel', 'user']
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['channel', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.channel.name}"
    
    def mark_as_read(self):
        """Mark channel as read"""
        self.last_read_at = timezone.now()
        self.unread_count = 0
        self.save(update_fields=['last_read_at', 'unread_count', 'updated_at'])
    
    def increment_unread(self):
        """Increment unread message count"""
        self.unread_count += 1
        self.save(update_fields=['unread_count', 'updated_at'])


class ChannelTab(models.Model):
    """
    Channel Tab Model
    Custom tabs within channels (Files, Calendar, Apps, etc.)
    """
    
    TAB_TYPES = [
        ('files', 'Files'),
        ('calendar', 'Calendar'),
        ('notes', 'Notes'),
        ('tasks', 'Tasks'),
        ('custom', 'Custom App'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='tabs'
    )
    
    # Tab Information
    name = models.CharField(max_length=100)
    tab_type = models.CharField(max_length=20, choices=TAB_TYPES)
    icon_url = models.URLField(blank=True, null=True)
    
    # Configuration
    config = models.JSONField(default=dict, blank=True)
    # Example: {"folder_id": "abc123", "view": "grid"}
    
    # Order
    order = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_channel_tabs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'channel_tabs'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['channel']),
        ]
    
    def __str__(self):
        return f"{self.name} tab in {self.channel.name}"


class Meeting(models.Model):
    """Meeting Model - Core meeting information"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting_code = models.CharField(max_length=20, unique=True, default=generate_meeting_code, db_index=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_meetings')
    password_hash = models.CharField(max_length=255, blank=True, null=True)

    # Team Context (Integrated)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='meetings', null=True, blank=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='meetings', null=True, blank=True)

    # Meeting Settings
    max_participants = models.IntegerField(
        default=300,
        validators=[MinValueValidator(2), MaxValueValidator(300)]
    )
    duration_limit_minutes = models.IntegerField(
        default=180,
        validators=[MinValueValidator(15), MaxValueValidator(1440)]
    )
    is_lobby_enabled = models.BooleanField(default=True)
    is_recording_enabled = models.BooleanField(default=False)
    is_chat_enabled = models.BooleanField(default=True)
    is_screen_share_enabled = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)

    # Meeting State
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    scheduled_start = models.DateTimeField(null=True, blank=True, db_index=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)

    # Recurring Meeting
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.JSONField(null=True, blank=True)
    # Example: {"type": "weekly", "interval": 1, "days": ["monday", "wednesday"]}

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meetings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meeting_code']),
            models.Index(fields=['host', 'status']),
            models.Index(fields=['scheduled_start']),
        ]

    def __str__(self):
        return f"{self.title} ({self.meeting_code})"

    @property
    def join_url(self):
        return f"https://meet.truetalk.ai/{self.meeting_code}"

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def duration_minutes(self):
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() / 60)
        return 0

    def start_meeting(self):
        """Start the meeting"""
        self.status = 'active'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])

    def end_meeting(self):
        """End the meeting"""
        self.status = 'ended'
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'ended_at', 'updated_at'])


class MeetingParticipant(models.Model):
    """Meeting Participant Model"""
    
    ROLE_CHOICES = [
        ('host', 'Host'),
        ('co_host', 'Co-Host'),
        ('participant', 'Participant'),
    ]

    STATUS_CHOICES = [
        ('lobby', 'In Lobby'),
        ('admitted', 'Admitted'),
        ('joined', 'Joined'),
        ('left', 'Left'),
        ('removed', 'Removed'),
    ]

    QUALITY_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_participations')

    # Role & Permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')

    # Participant State
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lobby')
    is_audio_muted = models.BooleanField(default=False)
    is_video_off = models.BooleanField(default=False)
    is_hand_raised = models.BooleanField(default=False)
    hand_raised_at = models.DateTimeField(null=True, blank=True)
    is_screen_sharing = models.BooleanField(default=False)

    # Connection Info
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    connection_quality = models.CharField(
        max_length=20,
        choices=QUALITY_CHOICES,
        null=True,
        blank=True
    )

    # WebRTC Info
    peer_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meeting_participants'
        unique_together = ['meeting', 'user']
        ordering = ['hand_raised_at', 'joined_at']
        indexes = [
            models.Index(fields=['meeting', 'status']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.meeting.title}"

    def raise_hand(self):
        """Raise hand"""
        self.is_hand_raised = True
        self.hand_raised_at = timezone.now()
        self.save(update_fields=['is_hand_raised', 'hand_raised_at', 'updated_at'])

    def lower_hand(self):
        """Lower hand"""
        self.is_hand_raised = False
        self.hand_raised_at = None
        self.save(update_fields=['is_hand_raised', 'hand_raised_at', 'updated_at'])


class ChatMessage(models.Model):
    """Chat Message Model"""
    
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('reaction', 'Reaction'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages'
    )

    # Message Content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()

    # Private Message
    recipient = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_messages'
    )
    is_private = models.BooleanField(default=False)

    # File Attachment
    file_url = models.URLField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['meeting', 'created_at']),
            models.Index(fields=['sender']),
        ]

    def __str__(self):
        return f"Message from {self.sender.username if self.sender else 'System'}"


class MeetingRecording(models.Model):
    """Meeting Recording Model"""
    
    STATUS_CHOICES = [
        ('recording', 'Recording'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='recordings')

    # Recording Info
    file_url = models.URLField()
    file_size = models.BigIntegerField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    format = models.CharField(max_length=20, default='webm')

    # Recording Metadata
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='started_recordings'
    )

    # Processing Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='recording')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'meeting_recordings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meeting']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Recording of {self.meeting.title}"


class MeetingReaction(models.Model):
    """Meeting Reaction Model"""
    
    REACTION_TYPES = [
        ('thumbs_up', '👍'),
        ('thumbs_down', '👎'),
        ('heart', '❤️'),
        ('laugh', '😂'),
        ('clap', '👏'),
        ('celebrate', '🎉'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')

    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'meeting_reactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meeting', 'expires_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Reactions expire after 5 seconds
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(seconds=5)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_type_display()}"


class MeetingInvitation(models.Model):
    """Meeting Invitation Model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='invitations')

    # Invitee Info
    email = models.EmailField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='meeting_invitations'
    )

    # Invitation Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'meeting_invitations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meeting', 'status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"Invitation to {self.email} for {self.meeting.title}"


class MeetingAnalytics(models.Model):
    """Meeting Analytics Model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name='analytics'
    )

    # Participant Stats
    total_participants = models.IntegerField(default=0)
    peak_participants = models.IntegerField(default=0)
    average_participants = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Duration Stats
    actual_duration_minutes = models.IntegerField(null=True, blank=True)

    # Engagement Stats
    total_messages = models.IntegerField(default=0)
    total_reactions = models.IntegerField(default=0)
    total_hand_raises = models.IntegerField(default=0)
    screen_shares_count = models.IntegerField(default=0)

    # Quality Stats
    average_connection_quality = models.CharField(max_length=20, blank=True)
    disconnect_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meeting_analytics'

    def __str__(self):
        return f"Analytics for {self.meeting.title}"
