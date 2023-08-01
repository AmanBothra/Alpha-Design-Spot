from rest_framework import serializers

from app_modules.website import models



class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Enquiry
        fields = ['id', 'name', 'email', 'phone_number', 'standard', 'message']
        
        

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Testimonial
        fields = ['id', 'image', 'client_name']