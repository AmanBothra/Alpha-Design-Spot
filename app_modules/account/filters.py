import django_filters

from . import models
from lib import filters


class CustomerFrameFilter(filters.BaseFilter):
    mobile_number = django_filters.CharFilter(lookup_expr='contains', field_name="customer__whatsapp_number")

    class Meta:
        model = models.CustomerFrame
        fields = ('group', 'profession_type', 'display_name')

    ordering = filters.BaseOrderingFilter(
        fields=(
            ('display_name', 'display_name'),
            ('id', 'id'),
        ))
