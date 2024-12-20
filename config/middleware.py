import logging
import json
from datetime import datetime
import pytz

logger = logging.getLogger('django.request')
error_logger = logging.getLogger('api_errors')

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details
        logger.info(f"Request: {request.method} {request.path} - Headers: {dict(request.headers)}")

        # Process the request to get the response
        response = self.get_response(request)

        # Log response details
        logger.info(f"Response: Status {response.status_code} - Path: {request.path}")

        # Log errors for specific status codes
        if response.status_code in {400, 404, 500}:
            error_details = {
                "timestamp": self._get_ist_time(),
                "error_type": response.status_code,
                "device": request.headers.get('User-Agent', 'Unknown'),
                "ip": self._get_client_ip(request),
                "request_url": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "headers": dict(request.headers),
                "error_message": response.reason_phrase or response.content.decode('utf-8', errors='ignore')[:100],  # Concise message
            }
            error_logger.error(json.dumps(error_details))

        return response

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP address."""
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')

    @staticmethod
    def _get_ist_time():
        """Get the current time in IST."""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')