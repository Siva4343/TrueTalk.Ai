from django.db import models

class NewsArticle(models.Model):
    title = models.CharField(max_length=800)
    summary = models.TextField(blank=True, null=True)
    link = models.URLField(unique=True)
    published = models.CharField(max_length=200, blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    source = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source} | {self.title[:80]}"
