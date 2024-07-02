import django_filters
from django.utils import timezone
from django.db.models import Min
from .models import Event

class EventFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method='filter_categories')
    start_date = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    today = django_filters.BooleanFilter(method='filter_today', label='Today')
    weekend = django_filters.BooleanFilter(method='filter_weekend', label='Weekend')
    sort_by_price = django_filters.OrderingFilter(
        fields=(
            ('min_price', 'price'),
        ),
        field_labels={
            'price': 'Sort by price'
        },
        label='Sort by price'
    )
    order_by_start_date = django_filters.OrderingFilter(
        fields=(
            ('start_date', 'start_date'),
        ),
        field_labels={
            'start_date': 'Sort by start date'
        },
        label='Sort by start date'
    )

    class Meta:
        model = Event
        fields = ['categories__name', 'start_date']

    def __init__(self, *args, **kwargs):
        super(EventFilter, self).__init__(*args, **kwargs)
        self.queryset = self.queryset.annotate(min_price=Min('ticket_types__price'))
        # Apply ordering by start_date if order_by_start_date is used
        if 'order_by_start_date' in self.data:
            self.queryset = self.queryset.order_by('start_date')

    def filter_today(self, queryset, name, value):
        if value:
            today = timezone.localdate()  # Get today's date
            return queryset.filter(start_date__date=today).distinct()  # Compare only date part
        return queryset

    def filter_weekend(self, queryset, name, value):

        if value:
            today = timezone.localdate()
            saturday = today + timezone.timedelta(days=(5 - today.weekday() + 7) % 7)
            sunday = today + timezone.timedelta(days=(6 - today.weekday() + 7) % 7)
            
            return queryset.filter(start_date__date__in=[saturday, sunday]).distinct()
        return queryset
    
    def filter_categories(self, queryset, name, value):
        categories = value.split(',')
        return queryset.filter(categories__name__in=categories).distinct()
