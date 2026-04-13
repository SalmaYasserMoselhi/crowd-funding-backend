from django.contrib import admin
from django.db.models import Count, Q

from .models import Category, Project, ProjectMedia, Tag

class ProjectMediaInline(admin.TabularInline):
    readonly_fields = ('created_at',)
    model = ProjectMedia
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'total_target', 'current_donations', 'average_rating','is_cancelled', 'is_featured', 'start_time', 'end_time', 'created_at', 'updated_at')
    list_filter = ('status', 'is_featured', 'is_cancelled', 'category', 'start_time', 'end_time')
    search_fields = ('title', 'details', 'owner__username', 'owner__email')
    list_editable = ('is_featured',)
    raw_id_fields = ('owner',)
    filter_horizontal = ('tags',)
    readonly_fields = ('average_rating', 'current_donations', 'created_at', 'deleted_at')
    inlines = [ProjectMediaInline]
    actions = ['make_featured', 'unfeature']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Annotate report count — works once Dev 3's Report model exists
        # Uses GenericRelation or reverse FK depending on Dev 3's implementation
        try:
            from django.contrib.contenttypes.models import ContentType
            project_ct = ContentType.objects.get_for_model(Project)
            from apps.social.models import Report
            qs = qs.annotate(
                _report_count=Count(
                    "id",
                    filter=Q(
                        id__in=Report.objects.filter(
                            content_type=project_ct
                        ).values_list("object_id", flat=True)
                    ),
                )
            )
        except (ImportError, Exception):
            # Dev 3 hasn't shipped Report model yet
            qs = qs.annotate(
                _report_count=Count("id", filter=Q(pk__isnull=True))
            )  # always 0
        return qs
    
    def funded_percentage(self, obj):
        return f"{obj.funded_percentage}%"
    funded_percentage.short_description = 'Funded %'

    def report_count(self, obj):
        return obj._report_count
    report_count.short_description = 'Reports'
    report_count.admin_order_field = '_report_count'

    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    make_featured.short_description = 'Mark selected projects as Featured'

    def unfeature(self, request, queryset):
        queryset.update(is_featured=False)
    unfeature.short_description = 'Remove selected projects from Featured'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at', 'project_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(project_count=Count('projects'))
    
    def project_count(self, obj):
        return obj.project_count
    
    project_count.short_description = 'Projects'
    project_count.admin_order_field = 'project_count'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(project_count=Count('projects'))

    def project_count(self, obj):
        return obj.project_count
    
    project_count.short_description = 'Projects'
    project_count.admin_order_field = 'project_count'
