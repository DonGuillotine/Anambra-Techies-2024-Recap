from rest_framework import serializers
from users.models import User

class PhoneNumberAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)
    
    def validate_phone_number(self, value):
        cleaned_number = ''.join(filter(str.isdigit, value))
        
        if len(cleaned_number) == 10 and cleaned_number.startswith('0'):
            cleaned_number = '+234' + cleaned_number[1:]
        elif len(cleaned_number) == 11 and cleaned_number.startswith('0'):
            cleaned_number = '+234' + cleaned_number[1:]
        elif len(cleaned_number) == 13 and cleaned_number.startswith('234'):
            cleaned_number = '+' + cleaned_number
        
        if not 13 <= len(cleaned_number) <= 14:
            raise serializers.ValidationError("Invalid phone number format")
        
        return cleaned_number
    
class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)
    otp = serializers.CharField(max_length=6)
    phone_id = serializers.CharField()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone_number', 'display_name', 'last_active']
        read_only_fields = ['phone_number', 'last_active']

