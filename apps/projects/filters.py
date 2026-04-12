import django_filters

from .models import Project


class ProjectFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(field_name='category__id')
    tag = django_filters.CharFilter(field_name='tags__name', lookup_expr='iexact')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    min_target = django_filters.NumberFilter(field_name='total_target', lookup_expr='gte')
    max_target = django_filters.NumberFilter(field_name='total_target', lookup_expr='lte')

    class Meta:
        model = Project
        fields = ['category', 'tag', 'status', 'min_target', 'max_target']
