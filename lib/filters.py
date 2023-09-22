import django_filters
from django_filters import BaseInFilter, NumberFilter
from django_filters import rest_framework as filters
from django_filters.filters import OrderingFilter


class BaseFilter(filters.FilterSet):
    order_by_field = "ordering"


class BaseOrderingFilter(OrderingFilter):
    pass


class BaseNumberInFilter(BaseInFilter, NumberFilter):
    pass


class BaseTagFilter(filters.FilterSet):
    tags = django_filters.CharFilter(method="filter_by_tags")
    tag = django_filters.NumberFilter(field_name="tags")

    def filter_by_tags(self, queryset, name, value):
        tags = value.split(',')
        return queryset.filter(tags__in=tags).distinct()
