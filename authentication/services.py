import stytch
from django.conf import settings

class StytchService:
    def __init__(self):
        self.client = stytch.Client(
            project_id=settings.STYTCH_PROJECT_ID,
            secret=settings.STYTCH_SECRET,
            environment=settings.STYTCH_ENV
        )

    def send_whatsapp_otp(self, phone_number: str) -> dict:
        """Send OTP via WhatsApp without user creation."""
        try:
            response = self.client.otps.whatsapp.login_or_create(
                phone_number=phone_number
            )
            return {
                'success': True,
                'phone_id': response.phone_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        
    def verify_whatsapp_otp(self, phone_id: str, code: str) -> dict:
        """Verify WhatsApp OTP."""
        try:
            response = self.client.otps.authenticate(
                method_id=phone_id,
                code=code
            )
            return {
                'success': True,
                'valid': True,
                'response': response
            }
        except Exception as e:
            return {
                'success': False,
                'valid': False,
                'error': str(e)
            }

