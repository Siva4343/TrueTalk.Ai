from django.db import models

class Caption(models.Model):
    original_text = models.TextField()
    hindi = models.TextField()
    telugu = models.TextField()
    tamil = models.TextField()
    speaker = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_text[:50]


# Create your models here.
