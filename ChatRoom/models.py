from django.db import models


class Message(models.Model):
    """
    Simple chat message model.

    For now we only store:
    - author name
    - text content
    - created_at timestamp
    """

    author = models.CharField(max_length=100)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.author}: {self.text[:30]}"
