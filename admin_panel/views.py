# Views para gerenciar preços dos planos e produtos
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.db import models, transaction
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Product, PlanPricing, PurchaseTracking, CashbackTransaction, UserCashbackBalance
from accounts.models import UserProfile
from salons.models import Salon
from subscriptions.models import Subscription
from appointments.models import Appointment
from decimal import Decimal
import uuid
import json
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def is_admin_user(user):
    """Verifica se o usuário é superusuário (administrador)"""
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Dashboard principal do administrador"""
    # Estatísticas gerais
    total_owners = UserProfile.objects.filter(user_type='owner').count()
    total_clients = UserProfile.objects.filter(user_type='client').count()
    total_salons = Salon.objects.count()
    total_appointments = Appointment.objects.count()

    # Assinaturas ativas e expiradas
    active_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__gt=timezone.now()
    ).count()

    expired_subscriptions = Subscription.objects.filter(
        Q(status='expired') | Q(end_date__lte=timezone.now())
    ).count()

    # Assinaturas expirando em 3 dias
    expiring_soon = Subscription.objects.filter(
        status='active',
        end_date__lte=timezone.now() + timedelta(days=3),
        end_date__gt=timezone.now()
    ).count()

    # Últimos comerciantes cadastrados
    recent_owners = UserProfile.objects.filter(
        user_type='owner'
    ).select_related('user').order_by('-created_at')[:5]

    # Comerciantes com assinaturas expirando
    expiring_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__lte=timezone.now() + timedelta(days=7),
        end_date__gt=timezone.now()
    ).select_related('user').order_by('end_date')[:10]

    context = {
        'total_owners': total_owners,
        'total_clients': total_clients,
        'total_salons': total_salons,
        'total_appointments': total_appointments,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'expiring_soon': expiring_soon,
        'recent_owners': recent_owners,
        'expiring_subscriptions': expiring_subscriptions,
    }

    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin_user)
def manage_owners(request):
    """Gerenciar comerciantes"""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    owners = UserProfile.objects.filter(user_type='owner').select_related('user')

    if search:
        owners = owners.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )

    if status_filter == 'active':
        owners = owners.filter(user__subscription__status='active')
    elif status_filter == 'expired':
        owners = owners.filter(
            Q(user__subscription__status='expired') |
            Q(user__subscription__end_date__lte=timezone.now())
        )

    owners = owners.order_by('-created_at')

    return render(request, 'admin_panel/manage_owners.html', {
        'owners': owners,
        'search': search,
        'status_filter': status_filter,
    })

@login_required
@user_passes_test(is_admin_user)
def owner_detail(request, owner_id):
    """Detalhes de um comerciante específico"""
    owner = get_object_or_404(UserProfile, id=owner_id, user_type='owner')

    # Informações do salão
    salon = getattr(owner.user, 'salon', None)

    # Assinatura
    subscription = getattr(owner.user, 'subscription', None)

    # Estatísticas
    if salon:
        total_services = salon.services.filter(is_active=True).count()
        total_appointments = Appointment.objects.filter(salon=salon).count()
        pending_appointments = Appointment.objects.filter(
            salon=salon,
            status='scheduled'
        ).count()
    else:
        total_services = 0
        total_appointments = 0
        pending_appointments = 0

    return render(request, 'admin_panel/owner_detail.html', {
        'owner': owner,
        'salon': salon,
        'subscription': subscription,
        'total_services': total_services,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
    })

@login_required
@user_passes_test(is_admin_user)
def manage_subscription(request, owner_id):
    """Gerenciar assinatura de um comerciante"""
    owner = get_object_or_404(UserProfile, id=owner_id, user_type='owner')
    subscription, created = Subscription.objects.get_or_create(
        user=owner.user,
        defaults={'plan_type': 'trial_10'}
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'renew':
            plan_type = request.POST.get('plan_type')
            if plan_type in ['trial_10', 'vip_30']:
                subscription.renew_subscription(plan_type)
                messages.success(request, f'Assinatura renovada para {subscription.get_plan_type_display()}!')

        elif action == 'extend':
            days = int(request.POST.get('days', 0))
            if days > 0:
                subscription.end_date += timedelta(days=days)
                subscription.save()
                messages.success(request, f'Assinatura estendida por {days} dias!')

        elif action == 'cancel':
            subscription.status = 'cancelled'
            subscription.save()
            messages.success(request, 'Assinatura cancelada!')

        elif action == 'activate':
            subscription.status = 'active'
            subscription.save()
            messages.success(request, 'Assinatura ativada!')

        elif action == 'fix_to_vip':
            subscription.renew_subscription('vip_30')
            messages.success(request, 'Assinatura corrigida para VIP 30 dias!')

        return redirect('admin_panel:owner_detail', owner_id=owner.id)

    return render(request, 'admin_panel/manage_subscription.html', {
        'owner': owner,
        'subscription': subscription,
    })

@login_required
@user_passes_test(is_admin_user)
def subscription_reports(request):
    """Relatórios de assinaturas"""
    # Assinaturas por tipo
    trial_count = Subscription.objects.filter(plan_type='trial_10').count()
    vip_count = Subscription.objects.filter(plan_type='vip_30').count()

    # Assinaturas por status
    active_count = Subscription.objects.filter(status='active').count()
    expired_count = Subscription.objects.filter(status='expired').count()
    cancelled_count = Subscription.objects.filter(status='cancelled').count()

    # Receita estimada (simulação)
    monthly_revenue = vip_count * 50  # Assumindo R$ 50 por plano VIP

    # Assinaturas expirando nos próximos 7 dias
    expiring_soon = Subscription.objects.filter(
        status='active',
        end_date__lte=timezone.now() + timedelta(days=7),
        end_date__gt=timezone.now()
    ).select_related('user').order_by('end_date')

    return render(request, 'admin_panel/subscription_reports.html', {
        'trial_count': trial_count,
        'vip_count': vip_count,
        'active_count': active_count,
        'expired_count': expired_count,
        'cancelled_count': cancelled_count,
        'monthly_revenue': monthly_revenue,
        'expiring_soon': expiring_soon,
    })


@login_required
@user_passes_test(is_admin_user)
def manage_products(request):
    """Gerenciar produtos da loja"""
    search = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    featured_filter = request.GET.get('featured', '')

    products = Product.objects.all()

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(brand__icontains=search) |
            Q(description__icontains=search)
        )

    if category_filter:
        products = products.filter(category=category_filter)

    if featured_filter == 'yes':
        products = products.filter(is_featured=True)
    elif featured_filter == 'no':
        products = products.filter(is_featured=False)

    products = products.order_by('-is_featured', '-created_at')

    # Paginação
    paginator = Paginator(products, 12)  # 12 produtos por página
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    # Categorias para o filtro
    categories = Product.CATEGORY_CHOICES

    return render(request, 'admin_panel/manage_products.html', {
        'products': products_page,
        'search': search,
        'category_filter': category_filter,
        'featured_filter': featured_filter,
        'categories': categories,
    })


@login_required
@user_passes_test(is_admin_user)
def create_product(request):
    """Criar novo produto"""
    if request.method == 'POST':
        try:
            # Validar cashback percentage
            cashback_percentage = Decimal(request.POST.get('cashback_percentage', '0.00'))
            if cashback_percentage < 0 or cashback_percentage > 100:
                messages.error(request, 'Percentual de cashback deve estar entre 0% e 100%.')
                return redirect('admin_panel:create_product')

            product = Product(
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                category=request.POST.get('category'),
                brand=request.POST.get('brand'),
                price=request.POST.get('price'),
                affiliate_link=request.POST.get('affiliate_link'),
                image_url=request.POST.get('image_url', ''),
                cashback_percentage=cashback_percentage,
                is_featured=request.POST.get('is_featured') == 'on',
                is_active=request.POST.get('is_active') == 'on'
            )
            product.full_clean()  # Validate model constraints
            product.save()
            messages.success(request, 'Produto criado com sucesso!')
            return redirect('admin_panel:manage_products')
        except ValidationError as e:
            messages.error(request, f'Erro de validação: {str(e)}')
        except Exception as e:
            messages.error(request, f'Erro ao criar produto: {str(e)}')

    categories = Product.CATEGORY_CHOICES
    return render(request, 'admin_panel/create_product.html', {
        'categories': categories,
    })


@login_required
@user_passes_test(is_admin_user)
def edit_product(request, product_id):
    """Editar produto"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        try:
            # Validar cashback percentage
            cashback_percentage = Decimal(request.POST.get('cashback_percentage', '0.00'))
            if cashback_percentage < 0 or cashback_percentage > 100:
                messages.error(request, 'Percentual de cashback deve estar entre 0% e 100%.')
                return redirect('admin_panel:edit_product', product_id=product.id)

            product.name = request.POST.get('name')
            product.description = request.POST.get('description')
            product.category = request.POST.get('category')
            product.brand = request.POST.get('brand')
            product.price = request.POST.get('price')
            product.affiliate_link = request.POST.get('affiliate_link')
            product.image_url = request.POST.get('image_url', '')
            product.cashback_percentage = cashback_percentage
            product.is_featured = request.POST.get('is_featured') == 'on'
            product.is_active = request.POST.get('is_active') == 'on'
            product.full_clean()  # Validate model constraints
            product.save()
            messages.success(request, 'Produto atualizado com sucesso!')
            return redirect('admin_panel:manage_products')
        except ValidationError as e:
            messages.error(request, f'Erro de validação: {str(e)}')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar produto: {str(e)}')

    categories = Product.CATEGORY_CHOICES
    return render(request, 'admin_panel/edit_product.html', {
        'product': product,
        'categories': categories,
    })


