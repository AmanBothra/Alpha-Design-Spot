import logging

logger = logging.getLogger('django.request')
error_logger = logging.getLogger('api_errors')

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details
        logger.info(f"Request: {request.method} {request.path} - Body: {request.body.decode('utf-8', errors='ignore')}")

        # Process the request to get the response
        response = self.get_response(request)

        # Log response details
        logger.info(f"Response: Status {response.status_code} - Content: {response.content.decode('utf-8', errors='ignore')}")

        # Log errors for status codes 400, 404, 500
        if response.status_code in {400, 404, 500}:
            error_logger.error(f"Error Response: Status {response.status_code} - Path: {request.path} - Body: {request.body.decode('utf-8', errors='ignore')} - Content: {response.content.decode('utf-8', errors='ignore')}")

        return response
