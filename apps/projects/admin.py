from django.contrib import admin

from .models import Category, Project, ProjectMedia, Tag


class ProjectMediaInline(admin.TabularInline):
    model = ProjectMedia
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'total_target', 'current_donations', 'average_rating', 'is_featured')
    list_filter = ('status', 'is_featured', 'category', 'start_time')
    search_fields = ('title', 'details', 'owner__email', 'tags__name')
    inlines = [ProjectMediaInline]
    readonly_fields = ('average_rating', 'current_donations', 'created_at', 'deleted_at')
    actions = ['make_featured', 'unfeature']

    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    make_featured.short_description = 'Mark selected projects as Featured'

    def unfeature(self, request, queryset):
        queryset.update(is_featured=False)
    unfeature.short_description = 'Remove selected projects from Featured'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