@login_required
@user_passes_test(is_admin_user)
def delete_product(request, product_id):
    """Deletar produto"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Produto "{product_name}" foi removido com sucesso!')
        return redirect('admin_panel:manage_products')

    return render(request, 'admin_panel/delete_product.html', {
        'product': product,
    })


@login_required
@user_passes_test(is_admin_user)
def toggle_product_status(request, product_id):
    """Alternar status ativo/inativo do produto"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product.is_active = not product.is_active
        product.save()

        status = 'ativado' if product.is_active else 'desativado'
        messages.success(request, f'Produto "{product.name}" foi {status}!')

    return redirect('admin_panel:manage_products')


@login_required
@user_passes_test(is_admin_user)
def manage_plan_pricing(request):
    """Gerenciar preços dos planos"""
    plans = PlanPricing.objects.all().order_by('plan_type')

    # Se não existirem planos, criar os padrões
    if not plans.exists():
        PlanPricing.objects.create(
            plan_type='trial_10',
            price=0.00,
            description='Plano gratuito de teste por 10 dias'
        )
        PlanPricing.objects.create(
            plan_type='vip_30',
            price=49.90,
            description='Plano premium com todos os recursos por 30 dias'
        )
        plans = PlanPricing.objects.all().order_by('plan_type')

    return render(request, 'admin_panel/manage_plan_pricing.html', {
        'plans': plans,
    })


