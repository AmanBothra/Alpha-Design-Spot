from django_filters import rest_framework as filters
from django_filters.filters import OrderingFilter
from app_modules.post.models import Event, BusinessCategory

class EventFilter(filters.FilterSet):
    ordering = OrderingFilter(
        fields=(
            ('event_date', 'event_date'),
            ('name', 'name'),
        ),
    )

    class Meta:
        model = Event
        fields = ('event_date', 'name', 'ordering')
