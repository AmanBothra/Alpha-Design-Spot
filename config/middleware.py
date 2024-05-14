import logging

class LogRequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django.request')

    def __call__(self, request):
        # Log the request URL
        self.logger.debug(f'Request URL: {request.get_full_path()}')
        response = self.get_response(request)
        return response
