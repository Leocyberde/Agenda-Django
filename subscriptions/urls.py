from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.detail, name='detail'),
    path('start-trial/', views.start_trial, name='start_trial'),
]
