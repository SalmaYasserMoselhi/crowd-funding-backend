from django.contrib import admin

from .models import Category, Project, ProjectMedia, Tag


class ProjectMediaInline(admin.TabularInline):
    readonly_fields = ('created_at',)
    model = ProjectMedia
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'total_target', 'current_donations', 'average_rating', 'is_featured', 'start_time', 'end_time', 'created_at', 'updated_at')
    list_filter = ('status', 'is_featured', 'is_cancelled', 'category', 'start_time')
    search_fields = ('title', 'details', 'owner__username', 'owner__email')
    list_editable = ('is_featured',)
    raw_id_fields = ('owner',)
    filter_horizontal = ('tags',)
    inlines = [ProjectMediaInline]
    readonly_fields = ('average_rating', 'current_donations', 'created_at', 'deleted_at')
    actions = ['make_featured', 'unfeature']
    date_hierarchy = 'created_at'

    def funded_percentage(self, obj):
        return f"{obj.funded_percentage}%"
    funded_percentage.short_description = 'Funded %'

    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    make_featured.short_description = 'Mark selected projects as Featured'

    def unfeature(self, request, queryset):
        queryset.update(is_featured=False)
    unfeature.short_description = 'Remove selected projects from Featured'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def project_count(self, obj):
        return obj.projects.count()
    
    project_count.short_description = 'Projects'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
