from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import PhoneNumberAuthSerializer, OTPVerificationSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .services import StytchService

User = get_user_model()

class RequestOTPView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        tags=['auth'],
        request=PhoneNumberAuthSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP sent successfully",
                response={"type": "object", "properties": {"message": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Invalid phone number format")
        },
        description="Request an OTP for phone number authentication",
    )

    def post(self, request):
        serializer = PhoneNumberAuthSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            
            stytch_service = StytchService()
            result = stytch_service.send_whatsapp_otp(phone_number)
            
            if not result['success']:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user, created = User.objects.get_or_create(phone_number=phone_number)
            
            return Response({
                'message': 'OTP sent successfully via WhatsApp',
                 'phone_id': result['phone_id']
            })
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(
        tags=['auth'],
        request=OTPVerificationSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP verified successfully",
                response={
                    "type": "object",
                    "properties": {
                        "refresh": {"type": "string"},
                        "access": {"type": "string"}
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid OTP")
        },
        description="Verify OTP and get access tokens",
    )

    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp = serializer.validated_data['otp']
            phone_id = serializer.validated_data['phone_id']
            
            stytch_service = StytchService()
            result = stytch_service.verify_whatsapp_otp(phone_id, otp)
            
            if not result['success'] or not result.get('valid'):
                return Response(
                    {'error': result.get('error', 'Invalid OTP')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.get(phone_number=phone_number)
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
