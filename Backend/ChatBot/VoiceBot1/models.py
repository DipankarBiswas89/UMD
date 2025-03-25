from django.db import models

# Create your models here.


class Conversation(models.Model):
    user_input = models.TextField()
    bot_response = models.TextField()
    audio_response = models.FileField(upload_to='audio_responses/', null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation at {self.created_at}"