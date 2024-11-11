import logging

logger = logging.getLogger('django.request')

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Request details log karein
        logger.info(f"Request: {request.method} {request.path} - Body: {request.body.decode('utf-8', errors='ignore')}")

        # Response ke liye request ko process karein
        response = self.get_response(request)

        # Response details log karein
        logger.info(f"Response: Status {response.status_code} - Content: {response.content.decode('utf-8', errors='ignore')}")
        
        return response
