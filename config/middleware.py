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
        import time
        import uuid
        start_time = time.time()
        
        # Generate unique request ID for correlation
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id
        
        # Enhanced request logging for login endpoint
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        if request.path == '/api/auth/login':
            logger.info(f"LOGIN_REQUEST [{request_id}]: {request.method} {request.path} - IP: {client_ip} - Agent: {user_agent[:100]}")

        # Process the request to get the response
        response = self.get_response(request)
        
        # Add request ID to response headers for client correlation
        response['X-Request-ID'] = request_id
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Enhanced response logging for login endpoint
        if request.path == '/api/auth/login':
            logger.info(f"LOGIN_RESPONSE [{request_id}]: Status {response.status_code} - IP: {client_ip} - Time: {response_time:.2f}ms")

        # Enhanced error logging for all requests
        if response.status_code in {400, 404, 500, 408, 504}:  # Added timeout codes
            error_details = {
                "request_id": request_id,
                "timestamp": self._get_ist_time(),
                "error_type": response.status_code,
                "device": user_agent,
                "ip": client_ip,
                "request_url": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2),
                "headers": {
                    "user_agent": user_agent,
                    "content_type": request.headers.get('Content-Type', 'Unknown'),
                    "accept": request.headers.get('Accept', 'Unknown'),
                    "connection": request.headers.get('Connection', 'Unknown'),
                },
                "error_message": response.reason_phrase or response.content.decode('utf-8', errors='ignore')[:200],
            }
            
            # Special handling for login failures
            if request.path == '/api/auth/login' and response.status_code == 400:
                error_details["login_failure_type"] = "POTENTIAL_SERVER_TIMEOUT_OR_RESOURCE_ISSUE"
                error_details["investigation_hints"] = [
                    "Check server resource usage",
                    "Verify database connection pool",
                    "Monitor memory consumption",
                    "Check for deadlocks or slow queries"
                ]
                
            error_logger.error(f"ERROR [{request_id}]: {json.dumps(error_details, indent=2)}")

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