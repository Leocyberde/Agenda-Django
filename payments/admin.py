from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'status', 'plan_type', 'created_at']
    list_filter = ['status', 'plan_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'payment_id', 'preference_id']
    readonly_fields = ['created_at', 'updated_at']
