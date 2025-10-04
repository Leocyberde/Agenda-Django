from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<int:plan_id>/', views.checkout, name='checkout'),
    path('gerar-pix/<int:plan_id>/', views.gerar_pix, name='gerar_pix'),
    path('verificar-pagamento/<int:payment_id>/', views.verificar_pagamento, name='verificar_pagamento'),
    path('success/', views.payment_success, name='success'),
    path('failure/', views.payment_failure, name='failure'),
    path('webhook/', views.webhook, name='webhook'),
]
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<int:plan_id>/', views.checkout, name='checkout'),
    path('gerar-pix/<int:plan_id>/', views.gerar_pix, name='gerar_pix'),
    path('verificar-pagamento/<int:payment_id>/', views.verificar_pagamento, name='verificar_pagamento'),
    path('success/', views.payment_success, name='success'),
    path('failure/', views.payment_failure, name='failure'),
    path('webhook/', views.webhook, name='webhook'),
    path('aprovar-pagamento/<int:payment_id>/', views.aprovar_pagamento_manual, name='aprovar_pagamento_manual'),
]
