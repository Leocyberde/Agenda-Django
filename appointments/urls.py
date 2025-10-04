
from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('link/<uuid:token>/', views.client_booking, name='client_booking'),
    path('booking/<uuid:token>/', views.client_booking, name='client_booking_alias'),
    path('link/<uuid:token>/confirm-reschedule/<int:appointment_id>/', views.confirm_reschedule, name='confirm_reschedule'),
    path('link/<uuid:token>/reject-reschedule/<int:appointment_id>/', views.reject_reschedule, name='reject_reschedule'),
    path('link/<uuid:token>/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('link/<uuid:token>/available-slots/', views.get_available_slots, name='get_available_slots'),
]