@login_required
@user_passes_test(is_admin_user)
def edit_plan_pricing(request, plan_id):
    """Editar preço de um plano"""
    plan = get_object_or_404(PlanPricing, id=plan_id)

    if request.method == 'POST':
        try:
            plan.price = request.POST.get('price')
            plan.description = request.POST.get('description', '')
            plan.is_active = request.POST.get('is_active') == 'on'
            plan.save()
            messages.success(request, f'Preço do {plan.get_plan_type_display()} atualizado com sucesso!')
            return redirect('admin_panel:manage_plan_pricing')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar preço: {str(e)}')

    return render(request, 'admin_panel/edit_plan_pricing.html', {
        'plan': plan,
    })


# --- Novas Views para Rastreamento de Afiliados e Cashback ---

@require_http_methods(["GET"])
def track_affiliate_click(request, product_id):
    """Rastreia cliques em links de afiliados e armazena o rastreamento."""
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return HttpResponseForbidden("Produto inválido.")

    # Se usuário não estiver logado, redireciona para login
    if not request.user.is_authenticated:
        messages.info(request, 'Faça login para ganhar cashback neste produto!')
        login_url = f"/accounts/login/?next=/admin-panel/track-click/{product_id}/"
        return redirect(login_url)

    # Criar rastreamento da compra
    purchase_tracking = PurchaseTracking.objects.create(
        product=product,
        user=request.user,
        purchase_amount=product.price,  # Valor inicial (será atualizado pelo webhook)
        cashback_percentage_at_purchase=product.cashback_percentage,
        cashback_amount=product.cashback_amount,
        status='pending',
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        referrer=request.META.get('HTTP_REFERER', ''),
    )

    # Construir URL de afiliado com parâmetros de tracking
    affiliate_url = product.affiliate_link
    if '?' in affiliate_url:
        affiliate_url += f"&utm_source=salon_booking&tracking_id={purchase_tracking.id}"
    else:
        affiliate_url += f"?utm_source=salon_booking&tracking_id={purchase_tracking.id}"

    return redirect(affiliate_url)



