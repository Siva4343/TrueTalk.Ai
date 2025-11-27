from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class CallHistory(models.Model):
    CALL_TYPES = (
        ('voice', 'Voice Call'),
        ('video', 'Video Call'),
    )
    
    CALL_STATUS = (
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call_id = models.CharField(max_length=100, unique=True)
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls')
    callee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls', null=True, blank=True)
    group = models.ForeignKey('chat.Group', on_delete=models.CASCADE, null=True, blank=True)
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    status = models.CharField(max_length=10, choices=CALL_STATUS, default='initiated')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)  # in seconds
    end_reason = models.CharField(max_length=100, blank=True)
    is_screen_sharing = models.BooleanField(default=False)

    class Meta:
        db_table = 'call_history'
        ordering = ['-start_time']

    def __str__(self):
        if self.group:
            return f"{self.call_type} call in {self.group.name} - {self.status}"
        return f"{self.call_type} call {self.caller} -> {self.callee} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status == 'ended' and self.start_time and not self.end_time:
            from django.utils import timezone
            self.end_time = timezone.now()
            if self.start_time:
                self.duration = (self.end_time - self.start_time).seconds
        super().save(*args, **kwargs)


class CallParticipant(models.Model):
    ROLE_CHOICES = (
        ('initiator', 'Initiator'),
        ('participant', 'Participant'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call = models.ForeignKey(CallHistory, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'call_participants'
        unique_together = ['call', 'user']

    def __str__(self):
        return f"{self.user.username} in {self.call.call_id}"


class ActiveCall(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call_id = models.CharField(max_length=100, unique=True)
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_calls_initiated')
    participants = models.ManyToManyField(User, through='ActiveCallParticipant', related_name='active_calls')
    call_type = models.CharField(max_length=10, choices=CallHistory.CALL_TYPES)
    is_group_call = models.BooleanField(default=False)
    group = models.ForeignKey('chat.Group', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_screen_sharing = models.BooleanField(default=False)

    class Meta:
        db_table = 'active_calls'

    def __str__(self):
        return f"Active {self.call_type} call: {self.call_id}"


class ActiveCallParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    active_call = models.ForeignKey(ActiveCall, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    stream_id = models.CharField(max_length=100, blank=True)  # For tracking media streams

    class Meta:
        db_table = 'active_call_participants'
        unique_together = ['active_call', 'user']