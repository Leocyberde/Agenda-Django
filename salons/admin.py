from django.contrib import admin
from .models import Salon, Service, Employee

@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'owner', 'created_at']
    list_filter = ['state', 'city', 'created_at']
    search_fields = ['name', 'owner__username', 'owner__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'salon', 'price', 'duration', 'is_active', 'created_at']
    list_filter = ['is_active', 'salon', 'created_at']
    search_fields = ['name', 'salon__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'salon', 'is_active', 'hire_date']
    list_filter = ['salon', 'is_active']
    search_fields = ['user__username', 'user__email', 'salon__name']