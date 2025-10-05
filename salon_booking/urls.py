"""
URL configuration for salon_booking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.shortcuts import redirect
from core.views import service_worker
import json
import os

def manifest_view(request):
    """Serve the manifest.json file"""
    try:
        manifest_path = os.path.join(settings.BASE_DIR, 'manifest.json')
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        return JsonResponse(manifest_data, content_type='application/manifest+json')
    except FileNotFoundError:
        return JsonResponse({'error': 'Manifest not found'}, status=404)

def home_redirect(request):
    """Redireciona a página inicial para o dashboard apropriado"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return redirect('core:landing_page')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('salons/', include('salons.urls')),
    path('appointments/', include('appointments.urls')),
    path('subscriptions/', include('subscriptions.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('payments/', include('payments.urls')),
    path('manifest.json', manifest_view, name='manifest'),
    path('sw.js', service_worker, name='service_worker'),  # Service worker from root for proper PWA scope
    path('', include('core.urls')),
]

# Servir arquivos de mídia durante desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
