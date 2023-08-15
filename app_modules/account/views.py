from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import timedelta
from rest_framework import permissions, viewsets, exceptions, status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView

from .serializers import (
    CustomerRegistrationSerializer, AdminRegistrationSerializer, CustomerFrameSerializer, SubscriptionSerializer,
    UserProfileListSerializer, CustomerGroupSerializer, CuatomerListSerializer, PlanSerializer, PaymentMethodSerializer,
)
from .models import CustomerFrame, User, CustomerGroup, PaymentMethod, Plan, Subscription
from app_modules.master.models import BusinessCategory


class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_type = request.data.get('user_type')

        if user_type == 'customer':
            serializer = CustomerRegistrationSerializer(data=request.data)
        elif user_type == 'admin':
            serializer = AdminRegistrationSerializer(data=request.data)
        else:
            return Response({'user_type': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            
            customer_frame = CustomerFrame.objects.filter(customer=user).first()
            is_a_group = customer_frame.is_a_group() if customer_frame else False

            business_categories = BusinessCategory.objects.filter(
                business_category_frames__customer=user
            ).distinct()

            category_names = [category.name for category in business_categories]
            category_count = len(category_names)

            return Response(
                {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'id': user.id,
                    'is_verify': user.is_verify,
                    'is_customer': bool(user.no_of_post <= 1),
                    'is_a_group': is_a_group,
                    'category_count': category_count,
                    'category_names': category_names
                }
            )
        else:
            raise exceptions.AuthenticationFailed('Invalid email or password')

class CustomerFrameViewSet(viewsets.ModelViewSet):
    queryset = CustomerFrame.objects.all()
    serializer_class = CustomerFrameSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['group__name', 'customer__whatsapp_number', 'business_category__name', 'business_sub_category__name']
    filterset_fields = ['group__name', 'business_sub_category__name']
    
    
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    
    # def update(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
        
    #     old_group = instance.group 
        
    #     self.perform_update(serializer)
        
    #     # Get the new group from the updated instance
    #     new_group = instance.group
        
        
    

class UserProfileListApiView(viewsets.ModelViewSet):
    serializer_class = UserProfileListSerializer
    queryset = User.objects.all().exclude(is_superuser=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'whatsapp_number', 'is_verify']
    http_method_names = ['get', 'patch']
    

class CustomerGroupViewSet(viewsets.ModelViewSet):
    queryset = CustomerGroup.objects.all()
    serializer_class = CustomerGroupSerializer
    

class CustomerGroupListApiView(ListAPIView):
    pagination_class = None
    queryset  = CustomerGroup.objects.all()
    serializer_class = CustomerGroupSerializer
    
    
class CustomerFrameListApiView(ListAPIView):
    pagination_class = None
    queryset  = CustomerFrame.objects.select_related('customer', 'group').all()
    serializer_class = CustomerFrameSerializer
    
    
class CustomerListApiView(ListAPIView):
    pagination_class = None
    queryset  = User.objects.all()
    serializer_class = CuatomerListSerializer
    
    
class PlanViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset  = Plan.objects.all().order_by('-id')
    serializer_class = PlanSerializer
    
    
class PaymentMethodViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset  = PaymentMethod.objects.all().order_by('-id')
    serializer_class = PaymentMethodSerializer
    
    
class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    # queryset = Subscription.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['order_number', 'user__whatsapp_number', 'email', 'is_verify']
    
    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            return Subscription.objects.all().select_related('user', 'plan', 'payment_method')
        else:
            return Subscription.objects.filter(user=user).select_related('user', 'plan', 'payment_method')
    
    # def perform_create(self, serializer):
    #     plan = serializer.validated_data['plan']
    #     duration_in_months = plan.duration_in_months
    #     start_date = serializer.validated_data['start_date']
    #     end_date = start_date + timedelta(days=(30 * duration_in_months))  # Assuming 30 days per month
    #     serializer.save(end_date=end_date)
