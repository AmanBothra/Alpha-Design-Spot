from app_modules.website import serializers
from rest_framework import permissions

from lib.viewsets import BaseModelViewSet
from app_modules.website.models import Enquiry, Testimonial


class EnquiryViewSet(BaseModelViewSet):
    serializer_class = serializers.EnquirySerializer
    queryset = Enquiry.objects.all()
    permission_classes = [permissions.AllowAny]
    

class TestimonalViewSet(BaseModelViewSet):
    serializer_class = serializers.TestimonialSerializer
    queryset = Testimonial.objects.all()
    permission_classes = [permissions.AllowAny]