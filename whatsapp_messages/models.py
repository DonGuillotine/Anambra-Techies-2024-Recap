import uuid
from django.db import models
from users.models import User

class Message(models.Model):
    MESSAGE_TYPES = (
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('AUDIO', 'Audio'),
        ('DOCUMENT', 'Document')
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField()
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        default='TEXT'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['sender', 'timestamp']),
            models.Index(fields=['message_type'])
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.sender.phone_number} - {self.timestamp}"