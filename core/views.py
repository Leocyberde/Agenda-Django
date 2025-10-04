from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
import os

def landing_page(request):
    """Landing page com marketing e opções de cadastro"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    return render(request, 'core/landing_page.html')

def offline_page(request):
    """Página offline para PWA"""
    return render(request, 'core/offline.html')

def service_worker(request):
    """Serve service worker from root path for proper PWA scope"""
    # Read the service worker file
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            sw_content = f.read()
        
        # Fix HTMX detection - replace URL param check with header check
        sw_content = sw_content.replace(
            'url.searchParams.has(\'hx-request\')',
            'request.headers.get(\'HX-Request\') === \'true\''
        )
        
        # Return with proper content type for service worker
        response = HttpResponse(sw_content, content_type='application/javascript')
        response['Service-Worker-Allowed'] = '/'  # Explicitly allow root scope
        return response
        
    except FileNotFoundError:
        return HttpResponse(
            'console.error("Service worker file not found");',
            content_type='application/javascript',
            status=404
        )
