from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    """
    Chat message model with sender and receiver for user-to-user messaging.
    """

    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages", null=True, blank=True
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        receiver_name = self.receiver.username if self.receiver else "Everyone"
        return f"{self.sender.username} -> {receiver_name}: {self.text[:30]}"
