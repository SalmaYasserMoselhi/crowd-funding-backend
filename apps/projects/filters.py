import django_filters

from .models import Project
from django.utils import timezone


class ProjectFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(field_name='category__id', lookup_expr='exact')
    tag = django_filters.CharFilter(field_name='tags__name', lookup_expr='iexact')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    is_featured = django_filters.BooleanFilter(field_name='is_featured', lookup_expr='exact')
    is_running = django_filters.BooleanFilter(method='filter_is_running')
    min_target = django_filters.NumberFilter(field_name='total_target', lookup_expr='gte')
    max_target = django_filters.NumberFilter(field_name='total_target', lookup_expr='lte')
    creator = django_filters.CharFilter(method='filter_by_creator')
    start_date_after = django_filters.DateFilter(field_name='start_time', lookup_expr='gte')
    start_date_before = django_filters.DateFilter(field_name='start_time', lookup_expr='lte')
    end_date_after = django_filters.DateFilter(field_name='end_time', lookup_expr='gte')
    end_date_before = django_filters.DateFilter(field_name='end_time', lookup_expr='lte')

    def filter_is_running(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(start_time__lte=today, end_time__gte=today, is_cancelled=False)
        else:
            return queryset

    def filter_by_creator(self, queryset, name, value):
        if value == "me" and self.request and self.request.user.is_authenticated:
            return queryset.filter(owner=self.request.user)
        return queryset
    
    class Meta:
        model = Project
        fields = ['category', 'tag', 'status', 'is_featured', 'is_running', 'creator', 'min_target', 'max_target', 'start_date_after', 'start_date_before', 'end_date_after', 'end_date_before']
