from rest_framework.response import Response
from rest_framework.views import APIView
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
from lib.viewsets import BaseModelViewSet


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

            return Response(
                {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'id': user.id,
                    'is_verify': user.is_verify,
                    'is_customer': bool(user.no_of_post <=1),
                    'is_a_group': is_a_group,
                }
            )
        else:
            raise exceptions.AuthenticationFailed('Invalid email or password')
        

class CustomerFrameViewSet(viewsets.ModelViewSet):
    queryset = CustomerFrame.objects.all()
    serializer_class = CustomerFrameSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['group__name', 'customer__whatsapp_number']
    filterset_fields = ['group__name']
    

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
    queryset = Subscription.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['order_number', 'user__whatsapp_number', 'email', 'whatsapp_number', 'is_verify']