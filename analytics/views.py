from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .services import AnalyticsService
from users.models import User

class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = AnalyticsService()

    @action(detail=True, methods=['get'])
    def user_metrics(self, request, pk=None):
        """Get analytics for a specific user."""
        try:
            user = get_object_or_404(User, phone_number=pk)
            
            # Handle date range if provided in query params
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            date_range = None
            if start_date and end_date:
                try:
                    date_range = (
                        datetime.strptime(start_date, '%Y-%m-%d'),
                        datetime.strptime(end_date, '%Y-%m-%d')
                    )
                except ValueError:
                    return Response(
                        {'error': 'Invalid date format. Use YYYY-MM-DD'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            metrics = self.analytics_service.calculate_user_metrics(user, date_range)
            return Response(metrics)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
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
            return Response(trends)
            
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

    @action(detail=False, methods=['get'])
    def group_metrics(self, request):
        """Get group-wide analytics."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        date_range = None
        if start_date and end_date:
            try:
                date_range = (
                    datetime.strptime(start_date, '%Y-%m-%d'),
                    datetime.strptime(end_date, '%Y-%m-%d')
                )
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        metrics = self.analytics_service.calculate_group_metrics(date_range)
        return Response(metrics)

    @action(detail=False, methods=['get'])
    def activity_patterns(self, request):
        """Get activity patterns analysis."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        date_range = None
        if start_date and end_date:
            try:
                date_range = (
                    datetime.strptime(start_date, '%Y-%m-%d'),
                    datetime.strptime(end_date, '%Y-%m-%d')
                )
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        patterns = self.analytics_service.get_activity_patterns(date_range)
        return Response(patterns)

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
