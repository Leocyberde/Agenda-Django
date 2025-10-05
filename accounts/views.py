from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserProfile

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        messages.success(self.request, 'Conta criada com sucesso! Faça login para continuar.')
        return response

def register_view(request):
    plan = request.GET.get('plan', 'trial')
    
    # Determinar o tipo de plano correto
    if plan == 'vip':
        plan_type = 'vip_30'
    else:
        plan_type = 'trial_10'
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, plan_type=plan_type)
        if form.is_valid():
            # Criar o usuário
            user = form.save()
            
            # Se for plano pago (VIP), fazer login automático e redirecionar para pagamento
            if plan == 'vip':
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Buscar o plano VIP para redirecionar para pagamento
                from admin_panel.models import PlanPricing
                try:
                    vip_plan = PlanPricing.objects.filter(plan_type='vip_30', is_active=True).first()
                    if vip_plan:
                        messages.info(request, 'Conta criada! Complete o pagamento para ativar sua assinatura VIP.')
                        return redirect('payments:gerar_pix', plan_id=vip_plan.id)
                except Exception as e:
                    logger.error(f"Erro ao buscar plano VIP: {e}")
                
                # Se não encontrar plano, redirecionar para página de assinaturas
                messages.warning(request, 'Plano VIP não disponível no momento. Escolha um plano abaixo.')
                return redirect('subscriptions:detail')
            else:
                # Para plano trial, criar assinatura automaticamente
                from subscriptions.models import Subscription
                from datetime import timedelta
                from django.utils import timezone
                
                Subscription.objects.create(
                    user=user,
                    plan_type='trial_10',
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=10),
                    status='active'
                )
                
                messages.success(request, 'Conta criada com sucesso! Faça login para continuar.')
                return redirect('accounts:login')
    else:
        form = CustomUserCreationForm(plan_type=plan_type)
    
    return render(request, 'accounts/register.html', {
        'form': form,
        'selected_plan': plan
    })

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile
    })


@login_required
def dashboard_view(request):
    """Dashboard principal que redireciona baseado no tipo de usuário"""
    # Verificar se é administrador (superusuário)
    if request.user.is_superuser:
        return redirect('admin_panel:dashboard')
    
    # Garantir que o perfil existe antes de acessá-lo
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Se não existe perfil, criar um padrão
        profile = UserProfile.objects.create(user=request.user, user_type='owner')
    
    if profile.user_type == 'owner':
        # Verificar se tem assinatura ativa
        subscription = getattr(request.user, 'subscription', None)
        
        # Se não tem assinatura, redirecionar para escolher plano
        if not subscription:
            messages.info(request, 'Escolha um plano para começar a usar o sistema.')
            return redirect('subscriptions:detail')
        
        # Se tem assinatura mas ela expirou, redirecionar para renovação
        if subscription and not subscription.is_active():
            messages.warning(request, 'Sua assinatura expirou. Renove para continuar usando o sistema.')
            return redirect('subscriptions:detail')
        
        # Verificar se tem salão cadastrado
        if hasattr(request.user, 'salon'):
            return redirect('salons:owner_dashboard')
        else:
            return redirect('salons:create_salon')
    elif profile.user_type == 'employee':
        return redirect('salons:employee_dashboard')
    else:
        # Para clientes, redirecionar para a página inicial por enquanto
        return redirect('core:landing_page')

@login_required
def subscription_status(request):
    """Mostra status da assinatura do usuário"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')
    
    subscription = getattr(request.user, 'subscription', None)
    
    return render(request, 'accounts/subscription_status.html', {
        'subscription': subscription
    })

class CustomLoginView(LoginView):
    """View de login customizada que processa parâmetro plan"""
    template_name = 'accounts/login.html'
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Tentar autenticar por username primeiro
        user = authenticate(request, username=username, password=password)
        
        # Se falhar e o username parece um email, tentar buscar por email
        if not user and '@' in username:
            from django.contrib.auth.models import User
            try:
                user_obj = User.objects.get(email__iexact=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user:
            login(request, user)
            return redirect(self.get_success_url())
        
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        plan = self.request.GET.get('plan')
        if plan:
            return f"/accounts/dashboard/?plan={plan}"
        return super().get_success_url()

def logout_view(request):
    """Custom logout view that accepts GET requests"""
    logout(request)
    messages.success(request, 'Você saiu do sistema com sucesso!')
    return redirect('core:landing_page')
