from django.contrib import admin

from .models import Comment, Donation, Rating, Report


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'created_at', 'is_reply')
    list_filter = ('created_at',)
    search_fields = ('content', 'user__email', 'project__title')
    readonly_fields = ('created_at', 'deleted_at')

    def is_reply(self, obj):
        return obj.parent is not None
    is_reply.boolean = True


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'reporter', 'project', 'comment', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('reason', 'reporter__email')


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'amount', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('user', 'project', 'amount', 'created_at')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'value', 'created_at')
    readonly_fields = ('user', 'project', 'value', 'created_at')
