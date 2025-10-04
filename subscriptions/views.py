from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Subscription
from admin_panel.models import PlanPricing
import logging

logger = logging.getLogger(__name__)

@login_required
def detail(request):
    """Página principal de assinaturas - redireciona para subscription_detail"""
    return subscription_detail(request)

@login_required
def subscription_detail(request):
    """Mostra detalhes da assinatura do usuário"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado. Apenas proprietários podem acessar esta página.')
        return redirect('accounts:dashboard')
    
    subscription = getattr(request.user, 'subscription', None)

    # Verificar se a assinatura expirou
    if subscription:
        logger.info(f"DEBUG: Verificando assinatura para {request.user.email}. Status atual: {subscription.status}, End Date: {subscription.end_date}, Agora: {timezone.now()}")
        if not subscription.is_active() and subscription.status == 'active':
            logger.info(f"DEBUG: Assinatura {request.user.email} detectada como inativa, atualizando status para 'expired'.")
            subscription.status = 'expired'
            subscription.save()
        elif subscription.is_active() and subscription.status == 'expired':
            logger.info(f"DEBUG: Assinatura {request.user.email} detectada como ativa, mas com status 'expired'. Atualizando status para 'active'.")
            subscription.status = 'active'
            subscription.save()
    else:
        logger.info(f"DEBUG: Usuário {request.user.email} não possui assinatura.")

    # Buscar planos disponíveis
    available_plans = PlanPricing.objects.filter(is_active=True).order_by('plan_type')

    return render(request, 'subscriptions/detail.html', {
        'subscription': subscription,
        'available_plans': available_plans,
    })

@login_required
def renew_subscription(request):
    """Renova a assinatura do usuário"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        plan_type = request.POST.get('plan_type')

        if plan_type not in ['trial_10', 'vip_30']:
            messages.error(request, 'Plano inválido.')
            return redirect('subscriptions:detail')

        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            defaults={'plan_type': plan_type}
        )

        # Renovar a assinatura
        subscription.renew_subscription(plan_type)

        if plan_type == 'trial_10':
            messages.success(request, 'Plano teste renovado por mais 10 dias!')
        else:
            messages.success(request, 'Plano VIP ativado por 30 dias!')

        return redirect('subscriptions:detail')

    return render(request, 'subscriptions/renew.html')

@login_required
def upgrade_to_vip(request):
    """Upgrade para plano VIP"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')

    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        defaults={'plan_type': 'trial_10'}
    )

    if request.method == 'POST':
        # Simular processo de pagamento
        subscription.renew_subscription('vip_30')
        messages.success(request, 'Parabéns! Seu plano VIP foi ativado por 30 dias!')
        return redirect('subscriptions:detail')

    return render(request, 'subscriptions/upgrade.html', {
        'subscription': subscription
    })

def subscription_required(view_func):
    """Decorator para verificar se o usuário tem assinatura ativa"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if request.user.profile.user_type != 'owner':
            messages.error(request, 'Acesso negado.')
            return redirect('accounts:dashboard')

        subscription = getattr(request.user, 'subscription', None)
        if not subscription or not subscription.is_active():
            messages.warning(request, 'Sua assinatura expirou. Renove para continuar usando o sistema.')
            return redirect('subscriptions:detail')

        return view_func(request, *args, **kwargs)

    return wrapper

@login_required
def detail(request):
    """Página de detalhes e gerenciamento da assinatura"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')

    subscription = getattr(request.user, 'subscription', None)

    # Buscar planos disponíveis
    available_plans = PlanPricing.objects.filter(is_active=True).order_by('plan_type')

    context = {
        'subscription': subscription,
        'available_plans': available_plans,
    }

    return render(request, 'subscriptions/detail.html', context)

@login_required
def start_trial(request):
    """Iniciar período de teste gratuito"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')

    # Verificar se já tem assinatura
    if hasattr(request.user, 'subscription'):
        messages.info(request, 'Você já possui uma assinatura.')
        return redirect('subscriptions:detail')

    if request.method == 'POST':
        # Criar assinatura trial
        subscription = Subscription.objects.create(
            user=request.user,
            plan_type='trial_10',
            status='active'
        )

        messages.success(request, 'Período de teste iniciado! Você tem 10 dias para testar todas as funcionalidades.')
        return redirect('salons:create_salon')

    return redirect('subscriptions:detail')