from rest_framework import serializers

from .models import User


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'user_type', 'whatsapp_number', 'address', 'pincode',
            'city', 'password', "is_verify"
            
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        validated_data['user_type'] = 'customer'
        user = User.objects.create_user(**validated_data)
        return user
    

class AdminRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'user_type', 'email', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        validated_data['user_type'] = 'admin'
        user = User.objects.create_user(**validated_data)
        return user
