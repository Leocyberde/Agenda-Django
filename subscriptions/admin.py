from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_type', 'status', 'start_date', 'end_date', 'days_remaining']
    list_filter = ['plan_type', 'status', 'start_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'start_date']
    
    def days_remaining(self, obj):
        return obj.days_remaining()
    days_remaining.short_description = 'Dias Restantes'
