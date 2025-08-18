from datetime import date, timedelta
from django.db.models import Prefetch, F, Value, BooleanField, Case, When, Q, ExpressionWrapper

from django.db.models.functions import Coalesce
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.forms import IntegerField
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets, exceptions, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from app_modules.post.models import Post, Category
from app_modules.post.serializers import BusinessCategorySerializer
from lib.constants import UserConstants
from lib.viewsets import BaseModelViewSet
from .filters import CustomerFrameFilter
from .models import CustomerFrame, User, CustomerGroup, PaymentMethod, Plan, Subscription, UserCode
from .serializers import (
    CustomerRegistrationSerializer, AdminRegistrationSerializer, CustomerFrameSerializer, SubscriptionSerializer,
    UserProfileListSerializer, CustomerGroupSerializer, CuatomerListSerializer, PlanSerializer, PaymentMethodSerializer,
)


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
        try:
            # Input validation
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email or not password:
                # Log this as a client error, not server issue
                import logging
                logger = logging.getLogger('django.request')
                request_id = getattr(request, 'request_id', 'unknown')
                logger.warning(f"LOGIN_VALIDATION_ERROR [{request_id}]: Missing email or password - Email: {'***' if email else 'missing'}, Password: {'***' if password else 'missing'}")
                
                return Response({
                    'error': 'Email and password are required',
                    'error_code': 'MISSING_CREDENTIALS',
                    'request_id': request_id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check user existence and status
            user_exists = User.objects.filter(email=email).first()
            request_id = getattr(request, 'request_id', 'unknown')
            
            if user_exists and not user_exists.is_active:
                return Response({
                    'error': 'This account has been deactivated. Please contact support for assistance.',
                    'error_code': 'ACCOUNT_DEACTIVATED',
                    'request_id': request_id
                }, status=status.HTTP_400_BAD_REQUEST)

            # Authenticate user
            user = authenticate(request, username=email, password=password)
            if user is None:
                return Response({
                    'error': 'Invalid Email and Password',
                    'error_code': 'INVALID_CREDENTIALS',
                    'request_id': request_id
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            current_date = timezone.now().date()

            # Optimized user data query with timeout protection
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout = '15s'")  # 15 second timeout for this query
                
                user_data = (
                    User.objects.filter(id=user.id)
                    .annotate(
                        is_customer=Case(
                            When(no_of_post__lte=1, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField()
                        ),
                        is_expired=Case(
                            When(
                                Q(subscription_users__end_date__lt=current_date) | Q(subscription_users__isnull=True), 
                                then=Value(True)
                            ),
                            default=Value(False),
                            output_field=BooleanField()
                        ),
                    )
                    .prefetch_related(
                        Prefetch(
                            'customer_frame',
                            queryset=CustomerFrame.objects.select_related('business_category').order_by('business_category__id').distinct(),
                            to_attr='frames'
                        )
                    )
                    .first()
                )

            # Calculate subscription info
            subscription = user.subscription_users.first()
            days_left = (subscription.end_date - current_date).days if subscription and subscription.end_date >= current_date else 0

            # Process profession types with error handling
            profession_types = {}
            try:
                for frame in user_data.frames:
                    category = frame.business_category
                    if category:
                        profession_type = frame.profession_type
                        thumbnail_url = request.build_absolute_uri(category.thumbnail.url) if category.thumbnail else None
                        category_data = {
                            "id": category.id,
                            "business_sub_category_name": category.name,
                            "file": thumbnail_url
                        }
                        if profession_type not in profession_types:
                            profession_types[profession_type] = {"name": profession_type, "categories": []}
                        profession_types[profession_type]["categories"].append(category_data)
            except Exception:
                profession_types = {}  # Fallback to empty if processing fails

            profession_types_list = list(profession_types.values())

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'id': user.id,
                'is_verify': user.is_verify,
                'mobile_number': user.whatsapp_number,
                'is_customer': user_data.is_customer,
                'is_a_group': bool(user_data.frames and len(user_data.frames) > 0 and user_data.frames[0].is_a_group()),
                'is_expired': user_data.is_expired,
                'days_left': days_left,
                'profession_types': profession_types_list,
                'login_time': timezone.now().isoformat()  # For debugging
            })

        except Exception as e:
            # Comprehensive error handling
            # Import DEBUG from settings
            from django.conf import settings
            return Response({
                'error': 'Login service temporarily unavailable. Please try again.',
                'error_code': 'SERVICE_ERROR',
                'debug_info': str(e) if settings.DEBUG else None,
                'request_id': getattr(request, 'request_id', None)  # Include request ID for correlation
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

       
class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user

            # Retrieve all refresh tokens and access tokens for the user
            refresh_tokens = RefreshToken.objects.filter(user=user)
            access_tokens = AccessToken.objects.filter(user=user)

            # Blacklist each refresh token
            for r_token in refresh_tokens:
                BlacklistedToken.objects.get_or_create(token=r_token)
            
            # Blacklist each access token
            for a_token in access_tokens:
                BlacklistedToken.objects.get_or_create(token=a_token)

            return Response({"details": "Logged Out"})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomerFrameViewSet(viewsets.ModelViewSet):
    queryset = CustomerFrame.objects.select_related(
        'customer', 'business_category', 'group').all().order_by('-id')
    serializer_class = CustomerFrameSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        'group__name', 'customer__whatsapp_number', 'display_name'
    ]
    filterset_fields = ['group__name', 'profession_type']
    filterset_class = CustomerFrameFilter


class UserProfileListApiView(BaseModelViewSet):
    serializer_class = UserProfileListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        'first_name', 'last_name', 'email', 'whatsapp_number', 'is_verify'
        ]

    def get_queryset(self):
        data = self.request.query_params.get('data', None)
        today_date = date.today()
        queryset = User.objects.all().order_by('-id')

        if data == "recent":
            queryset = queryset.filter(
                user_type="customer",
                is_verify=False,
                is_active=True,
                created__date=today_date
            )
        elif data == "admin":
            queryset = queryset.filter(
                user_type="admin", 
                is_active=True
            )
        elif data == "active":
            queryset = queryset.filter(
                user_type="customer", 
                is_verify=True, 
                is_active=True
            )
        elif data == "inactive":
            queryset = queryset.filter(
                user_type="customer", 
                is_verify=False, 
                is_active=True
            )
        # Remove "delete" filter since there are no deleted users anymore

        return queryset

    def destroy(self, request, *args, **kwargs):
        from django.db import transaction
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

        try:
            with transaction.atomic():
                # Get the user instance
                instance = self.get_object()
                user_id = instance.id

                # Delete all outstanding tokens for this user
                # OutstandingToken.objects.filter(user=instance).delete()

                # Note: BlacklistedToken entries will be automatically deleted due to CASCADE
                # relationship with OutstandingToken

                # Now perform the user deletion
                instance.delete()

                # Verify deletion was successful
                user_still_exists = User.objects.filter(id=user_id).exists()

                if user_still_exists:
                    return Response({
                        "success": False,
                        "status": False,
                        "message": "User deletion failed"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({
                    "success": True,
                    "status": True,
                    "message": "User permanently deleted from database"
                }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                "success": False,
                "status": False,
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "status": False,
                "message": f"Failed to delete user: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckEmailExistence(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            return Response({"message": "Email exists"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            raise exceptions.ValidationError({"Email": "Email does not exist"})


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
        subject = "OTP for Email Verification"
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

        return Response({"message": "Email verification is successfully completed", }, status=status.HTTP_200_OK)


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
    queryset = CustomerGroup.objects.all().order_by('name')
    serializer_class = CustomerGroupSerializer


class CustomerGroupListApiView(ListAPIView):
    pagination_class = None
    queryset = CustomerGroup.objects.all().order_by('name')
    serializer_class = CustomerGroupSerializer


class CustomerFrameListApiView(ListAPIView):
    pagination_class = None
    serializer_class = CustomerFrameSerializer
    queryset = CustomerFrame.objects.select_related(
        'customer', 'business_category', 'group').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        'customer__whatsapp_number'
    ]


class CustomerListApiView(ListAPIView):
    pagination_class = None
    queryset = User.objects.all().order_by('-id')
    serializer_class = CuatomerListSerializer


class PlanViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = Plan.objects.all().order_by('-id')
    serializer_class = PlanSerializer


class PaymentMethodViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = PaymentMethod.objects.all().order_by('-id')
    serializer_class = PaymentMethodSerializer


class SubscriptionViewSet(BaseModelViewSet):
    serializer_class = SubscriptionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        'order_number', 'user__whatsapp_number', 'frame__display_name', 'transaction_number',
        'payment_method__name', 'plan__name'
    ]

    def get_queryset(self):
        user = self.request.user
        current_date = timezone.now().date()
        queryset = Subscription.objects.all().select_related('user', 'plan', 'payment_method')

        # Apply filters based on query parameters
        days_until_expiry = self.request.query_params.get('days_until_expiry')
        expired = self.request.query_params.get('expired')
        active = self.request.query_params.get('active')

        if days_until_expiry:
            next_10_days = current_date + timedelta(days=10)
            queryset = queryset.filter(end_date__gte=current_date, end_date__lte=next_10_days)

        if expired == 'true':
            queryset = queryset.filter(end_date__lt=current_date)

        if active == 'true':
            queryset = queryset.filter(end_date__gte=current_date)

        if not user.is_staff:
            queryset = queryset.filter(user=user)

        return queryset


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
            'total_sub_category_count': total_sub_category_count,
            # 'total_active_customer_count':
            # 'total_inactive_customer_count': 
            # "expired_customer_subscription_count"

        }

        return Response(data)


class MobileDashboardApi(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
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

        # Retrieve the categories assigned to the user's CustomerFrame objects
        user_customer_frames = CustomerFrame.objects.filter(customer=user)
        assigned_business_categories = []
        for frame in user_customer_frames:
            if frame.business_category:
                assigned_business_categories.append(frame.business_category)

        # Serialize the assigned business categories
        category_serializer = BusinessCategorySerializer(assigned_business_categories, many=True)

        data = {
            'id': user.id,
            'is_verify': user.is_verify,
            'is_expired': is_expired,
            'days_left': days_left,
            'assigned_business_categories': category_serializer.data,
        }

        return Response(data)


class ChangeUserPasswordServiceApiView(APIView):
    def post(self, request, *args, **kwargs):
        new_password = request.data.get('new_password')

        users_to_change_password = User.objects.exclude(user_type='admin')
        for user in users_to_change_password:
            user.set_password(new_password)
            user.save()

        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    """Health check endpoint for monitoring server status"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        import time
        from django.db import connection
        from django.core.cache import cache
        
        start_time = time.time()
        health_data = {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "server": "online",
            "checks": {}
        }
        
        try:
            # Database check
            db_start = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_data["checks"]["database"] = {
                "status": "healthy",
                "response_time_ms": round((time.time() - db_start) * 1000, 2)
            }
        except Exception as e:
            health_data["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["status"] = "unhealthy"
        
        try:
            # Cache check
            cache_start = time.time()
            cache.set("health_check", "ok", 30)
            cache_value = cache.get("health_check")
            health_data["checks"]["cache"] = {
                "status": "healthy" if cache_value == "ok" else "unhealthy",
                "response_time_ms": round((time.time() - cache_start) * 1000, 2)
            }
        except Exception as e:
            health_data["checks"]["cache"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
        
        # Overall response time
        health_data["total_response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        status_code = status.HTTP_200_OK if health_data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(health_data, status=status_code)


class LoginDiagnosticsView(APIView):
    """Login diagnostics endpoint for debugging"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Diagnose login issues without actually authenticating"""
        diagnostics = {
            "request_id": getattr(request, 'request_id', 'unknown'),
            "timestamp": timezone.now().isoformat(),
            "request_data_received": {},
            "validation_results": {},
            "user_status": {},
            "system_status": "healthy"
        }
        
        # Check what data was received
        email = request.data.get('email')
        password = request.data.get('password')
        
        diagnostics["request_data_received"] = {
            "has_email": bool(email),
            "has_password": bool(password),
            "email_format": "valid" if email and "@" in email else "invalid" if email else "missing",
            "content_type": request.headers.get('Content-Type', 'unknown'),
            "request_size": len(request.body) if hasattr(request, 'body') else 0
        }
        
        # Basic validation
        if not email or not password:
            diagnostics["validation_results"]["missing_fields"] = True
            diagnostics["validation_results"]["missing"] = []
            if not email:
                diagnostics["validation_results"]["missing"].append("email")
            if not password:
                diagnostics["validation_results"]["missing"].append("password")
        else:
            diagnostics["validation_results"]["missing_fields"] = False
            
            # Check user existence (without revealing too much)
            if email:
                try:
                    user_exists = User.objects.filter(email=email).first()
                    if user_exists:
                        diagnostics["user_status"] = {
                            "exists": True,
                            "is_active": user_exists.is_active,
                            "is_verified": user_exists.is_verify,
                            "user_type": user_exists.user_type
                        }
                    else:
                        diagnostics["user_status"] = {"exists": False}
                except Exception as e:
                    diagnostics["user_status"] = {"error": "database_error"}
                    diagnostics["system_status"] = "database_issue"
        
        return Response(diagnostics)


class ServerStatsView(APIView):
    """Server statistics endpoint for monitoring"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        import psutil
        from django.db import connections
        
        try:
            # System stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Database connection pool stats
            db_stats = {}
            for conn_name in connections:
                conn = connections[conn_name]
                if hasattr(conn, 'pool'):
                    pool = conn.pool
                    db_stats[conn_name] = {
                        "pool_size": getattr(pool, '_pool', {}).qsize() if hasattr(pool, '_pool') else 0,
                        "overflow": getattr(pool, '_overflow', 0),
                        "checked_in": getattr(pool, '_checked_in', 0)
                    }
            
            stats = {
                "timestamp": timezone.now().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": round(memory.available / 1024 / 1024, 2),
                    "disk_percent": round((disk.total - disk.free) / disk.total * 100, 2),
                    "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
                },
                "database": db_stats,
                "active_users_count": User.objects.filter(is_active=True).count()
            }
            
            return Response(stats)
            
        except Exception as e:
            return Response({
                "error": "Could not retrieve stats",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
