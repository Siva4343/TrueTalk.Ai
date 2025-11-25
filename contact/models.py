from django.db import models
from django.contrib.auth.models import User

class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'phone_number']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.phone_number}"

class SharedContact(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_contacts')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_contacts')
    contact_name = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField(blank=True, null=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-shared_at']

    def __str__(self):
        return f"{self.contact_name} shared by {self.sender.username} to {self.receiver.username}"