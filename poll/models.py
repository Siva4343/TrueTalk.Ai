from django.db import models
from django.contrib.auth.models import User

class Poll(models.Model):
    question = models.CharField(max_length=255)
    allow_multiple = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('poll', 'option', 'user')


