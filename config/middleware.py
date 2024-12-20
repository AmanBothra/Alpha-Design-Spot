import logging
import json
from datetime import datetime
import pytz
from django.conf import settings

# Create separate loggers
request_logger = logging.getLogger('api.requests')
error_logger = logging.getLogger('api.errors')

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define error status codes to monitor
        self.error_codes = {400, 401, 403, 404, 500}
        
    def __call__(self, request):
        # Only log if debug is True or it's a non-static/media request
        should_log = (
            settings.DEBUG or 
            not (request.path.startswith('/static/') or 
                 request.path.startswith('/media/'))
        )
        
        if should_log:
            # Log minimal request details
            request_logger.info(
                f"{request.method} {request.path} - "
                f"Agent: {request.headers.get('User-Agent', '')[:50]}"
            )

        response = self.get_response(request)

        # Log errors only for specific status codes
        if should_log and response.status_code in self.error_codes:
            self._log_error(request, response)

        return response

    def _log_error(self, request, response):
        """Log error details in a structured format"""
        try:
            error_details = {
                "timestamp": self._get_ist_time(),
                "status": response.status_code,
                "method": request.method,
                "path": request.path,
                "user_agent": request.headers.get('User-Agent', '')[:100],
                "ip": self._get_client_ip(request),
            }

            # Add response content for server errors only
            if response.status_code >= 500:
                error_details["error"] = response.content.decode('utf-8', 'ignore')[:200]

            # Add request body only in debug mode
            if settings.DEBUG and request.method in {'POST', 'PUT', 'PATCH'}:
                try:
                    error_details["body"] = json.loads(request.body)
                except json.JSONDecodeError:
                    error_details["body"] = request.POST.dict()
                except Exception:
                    pass

            error_logger.error(json.dumps(error_details, default=str))

        except Exception as e:
            error_logger.error(f"Logging error: {str(e)}")

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP with fallback options"""
        for header in ('X-Forwarded-For', 'X-Real-IP'):
            ip = request.headers.get(header)
            if ip:
                return ip.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')

    @staticmethod
    def _get_ist_time():
        """Get current IST time"""
        return datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')


# custom_silk.py
import gzip
from silk.middleware import SilkyMiddleware
from silk.model_factory import ResponseModelFactory

class CustomResponseModelFactory(ResponseModelFactory):
    def body(self):
        content = self.response.content
        if self.response.get('Content-Encoding') == 'gzip':
            try:
                content = gzip.decompress(content)
            except Exception:
                pass
        try:
            # Try UTF-8 first
            return True, content.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to ignore errors
            return True, content.decode('utf-8', errors='ignore')

class CustomSilkyMiddleware(SilkyMiddleware):
    def _construct_response_model(self, request, response):
        r = CustomResponseModelFactory(response).construct_response_model()
        return r