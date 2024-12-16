from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from .services import AnalyticsService
from users.models import User
from .models import UserStatistics, GroupStatistics
from .serializers import (
    UserStatisticsSerializer,
    GroupStatisticsSerializer,
    UserTrendsSerializer,
    ActivityPatternSerializer,
    UserMetricsSerializer,
    GroupMetricsSerializer
)


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserMetricsSerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = AnalyticsService()

    @extend_schema(
        tags=['analytics'],
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='User phone number',
                required=True,
                pattern=r'^\+\d{1,15}$'
            ),
            OpenApiParameter(
                name='start_date',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Start date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='end_date',
                type=str,
                location=OpenApiParameter.QUERY,
                description='End date (YYYY-MM-DD)',
                required=False
            ),
        ],
        responses={
            200: UserMetricsSerializer,
            400: OpenApiResponse(description="Invalid date format"),
            404: OpenApiResponse(description="User not found")
        },
        description="Get analytics metrics for a specific user",
    )
    @action(detail=True, methods=['get'])
    def user_metrics(self, request, pk=None):
        """Get analytics for a specific user."""
        try:
            user = get_object_or_404(User, phone_number=pk)
            
            date_range = self._get_date_range_from_params(request.query_params)
            if isinstance(date_range, Response):
                return date_range

            metrics = self.analytics_service.calculate_user_metrics(user, date_range)
            serializer = UserMetricsSerializer(metrics)
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
    @extend_schema(
        tags=['analytics'],
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='User phone number',
                required=True,
                pattern=r'^\+\d{1,15}$'
            ),
            OpenApiParameter(
                name='days',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of days to analyze (1-365)',
                default=30,
                required=False
            ),
        ],
        responses={
            200: UserTrendsSerializer(many=True),
            400: OpenApiResponse(description="Invalid days parameter"),
            404: OpenApiResponse(description="User not found")
        },
        description="Get trend analysis for a specific user",
    )    
    @action(detail=True, methods=['get'])
    def user_trends(self, request, pk=None):
        """Get trend analysis for a specific user."""
        try:
            user = get_object_or_404(User, phone_number=pk)
            days = int(request.query_params.get('days', 30))
            
            if days < 1 or days > 365:
                return Response(
                    {'error': 'Days parameter must be between 1 and 365'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            trends = self.analytics_service.get_user_trends(user, days)
            serializer = UserTrendsSerializer(trends['daily_stats'], many=True)
            return Response({
                'daily_stats': serializer.data,
                'trend': trends['trend']
            })
            
        except ValueError:
            return Response(
                {'error': 'Invalid days parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=['analytics'],
        parameters=[
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Start date (YYYY-MM-DD)',
                required=False,
                pattern=r'^\d{4}-\d{2}-\d{2}$'
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='End date (YYYY-MM-DD)',
                required=False,
                pattern=r'^\d{4}-\d{2}-\d{2}$'
            ),
        ],
        responses={
            200: GroupMetricsSerializer,
            400: OpenApiResponse(description="Invalid date format")
        },
        description="Get group-wide analytics metrics",
    )
    @action(detail=False, methods=['get'])
    def group_metrics(self, request):
        """Get group-wide analytics."""
        date_range = self._get_date_range_from_params(request.query_params)
        if isinstance(date_range, Response):
            return date_range

        metrics = self.analytics_service.calculate_group_metrics(date_range)
        serializer = GroupMetricsSerializer(metrics)
        return Response(serializer.data)

    @extend_schema(
        tags=['analytics'],
        parameters=[
            OpenApiParameter(
                name='start_date',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Start date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='end_date',
                type=str,
                location=OpenApiParameter.QUERY,
                description='End date (YYYY-MM-DD)',
                required=False
            ),
        ],
        responses={
            200: ActivityPatternSerializer,
            400: OpenApiResponse(description="Invalid date format")
        },
        description="Get activity patterns analysis",
    )
    @action(detail=False, methods=['get'])
    def activity_patterns(self, request):
            """Get activity patterns analysis."""
            date_range = self._get_date_range_from_params(request.query_params)
            if isinstance(date_range, Response):
                return date_range

            patterns = self.analytics_service.get_activity_patterns(date_range)
            serializer = ActivityPatternSerializer(patterns)
            return Response(serializer.data)

    @extend_schema(
        tags=['analytics'],
        responses={
            200: OpenApiResponse(description="Statistics updated successfully"),
            403: OpenApiResponse(description="Permission denied"),
            500: OpenApiResponse(description="Internal server error")
        },
        description="Manually trigger update of group statistics (staff only)",
    )
    @action(detail=False, methods=['post'])
    def update_group_stats(self, request):
        """Manually trigger update of group statistics."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            self.analytics_service.update_group_statistics()
            return Response({'status': 'Group statistics updated successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to update group statistics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def _get_date_range_from_params(self, query_params):
        """Helper method to get date range from query parameters."""
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')
        
        if not (start_date and end_date):
            return None
            
        try:
            return (
                datetime.strptime(start_date, '%Y-%m-%d'),
                datetime.strptime(end_date, '%Y-%m-%d')
            )
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
