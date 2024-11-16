# import logging

# logger = logging.getLogger('django.request')
# error_logger = logging.getLogger('api_errors')

# class APILoggingMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Log request details
#         logger.info(f"Request: {request.method} {request.path} - Body: {request.body.decode('utf-8', errors='ignore')}")

#         # Process the request to get the response
#         response = self.get_response(request)

#         # Log response details
#         logger.info(f"Response: Status {response.status_code} - Content: {response.content.decode('utf-8', errors='ignore')}")

#         # Log errors for status codes 400, 404, 500
#         if response.status_code in {400, 404, 500}:
#             error_logger.error(f"Error Response: Status {response.status_code} - Path: {request.path} - Body: {request.body.decode('utf-8', errors='ignore')} - Content: {response.content.decode('utf-8', errors='ignore')}")

#         return response

import logging
import re
from user_agents import parse  # You'll need to install pyyaml and ua-parser

logger = logging.getLogger('django.request')
error_logger = logging.getLogger('api_errors')

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.mobile_patterns = [
            r'Android',
            r'iPhone',
            r'iPad',
            r'Windows Phone',
            r'webOS',
            r'Mobile Safari',
            r'CFNetwork'
        ]
        self.mobile_regex = re.compile('|'.join(self.mobile_patterns), re.IGNORECASE)

    def get_device_info(self, request):
        """Extract detailed device information from the request."""
        user_agent_string = request.headers.get('User-Agent', '')
        user_agent = parse(user_agent_string)
        
        device_info = {
            'device_type': 'unknown',
            'os': 'unknown',
            'os_version': 'unknown',
            'browser': 'unknown',
            'app_version': request.headers.get('X-App-Version', 'unknown')
        }

        # Get device type
        if user_agent.is_mobile:
            device_info['device_type'] = 'mobile'
        elif user_agent.is_tablet:
            device_info['device_type'] = 'tablet'
        
        # Get OS info
        if user_agent.os.family:
            device_info['os'] = user_agent.os.family
            if user_agent.os.version_string:
                device_info['os_version'] = user_agent.os.version_string

        # Get browser/app info
        if user_agent.browser.family:
            device_info['browser'] = user_agent.browser.family

        # Get device brand and model if available
        if user_agent.device.brand:
            device_info['device_brand'] = user_agent.device.brand
        if user_agent.device.model:
            device_info['device_model'] = user_agent.device.model

        return device_info

    def is_mobile_request(self, request):
        user_agent = request.headers.get('User-Agent', '')
        is_mobile_app = request.headers.get('X-Mobile-App', '')
        
        # Parse the user agent for more accurate mobile detection
        ua_info = parse(user_agent)
        return bool(ua_info.is_mobile or ua_info.is_tablet or 
                   self.mobile_regex.search(user_agent) or 
                   is_mobile_app)

    def format_log_message(self, request, response=None, device_info=None):
        """Format log message with device information."""
        log_data = {
            'method': request.method,
            'path': request.path,
            'device_info': device_info,
            'ip_address': self.get_client_ip(request),
            'headers': {
                key: value for key, value in request.headers.items()
                if key.lower() not in ['cookie', 'authorization']  # Exclude sensitive headers
            }
        }
        
        if response:
            log_data['status_code'] = response.status_code
            
        return log_data

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def __call__(self, request):
        if self.is_mobile_request(request):
            # Get device information
            device_info = self.get_device_info(request)
            
            # Log request with device info
            request_log = self.format_log_message(request, device_info=device_info)
            logger.info(f"Mobile Request: {request_log}")

            try:
                # Process the request
                response = self.get_response(request)
                
                # Log response
                response_log = self.format_log_message(request, response, device_info)
                logger.info(f"Mobile Response: {response_log}")

                # Log errors for status codes 400, 404, 500
                if response.status_code in {400, 404, 500}:
                    error_log = {
                        **response_log,
                        'request_body': request.body.decode('utf-8', errors='ignore'),
                        'response_content': response.content.decode('utf-8', errors='ignore')
                    }
                    error_logger.error(f"Mobile Error Response: {error_log}")

                return response
                
            except Exception as e:
                # Log unexpected errors
                error_logger.exception(f"Mobile Request Exception: {device_info}")
                raise

        # For web requests, just process without logging
        return self.get_response(request)