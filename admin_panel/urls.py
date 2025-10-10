from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('owners/', views.manage_owners, name='manage_owners'),
    path('owners/<int:owner_id>/', views.owner_detail, name='owner_detail'),
    path('owners/<int:owner_id>/subscription/', views.manage_subscription, name='manage_subscription'),
    path('reports/', views.subscription_reports, name='subscription_reports'),
    # URLs para gerenciamento de produtos
    # path("products/", views.manage_products, name="manage_products"),
    # path("products/create/", views.create_product, name="create_product"),
    # path("products/<int:product_id>/edit/", views.edit_product, name="edit_product"),
    # path("products/<int:product_id>/delete/", views.delete_product, name="delete_product"),
    # path("products/<int:product_id>/toggle/", views.toggle_product_status, name="toggle_product_status"),
    # URLs para gerenciamento de preços dos planos
    path('plan-pricing/', views.manage_plan_pricing, name='manage_plan_pricing'),
    path('plan-pricing/<int:plan_id>/edit/', views.edit_plan_pricing, name='edit_plan_pricing'),
    # Cashback tracking URLs
    # path("track-click/<int:product_id>/", views.track_affiliate_click, name="track_affiliate_click"),
    # path("webhook/purchase-confirmation/", views.webhook_purchase_confirmation, name="webhook_purchase_confirmation"),
    # path("cashback/dashboard/", views.user_cashback_dashboard, name="cashback_dashboard"),
    # path("cashback/request-payment/", views.request_cashback_payment, name="request_cashback_payment"),
    # path("cashback/admin/", views.admin_cashback_management, name="admin_cashback_management"),
]