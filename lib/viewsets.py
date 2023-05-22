from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


class BaseModelViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       mixins.ListModelMixin,
                       GenericViewSet):
    http_method_names = ('get', 'post', 'put', 'patch', 'options')
