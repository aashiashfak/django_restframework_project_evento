import django_filters
from .models import Event


class EventFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='ticket_types__price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='ticket_types__price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='categories__name', lookup_expr='icontains')
    start_date = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')

    class Meta:
        model = Event
        fields = ['ticket_types__price', 'categories__name', 'start_date', 'end_date']