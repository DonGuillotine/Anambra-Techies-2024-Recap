from django.db import models
from users.models import User

class UserStatistics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='statistics')
    total_messages = models.IntegerField(default=0)
    media_messages = models.IntegerField(default=0)
    active_days = models.IntegerField(default=0)
    avg_message_length = models.FloatField(default=0)
    peak_activity_hour = models.IntegerField(null=True)
    last_calculated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stats for {self.user.phone_number}"

class GroupStatistics(models.Model):
    date = models.DateField(unique=True)
    total_messages = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    media_count = models.IntegerField(default=0)
    peak_hour = models.IntegerField(null=True)
    
    def __str__(self):
        return f"Group stats for {self.date}"
