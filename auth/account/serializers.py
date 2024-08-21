from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from rest_framework.exceptions import ErrorDetail, ValidationError



User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name","phone","email","password","active","otp_pending"]
        extra_kwargs = {
            "id": {"read_only": True},
            "password": {'min_length':5},
        }  
        
        
    def create(self, validated_data):
        pwd = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(pwd)
        user.save()
        return user
 
    def check_active(self):
        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )
        validated_data = self.initial_data
        try:
            user = User.objects.get(
                    Q(email=validated_data["email"]) | Q(phone=validated_data["phone"]) 
                )    
            # Already registered user without verification,  try to register again update it
            if user and not user.is_active:
                user.delete()
        except User.DoesNotExist:
            return None


class VerifyAccountSerializer(serializers.Serializer):
    email = serializers.CharField()
    otp = serializers.CharField()
