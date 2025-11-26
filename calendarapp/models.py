# calendarapp/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Event(models.Model):
    RECURRENCE_CHOICES = [
        ("none", "None"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    # Make owner optional (dev-friendly). Use SET_NULL so removing a user
    # doesn't delete events. If you require ownership, revert to CASCADE and
    # enforce authentication in views.
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="events",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_all_day = models.BooleanField(default=False)
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default="none")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time", "created_at"]

    def __str__(self):
        return self.title or f"Event {self.pk}"

    def clean(self):
        # Basic validation: if end_time provided, it must be >= start_time
        if self.end_time and self.end_time < self.start_time:
            raise ValidationError({"end_time": "end_time must be equal to or after start_time."})


class Reminder(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reminders")
    remind_at = models.DateTimeField()
    message = models.CharField(max_length=255, blank=True)
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["remind_at", "created_at"]

    def __str__(self):
        return f"Reminder for {self.event.title if self.event else 'unknown event'} at {self.remind_at}"
