from django_filters import rest_framework as filters
from django_filters.filters import OrderingFilter
from app_modules.post.models import Event, BusinessPost, BusinessCategory

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
        
        

class BusinessPostFilter(filters.FilterSet):
    ordering = OrderingFilter(
        fields=(
            ('profession_type', 'profession_type'),
            ('file_type', 'file_type'),
        ),
    )

    class Meta:
        model = BusinessPost
        fields = ('profession_type', 'file_type')
        
        
class BusinessCategoryFilter(filters.FilterSet):
    ordering = OrderingFilter(
        fields=(
            ('profession_type', 'profession_type'),
            ('name', 'name'),
        ),
    )

    class Meta:
        model = BusinessCategory
        fields = ('profession_type', 'name')
