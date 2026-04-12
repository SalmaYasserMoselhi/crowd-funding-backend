from django.contrib import admin

from .models import ActivationToken, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_active', 'date_joined')
    list_filter = ('is_active', 'country')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('date_joined', 'created_at', 'deleted_at')


@admin.register(ActivationToken)
class ActivationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at')
    readonly_fields = ('token', 'created_at')
