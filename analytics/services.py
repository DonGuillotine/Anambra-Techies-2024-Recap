from datetime import datetime, timedelta
from django.db.models import Count, Avg, F, Q
from django.db import models
from django.utils import timezone
from whatsapp_messages.models import Message
from users.models import User
from .models import UserStatistics, GroupStatistics

class AnalyticsService:
    def __init__(self):
        self.year_2024_start = datetime(2024, 1, 1)
        self.year_2024_end = datetime(2024, 12, 31, 23, 59, 59)

    def update_group_statistics(self) -> None:
        """Update daily group statistics."""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # Get messages from yesterday
        messages = Message.objects.filter(
            timestamp__date=yesterday
        )

        # Calculate daily statistics
        stats = {
            'total_messages': messages.count(),
            'active_users': messages.values('sender').distinct().count(),
            'media_count': messages.exclude(message_type='TEXT').count(),
            'peak_hour': messages.annotate(
                hour=models.functions.ExtractHour('timestamp')
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('-count').first()['hour'] if messages.exists() else None
        }

        # Update or create group statistics
        GroupStatistics.objects.update_or_create(
            date=yesterday,
            defaults=stats
        )

    def get_user_trends(self, user: User, days: int = 30) -> dict:
        """Analyze user engagement trends over time."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        daily_messages = Message.objects.filter(
            sender=user,
            timestamp__range=(start_date, end_date)
        ).annotate(
            date=models.functions.TruncDate('timestamp')
        ).values('date').annotate(
            message_count=Count('id'),
            media_count=Count('id', filter=Q(message_type__in=['IMAGE', 'VIDEO', 'AUDIO', 'DOCUMENT'])),
            avg_length=Avg(
                models.functions.Length('content'),
                filter=Q(message_type='TEXT')
            )
        ).order_by('date')

        return {
            'daily_stats': list(daily_messages),
            'trend': self._calculate_trend(daily_messages)
        }

    def _calculate_trend(self, daily_stats) -> str:
        """Calculate engagement trend (increasing/decreasing/stable)."""
        if not daily_stats:
            return 'insufficient_data'

        # Compare first and last week averages
        first_week = daily_stats[:7]
        last_week = daily_stats[-7:]

        first_week_avg = sum(day['message_count'] for day in first_week) / len(first_week)
        last_week_avg = sum(day['message_count'] for day in last_week) / len(last_week)

        difference = last_week_avg - first_week_avg
        if difference > 2:
            return 'increasing'
        elif difference < -2:
            return 'decreasing'
        return 'stable'

    def calculate_user_metrics(self, user: User, date_range: tuple = None) -> dict:
        """Calculate metrics for a specific user."""
        if not date_range:
            date_range = (self.year_2024_start, self.year_2024_end)
        
        start_date, end_date = date_range
        
        messages = Message.objects.filter(
            sender=user,
            timestamp__range=(start_date, end_date)
        )

        base_metrics = messages.aggregate(
            total_messages=Count('id'),
            media_count=Count('id', filter=~Q(message_type='TEXT')),
            avg_length=Avg(
                models.functions.Length('content'),
                filter=Q(message_type='TEXT')
            ),
            total_chars=models.Sum(
                models.functions.Length('content'),
                filter=Q(message_type='TEXT')
            )
        )

        # Calculate response times
        response_times = []
        previous_message = None
        for message in messages.order_by('timestamp'):
            if previous_message:
                time_diff = (message.timestamp - previous_message.timestamp).total_seconds()
                if time_diff < 3600:
                    response_times.append(time_diff)
            previous_message = message

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        metrics = {
            'total_messages': base_metrics['total_messages'],
            'media_messages': base_metrics['media_count'],
            'active_days': messages.dates('timestamp', 'day').count(),
            'avg_message_length': round(base_metrics['avg_length'] or 0, 2),
            'total_characters': base_metrics['total_chars'] or 0,
            'avg_response_time_seconds': round(avg_response_time, 2),
            'messages_per_day': round(
                base_metrics['total_messages'] / messages.dates('timestamp', 'day').count()
                if messages.exists() else 0, 2
            ),
            'engagement_trend': self.get_user_trends(user)['trend']
        }

        UserStatistics.objects.update_or_create(
            user=user,
            defaults={
                'total_messages': metrics['total_messages'],
                'media_messages': metrics['media_messages'],
                'active_days': metrics['active_days'],
                'avg_message_length': metrics['avg_message_length'],
                'last_calculated': timezone.now()
            }
        )

        return metrics
    
    def calculate_group_metrics(self, date_range: tuple = None) -> dict:
        """Calculate metrics for the entire group."""
        if not date_range:
            date_range = (self.year_2024_start, self.year_2024_end)
        
        start_date, end_date = date_range
        
        messages = Message.objects.filter(timestamp__range=(date_range))
        
        total_messages = messages.count()
        active_users = messages.values('sender').distinct().count()
        media_count = messages.exclude(message_type='TEXT').count()

        daily_stats = messages.annotate(
            date=models.functions.TruncDate('timestamp')
        ).values('date').annotate(
            count=Count('id'),
            active_users=Count('sender', distinct=True)
        ).order_by('date')
        
        top_users = messages.values('sender__phone_number').annotate(
            message_count=Count('id')
        ).order_by('-message_count')[:10]
        
        return {
            'total_messages': total_messages,
            'active_users': active_users,
            'media_count': media_count,
            'messages_per_user': round(total_messages / active_users if active_users > 0 else 0, 2),
            'daily_stats': list(daily_stats),
            'top_users': list(top_users)
        }

    def get_activity_patterns(self, date_range: tuple = None) -> dict:
        """Analyze activity patterns."""
        if not date_range:
            date_range = (self.year_2024_start, self.year_2024_end)
            
        messages = Message.objects.filter(timestamp__range=(date_range))

        hourly_distribution = messages.annotate(
            hour=models.functions.ExtractHour('timestamp')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        weekly_distribution = messages.annotate(
            day=models.functions.ExtractWeekDay('timestamp')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        return {
            'hourly_distribution': list(hourly_distribution),
            'weekly_distribution': list(weekly_distribution)
        }
