from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions, viewsets, exceptions, status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView
from django.core.mail import send_mail
from django.conf import settings
from datetime import date
from django.db.models import Q

from .serializers import (
    CustomerRegistrationSerializer, AdminRegistrationSerializer, CustomerFrameSerializer, SubscriptionSerializer,
    UserProfileListSerializer, CustomerGroupSerializer, CuatomerListSerializer, PlanSerializer, PaymentMethodSerializer,
    AppVersionSerializer
)
from .models import CustomerFrame, User, CustomerGroup, PaymentMethod, Plan, Subscription, UserCode, AppVersion
from app_modules.master.models import BusinessCategory
from app_modules.post.models import Post, Category, CustomerPostFrameMapping
from lib.constants import UserConstants
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

            business_categories = BusinessCategory.objects.filter(
                business_category_frames__customer=user
            ).distinct()

            category_names = [category.name for category in business_categories]
            category_count = len(category_names)
            
            current_date = date.today()
            
            expired_subscription = Subscription.objects.filter(end_date__lt=current_date, user=user).exists()
            if expired_subscription:
                is_expired = True
                days_left = None
            else:
                is_expired = False
                if user.subscription_users.exists():
                    subscription = user.subscription_users.latest('end_date')
                    days_left = (subscription.end_date - current_date).days
                else:
                    days_left = None

            return Response(
                {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'id': user.id,
                    'is_verify': user.is_verify,
                    'is_customer': bool(user.no_of_post <= 1),
                    'is_a_group': is_a_group,
                    'is_expired': bool(is_expired),
                    'days_left': days_left, 
                    'category_count': category_count,
                    'category_names': category_names
                }
            )
        else:
            raise exceptions.ValidationError({'email': 'Invalid Email and Password'})


class CustomerFrameViewSet(viewsets.ModelViewSet):
    queryset = CustomerFrame.objects.all().order_by('-id')
    serializer_class = CustomerFrameSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['group__name', 'customer__whatsapp_number', 'business_category__name', 'business_sub_category__name']
    filterset_fields = ['group__name', 'business_sub_category__name']
    
    def perform_update(self, serializer):
        instance = serializer.instance  # Get the current instance being updated
        old_group_id = instance.group.id if instance.group else None  # Store the old group ID
        serializer.save()
        
        if old_group_id:
            new_post_group_wise = Post.objects.filter(group_id=instance.group)
            old_post_mapping = CustomerPostFrameMapping.objects.filter(
                customer=instance.customer,
                customer_frame__group=old_group_id
            )


class UserProfileListApiView(BaseModelViewSet):
    serializer_class = UserProfileListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'whatsapp_number', 'is_verify']

    def get_queryset(self):
        queryset = User.objects.all().order_by('-id')
        data = self.request.query_params.get('data', None)
        
        if data == "recent":
            queryset = queryset.filter(user_type="customer").order_by('-date_joined')[:15]
        
        if data == "admin":
            queryset = User.objects.filter(user_type="admin")
        
        if data == "active":
            queryset = User.objects.filter(user_type="customer", is_verify=True)
            
        if data == "inactive":
            queryset = User.objects.filter(user_type="customer", is_verify=False)
            
        return queryset
    

class CheckEmailExistence(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            return Response({"message": "Email exists"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            raise exceptions.ValidationError ({"Email": "Email does not exist"})
        

class SendOTP(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, *args, **kwargs):
        email = request.query_params.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise exceptions.ValidationError({"email": "User not found with this email"})

        # Send email OTP for email verification
        user_code_email, _ = user.get_or_create_user_code(
            code_type=UserConstants.FORGOTTEN_PASSWORD
        )
        subject = f"OTP for Email Verification"
        message = f"Your email verification OTP is: {user_code_email.code}"
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [
            user.email,
        ]
        send_mail(subject, message, email_from, recipient_list, fail_silently=True)

        response_data = {"message": "Email OTP sent successfully."}
        return Response(data=response_data, status=status.HTTP_200_OK)
    
    
class VerifyOTP(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        data = request.data
        email = data.get("email")
        code = int(data.get("code"))

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise exceptions.ValidationError({"email": "User not found with this email"})

        user_code = UserCode.objects.filter(
            user=user, code_type=UserConstants.FORGOTTEN_PASSWORD
        ).first()
        if not user_code or code != user_code.code:
            raise exceptions.ValidationError({"core": "Invalid Code"})

        user.is_email_verify = True
        user.save()
        user_code.delete()
        
        return Response({"message": "Email verification is successfully completed",},status=status.HTTP_200_OK)

class SetNewPassword(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if new_password != confirm_password:
            raise exceptions.ValidationError({"password": "Passwords do not match"})

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            raise exceptions.ValidationError({"email": "User not found"})
        
    
class CustomerGroupViewSet(viewsets.ModelViewSet):
    queryset = CustomerGroup.objects.all()
    serializer_class = CustomerGroupSerializer
    

class CustomerGroupListApiView(ListAPIView):
    pagination_class = None
    queryset  = CustomerGroup.objects.all()
    serializer_class = CustomerGroupSerializer
    
    
class CustomerFrameListApiView(ListAPIView):
    pagination_class = None
    queryset  = CustomerFrame.objects.select_related('customer', 'group').all().order_by('-id')
    serializer_class = CustomerFrameSerializer
    
    
class CustomerListApiView(ListAPIView):
    pagination_class = None
    queryset  = User.objects.all().order_by('-id')
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


class AppVersionViewSet(BaseModelViewSet):
    serializer_class = AppVersionSerializer
    queryset = AppVersion.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['app_type']

## Dashboard API
###------------------------------------------

class DashboardApi(APIView):
    
    def get(self, request, *args, **kwargs):
        total_customer_count = User.objects.filter(user_type="customer", no_of_post__lte=1).count()
        total_post_count = Post.objects.select_related('event', 'group').count()
        total_resaller_count = User.objects.filter(no_of_post__gt=1, user_type="customer").count()
        total_category_count = Category.objects.filter(sub_category__isnull=True).count()
        total_sub_category_count = Category.objects.filter(sub_category__isnull=False).count()
        
        data = {
            'total_customer_count': total_customer_count,
            'total_post_count': total_post_count,
            'total_resaller_count': total_resaller_count,
            'total_category_count': total_category_count,
            'total_sub_category_count': total_sub_category_count 
        }
        
        return Response(data)