from django.db import models
from django.contrib.auth.models import User


class Group(models.Model):
    """
    Group model for group chats.
    """
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name="chat_groups")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """
    Extended user profile to store phone number.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Message(models.Model):
    """
    Chat message model with sender and receiver for user-to-user messaging.
    Also supports group messaging and different message types.
    """
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
        ('location', 'Location'),
    )

    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages", null=True, blank=True
    )
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="messages", null=True, blank=True
    )
    text = models.TextField(blank=True, null=True)
    msg_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    attachment_url = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        if self.group:
            return f"{self.sender.username} in {self.group.name}: {self.msg_type}"
        receiver_name = self.receiver.username if self.receiver else "Unknown"
        return f"{self.sender.username} -> {receiver_name}: {self.msg_type}"
