from rest_framework import serializers
from users.models import User
from .models import UserStatistics, GroupStatistics

class UserStatisticsSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number')
    
    class Meta:
        model = UserStatistics
        fields = [
            'phone_number',
            'total_messages',
            'media_messages',
            'active_days',
            'avg_message_length',
            'peak_activity_hour',
            'last_calculated'
        ]

class GroupStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupStatistics
        fields = [
            'date',
            'total_messages',
            'active_users',
            'media_count',
            'peak_hour'
        ]

class UserTrendsSerializer(serializers.Serializer):
    date = serializers.DateField()
    message_count = serializers.IntegerField()
    media_count = serializers.IntegerField()
    avg_length = serializers.FloatField()

class ActivityPatternSerializer(serializers.Serializer):
    hourly_distribution = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    weekly_distribution = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )

class UserMetricsSerializer(serializers.Serializer):
    total_messages = serializers.IntegerField()
    media_messages = serializers.IntegerField()
    active_days = serializers.IntegerField()
    avg_message_length = serializers.FloatField()
    total_characters = serializers.IntegerField()
    avg_response_time_seconds = serializers.FloatField()
    messages_per_day = serializers.FloatField()
    engagement_trend = serializers.CharField()

class GroupMetricsSerializer(serializers.Serializer):
    total_messages = serializers.IntegerField()
    active_users = serializers.IntegerField()
    media_count = serializers.IntegerField()
    messages_per_user = serializers.FloatField()
    daily_stats = GroupStatisticsSerializer(many=True)
    top_users = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )