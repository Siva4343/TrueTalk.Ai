from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def to_json(self):
        return {
            "id": self.id,
            "sender": self.sender.username,
            "text": self.text,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "timestamp": str(self.timestamp)
        }