# Endpoint para o admin visualizar todas as transações de cashback
@login_required
@user_passes_test(is_admin_user)
def admin_cashback_reports(request):
    """Relatórios de todas as transações de cashback para administradores."""
    
    transactions = CashbackTransaction.objects.all().order_by('-created_at')
    
    # Filtros (exemplo)
    affiliate_id_filter = request.GET.get('affiliate_id', '')
    product_id_filter = request.GET.get('product_id', '')

    if affiliate_id_filter:
        transactions = transactions.filter(user_id=affiliate_id_filter)
    if product_id_filter:
        transactions = transactions.filter(purchase_tracking__product_id=product_id_filter)

    total_cashback_distributed = transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)

    paginator = Paginator(transactions, 15)  # 15 transações por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'total_cashback_distributed': total_cashback_distributed,
        'affiliate_id_filter': affiliate_id_filter,
        'product_id_filter': product_id_filter,
    }
    return render(request, 'admin_panel/admin_cashback_reports.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_purchase_confirmation(request):
    """Webhook para receber confirmações de compra dos sistemas de afiliados"""
    try:
        data = json.loads(request.body)
        tracking_id = data.get('tracking_id')
        order_id = data.get('order_id')
        purchase_amount = Decimal(str(data.get('purchase_amount', '0')))
        status = data.get('status', 'confirmed')

        if not all([tracking_id, order_id, purchase_amount]):
            return JsonResponse({
                'status': 'error', 
                'message': 'Dados obrigatórios não fornecidos'
            }, status=400)

        try:
            purchase_tracking = PurchaseTracking.objects.get(id=tracking_id)
        except PurchaseTracking.DoesNotExist:
            return JsonResponse({
                'status': 'error', 
                'message': 'Rastreamento não encontrado'
            }, status=404)

        # Atualizar os dados da compra
        with transaction.atomic():
            purchase_tracking.purchase_amount = purchase_amount
            purchase_tracking.status = status
            purchase_tracking.affiliate_order_id = order_id
            purchase_tracking.purchase_confirmation_date = timezone.now()
            
            # Recalcular cashback com valor real da compra
            cashback_amount = purchase_amount * (purchase_tracking.cashback_percentage_at_purchase / Decimal('100'))
            purchase_tracking.cashback_amount = cashback_amount
            purchase_tracking.save()

            # Criar transação de cashback se confirmada
            if status == 'confirmed':
                cashback_transaction, created = CashbackTransaction.objects.get_or_create(
                    purchase_tracking=purchase_tracking,
                    defaults={
                        'user': purchase_tracking.user,
                        'transaction_type': 'earned',
                        'amount': cashback_amount,
                        'description': f'Cashback da compra {order_id} - {purchase_tracking.product.name}',
                    }
                )

                # Atualizar saldo do usuário
                balance, created = UserCashbackBalance.objects.get_or_create(
                    user=purchase_tracking.user
                )
                balance.update_balance()

        logger.info(f"Compra confirmada via webhook: {order_id} - Cashback: R$ {cashback_amount}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Compra processada com sucesso',
            'cashback_amount': float(cashback_amount)
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error', 
            'message': 'JSON inválido'
        }, status=400)
    except Decimal.InvalidOperation:
        return JsonResponse({
            'status': 'error', 
            'message': 'Valor de compra inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return JsonResponse({
            'status': 'error', 
            'message': 'Erro interno do servidor'
        }, status=500)


@login_required
def user_cashback_dashboard(request):
    """Dashboard de cashback para o usuário"""
    try:
        balance, created = UserCashbackBalance.objects.get_or_create(
            user=request.user
        )
        
        purchases = PurchaseTracking.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        transactions = CashbackTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        # Calcular cashback pendente
        pending_cashback = purchases.filter(status='pending').aggregate(
            total=models.Sum('cashback_amount')
        )['total'] or Decimal('0.00')
        
        context = {
            'balance': balance,
            'purchases': purchases,
            'transactions': transactions,
            'pending_cashback': pending_cashback,
        }
        
        return render(request, 'admin_panel/cashback_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Erro no dashboard de cashback: {e}")
        messages.error(request, "Erro ao carregar dashboard de cashback")
        return redirect('salons:owner_dashboard')


@login_required
def request_cashback_payment(request):
    """Solicitar pagamento do cashback"""
    if request.method == 'POST':
        try:
            balance = UserCashbackBalance.objects.get(user=request.user)
            
            if balance.available_balance < Decimal('10.00'):  # Mínimo R$ 10
                messages.error(request, 'Saldo mínimo para saque é R$ 10,00')
                return redirect('admin_panel:cashback_dashboard')
            
            # Criar transação de solicitação de pagamento
            # (Implementação depende do método de pagamento)
            messages.success(request, 'Solicitação de saque enviada! Processamento em até 30 dias úteis.')
            
        except UserCashbackBalance.DoesNotExist:
            messages.error(request, 'Saldo de cashback não encontrado')
        except Exception as e:
            logger.error(f"Erro ao solicitar saque: {e}")
            messages.error(request, 'Erro ao processar solicitação de saque')
    
    return redirect('admin_panel:cashback_dashboard')


@login_required
@user_passes_test(is_admin_user)
def admin_cashback_management(request):
    """Painel administrativo para gerenciar cashbacks"""
    purchases = PurchaseTracking.objects.all().order_by('-created_at')
    transactions = CashbackTransaction.objects.all().order_by('-created_at')
    
    # Estatísticas
    total_cashback_paid = transactions.filter(
        transaction_type='earned'
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    pending_purchases = purchases.filter(status='pending').count()
    confirmed_purchases = purchases.filter(status='confirmed').count()
    
    context = {
        'purchases': purchases[:20],  # Últimas 20 compras
        'transactions': transactions[:20],  # Últimas 20 transações
        'total_cashback_paid': total_cashback_paid,
        'pending_purchases': pending_purchases,
        'confirmed_purchases': confirmed_purchases,
    }
    
    return render(request, 'admin_panel/admin_cashback_management.html', context)
