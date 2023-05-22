from django.http import JsonResponse

from rest_framework.serializers import Serializer


class CustomResponse(JsonResponse):
    def __init__(self, data=None, status=None, message=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None):

        super().__init__(None, status=status)

        if isinstance(data, Serializer):
            msg = (
                'You passed a Serializer instance as data, but '
                'probably meant to pass serialized `.data` or '
                '`.error`. representation.'
            )
            raise AssertionError(msg)

        self.data = data
        self.template_name = template_name
        self.exception = exception
        self.content_type = content_type

        if headers:
            for name, value in headers.items():
                self[name] = value
