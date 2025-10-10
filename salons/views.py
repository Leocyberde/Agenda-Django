from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db import transaction
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
import uuid
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse
from subscriptions.views import subscription_required
from .models import Salon, Service, Employee, FinancialRecord
from .forms import SalonForm, ServiceForm, EmployeeForm, EmployeeEditForm, SalonStatusForm
from appointments.models import Appointment, LinkAgendamento, CancellationFee
# from admin_panel.models import Product

@login_required
def create_salon(request):
    """Criar salão para proprietário"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')

    # Verificar se já tem salão
    if hasattr(request.user, 'salon'):
        return redirect('salons:owner_dashboard')

    # Verificar se tem assinatura ativa
    subscription = getattr(request.user, 'subscription', None)
    if not subscription or not subscription.is_active():
        messages.warning(request, 'Você precisa de uma assinatura ativa para criar um salão.')
        return redirect('subscriptions:detail')

    if request.method == 'POST':
        form = SalonForm(request.POST, request.FILES)
        if form.is_valid():
            salon = form.save(commit=False)
            salon.owner = request.user
            salon.save()
            messages.success(request, 'Salão criado com sucesso!')
            return redirect('salons:owner_dashboard')
    else:
        form = SalonForm()

    return render(request, 'salons/create_salon.html', {'form': form})

@subscription_required
def owner_dashboard(request):
    """Dashboard do proprietário"""
    salon = request.user.salon

    # Estatísticas
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    stats = {
        'appointments_today': Appointment.objects.filter(
            salon=salon, 
            appointment_date=today
        ).count(),
        'appointments_week': Appointment.objects.filter(
            salon=salon,
            appointment_date__gte=week_start,
            appointment_date__lte=today
        ).count(),
        'pending_appointments': Appointment.objects.filter(
            salon=salon,
            status='scheduled'
        ).count(),
        'total_services': salon.services.filter(is_active=True).count(),
        'total_employees': salon.employees.filter(is_active=True).count(),
    }

    # Próximos agendamentos
    upcoming_appointments = Appointment.objects.filter(
        salon=salon,
        appointment_date__gte=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')[:5]

    # Informações da assinatura
    subscription = request.user.subscription

    # Dados financeiros básicos do mês atual
    current_month = timezone.now().month
    current_year = timezone.now().year

    current_financial_records = FinancialRecord.objects.filter(
        salon=salon,
        reference_month=current_month,
        reference_year=current_year
    )

    current_income = current_financial_records.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Separar despesas de funcionários das outras despesas
    employee_expenses = current_financial_records.filter(
        transaction_type='expense',
        category__in=['employee_salary', 'employee_commission']
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Outras despesas (excluindo funcionários)
    current_expenses = current_financial_records.filter(
        transaction_type='expense'
    ).exclude(
        category__in=['employee_salary', 'employee_commission']
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Calcular custos estimados de funcionários (salários fixos não registrados)
    from decimal import Decimal
    estimated_employee_costs = Decimal('0.00')
    for employee in salon.employees.filter(is_active=True):
        if employee.payment_type != 'percentage':  # Apenas salários fixos
            estimated_employee_costs += Decimal(str(employee.calculate_monthly_cost()))

    # Total de custos com funcionários
    total_employee_costs = Decimal(str(employee_expenses)) + estimated_employee_costs

    financial_summary = {
        'current_income': current_income,
        'current_expenses': current_expenses,
        'employee_costs': total_employee_costs,
        'net_result': Decimal('0.00'),
    }

    financial_summary['net_result'] = financial_summary['current_income'] - (financial_summary['current_expenses'] + financial_summary['employee_costs'])

    # Produtos em destaque com cashback para o dashboard
    # featured_products = Product.objects.filter(is_active=True, is_featured=True).order_by("-created_at")[:5]

    # Multas de cancelamento pendentes
    pending_fees = CancellationFee.objects.filter(
        appointment__salon=salon,
        is_paid=False
    ).select_related('appointment', 'appointment__client', 'appointment__service').order_by('-created_at')[:10]

    return render(request, 'salons/owner_dashboard.html', {
        'salon': salon,
        'stats': stats,
        'upcoming_appointments': upcoming_appointments,
        'subscription': subscription,
        'financial_summary': financial_summary,
        # 'featured_products': featured_products,  # Mudou de suggested_products para featured_products
        'pending_fees': pending_fees,
    })

@subscription_required
def edit_salon(request):
    """Editar informações do salão"""
    salon = request.user.salon

    if request.method == 'POST':
        form = SalonForm(request.POST, request.FILES, instance=salon)
        if form.is_valid():
            form.save()
            messages.success(request, 'Salão atualizado com sucesso!')
            return redirect('salons:owner_dashboard')
    else:
        form = SalonForm(instance=salon)

    return render(request, 'salons/edit_salon.html', {
        'form': form,
        'salon': salon
    })

@subscription_required
def services_list(request):
    """Lista de serviços do salão"""
    salon = request.user.salon
    services = salon.services.all().order_by('name')

    return render(request, 'salons/services_list.html', {
        'services': services,
        'salon': salon
    })

@subscription_required
def create_service(request):
    """Criar novo serviço"""
    salon = request.user.salon

    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.salon = salon
            service.save()
            messages.success(request, 'Serviço criado com sucesso!')
            return redirect('salons:services_list')
    else:
        form = ServiceForm()

    return render(request, 'salons/create_service.html', {
        'form': form,
        'salon': salon
    })

@subscription_required
def edit_service(request, service_id):
    """Editar serviço"""
    salon = request.user.salon
    service = get_object_or_404(Service, id=service_id, salon=salon)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço atualizado com sucesso!')
            return redirect('salons:services_list')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'salons/edit_service.html', {
        'form': form,
        'service': service,
        'salon': salon
    })

@subscription_required
def delete_service(request, service_id):
    """Deletar serviço"""
    salon = request.user.salon
    service = get_object_or_404(Service, id=service_id, salon=salon)

    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Serviço deletado com sucesso!')
        return redirect('salons:services_list')

    return render(request, 'salons/delete_service.html', {
        'service': service,
        'salon': salon
    })

@subscription_required
def appointments_list(request):
    """Lista de agendamentos do salão"""
    salon = request.user.salon

    # Filtros
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    appointments = Appointment.objects.filter(salon=salon)

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date=filter_date)
        except ValueError:
            pass

    appointments = appointments.order_by('-appointment_date', '-appointment_time')

    return render(request, 'salons/appointments_list.html', {
        'salon': salon,
        'appointments': appointments,
        'status_choices': Appointment.STATUS_CHOICES,
        'status_filter': status_filter,
        'date_filter': date_filter,
    })

@login_required
@require_POST
def delete_appointment_cascade(request, appointment_id):
    """Deleta um agendamento em cascata (remove tudo relacionado)"""
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)

        # Verificar se o usuário tem permissão
        if not request.user.profile.user_type == 'owner':
            return HttpResponseForbidden("Apenas proprietários podem deletar agendamentos")

        # Verificar se o agendamento pertence ao salão do proprietário
        salon = get_object_or_404(Salon, owner=request.user)
        if appointment.salon != salon:
            return HttpResponseForbidden("Você só pode deletar agendamentos do seu salão")

        with transaction.atomic():
            client_name = appointment.client.get_full_name() or appointment.client.username
            service_name = appointment.service.name
            appointment_date = appointment.appointment_date
            appointment_time = appointment.appointment_time

            # Deletar o agendamento (isso irá deletar automaticamente em cascata)
            appointment.delete()

            messages.success(
                request, 
                f'Agendamento de {client_name} para {service_name} em {appointment_date.strftime("%d/%m/%Y")} às {appointment_time.strftime("%H:%M")} foi deletado com sucesso!'
            )

    except Exception as e:
        messages.error(request, f'Erro ao deletar agendamento: {str(e)}')

    return redirect('salons:appointments_list')

# ============== GERENCIAMENTO DE FUNCIONÁRIOS ==============

@subscription_required
def employees_list(request):
    """Lista de funcionários do salão"""
    salon = request.user.salon
    employees = salon.employees.all().order_by('user__first_name')

    return render(request, 'salons/employees_list.html', {
        'employees': employees,
        'salon': salon
    })

@subscription_required
@transaction.atomic
def create_employee(request):
    """Criar novo funcionário"""
    salon = request.user.salon

    if request.method == 'POST':
        form = EmployeeForm(request.POST, salon=salon)
        if form.is_valid():
            try:
                # Criar usuário
                user = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    password=form.cleaned_data['password']
                )

                # Definir como funcionário
                user.profile.user_type = 'employee'
                user.profile.save()

                # Criar employee
                employee = form.save(commit=False)
                employee.user = user
                employee.salon = salon
                employee.save()
                form.save_m2m()  # Salvar many-to-many relationships

                messages.success(request, f'Funcionário {user.get_full_name()} criado com sucesso!')
                return redirect('salons:employees_list')
            except Exception as e:
                messages.error(request, f'Erro ao criar funcionário: {str(e)}')
    else:
        form = EmployeeForm(salon=salon)

    return render(request, 'salons/create_employee.html', {
        'form': form,
        'salon': salon
    })

@subscription_required
def edit_employee(request, employee_id):
    """Editar funcionário"""
    salon = request.user.salon
    employee = get_object_or_404(Employee, id=employee_id, salon=salon)

    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, instance=employee, salon=salon)
        if form.is_valid():
            form.save()
            messages.success(request, f'Funcionário {employee.user.get_full_name()} atualizado com sucesso!')
            return redirect('salons:employees_list')
    else:
        form = EmployeeEditForm(instance=employee, salon=salon)

    return render(request, 'salons/edit_employee.html', {
        'form': form,
        'employee': employee,
        'salon': salon
    })

@subscription_required
def delete_employee(request, employee_id):
    """Deletar funcionário"""
    salon = request.user.salon
    employee = get_object_or_404(Employee, id=employee_id, salon=salon)

    if request.method == 'POST':
        user = employee.user
        employee_name = user.get_full_name()

        # Deletar funcionário (o usuário também será deletado devido ao CASCADE)
        employee.delete()
        user.delete()

        messages.success(request, f'Funcionário {employee_name} removido com sucesso!')
        return redirect('salons:employees_list')

    return render(request, 'salons/delete_employee.html', {
        'employee': employee,
        'salon': salon
    })

# ============== PAINEL DO FUNCIONÁRIO ==============

def is_employee(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.user_type == 'employee'

@login_required
def employee_dashboard(request):
    """Dashboard do funcionário"""
    if not (hasattr(request.user, 'profile') and request.user.profile.user_type == 'employee'):
        messages.error(request, 'Acesso negado. Você precisa ser um funcionário para acessar esta área.')
        return redirect('accounts:dashboard')
    """Dashboard do funcionário"""
    employee = request.user.employee_profile
    salon = employee.salon

    # Estatísticas do funcionário
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    my_appointments = Appointment.objects.filter(
        employee=employee,
        appointment_date__gte=today
    ).order_by('appointment_date', 'appointment_time')

    stats = {
        'appointments_today': my_appointments.filter(
            appointment_date=today
        ).count(),
        'appointments_week': my_appointments.filter(
            appointment_date__gte=week_start,
            appointment_date__lte=today
        ).count(),
        'pending_appointments': my_appointments.filter(
            status='scheduled'
        ).count(),
        'my_services': employee.services.filter(is_active=True).count(),
    }

    # Próximos agendamentos do funcionário
    upcoming_appointments = my_appointments.filter(
        status__in=['scheduled', 'confirmed']
    )[:5]

    # Calcular ganhos por serviço se o funcionário recebe por porcentagem
    earnings_by_service = []
    if employee.payment_type == 'percentage':
        # Buscar agendamentos concluídos do mês atual
        current_month = today.month
        current_year = today.year

        completed_appointments = Appointment.objects.filter(
            employee=employee,
            status='completed',
            appointment_date__month=current_month,
            appointment_date__year=current_year
        ).select_related('service')

        # Agrupar por serviço e calcular ganhos
        service_earnings = {}
        for appointment in completed_appointments:
            service = appointment.service
            earning = service.price * (employee.commission_percentage / 100)

            if service.name in service_earnings:
                service_earnings[service.name]['count'] += 1
                service_earnings[service.name]['total_earned'] += earning
            else:
                service_earnings[service.name] = {
                    'service': service,
                    'count': 1,
                    'price': service.price,
                    'commission_rate': employee.commission_percentage,
                    'earning_per_service': earning,
                    'total_earned': earning
                }

        earnings_by_service = list(service_earnings.values())

    total_monthly_earnings = sum(item['total_earned'] for item in earnings_by_service)

    return render(request, 'salons/employee_dashboard.html', {
        'employee': employee,
        'salon': salon,
        'stats': stats,
        'upcoming_appointments': upcoming_appointments,
        'earnings_by_service': earnings_by_service,
        'total_monthly_earnings': total_monthly_earnings,
        'current_month': today.month,
        'current_year': today.year,
    })

@login_required
def employee_appointments(request):
    """Lista de agendamentos do funcionário"""
    if not (hasattr(request.user, 'profile') and request.user.profile.user_type == 'employee'):
        messages.error(request, 'Acesso negado. Você precisa ser um funcionário para acessar esta área.')
        return redirect('accounts:dashboard')

    employee = request.user.employee_profile
    salon = employee.salon
    today = timezone.now().date()

    # Filtros
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    view_type = request.GET.get('view', 'upcoming')  # 'upcoming' ou 'history'

    # Base queryset - sempre filtrar pelo funcionário
    base_appointments = Appointment.objects.filter(employee=employee).select_related(
        'client', 'service', 'salon'
    )

    # Separar em próximos e histórico
    if view_type == 'history':
        # Para histórico, incluir agendamentos do passado OU agendamentos concluídos/cancelados
        appointments = base_appointments.filter(
            Q(appointment_date__lt=today) | 
            Q(status__in=['completed', 'cancelled'])
        )
        appointments = appointments.order_by('-appointment_date', '-appointment_time')
    else:  # upcoming
        # Para próximos, apenas agendamentos futuros que não foram concluídos ou cancelados
        appointments = base_appointments.filter(
            appointment_date__gte=today,
            status__in=['scheduled', 'confirmed', 'rescheduled']
        )
        appointments = appointments.order_by('appointment_date', 'appointment_time')

    # Aplicar filtros adicionais
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date=filter_date)
        except ValueError:
            pass

    # Contar próximos e histórico para exibir nas abas
    upcoming_count = base_appointments.filter(
        appointment_date__gte=today,
        status__in=['scheduled', 'confirmed', 'rescheduled']
    ).count()

    history_count = base_appointments.filter(
        Q(appointment_date__lt=today) | 
        Q(status__in=['completed', 'cancelled'])
    ).count()

    return render(request, 'salons/employee_appointments.html', {
        'appointments': appointments,
        'employee': employee,
        'salon': salon,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'view_type': view_type,
        'upcoming_count': upcoming_count,
        'history_count': history_count,
        'status_choices': Appointment.STATUS_CHOICES,
        'today': timezone.now().date()
    })

@login_required
def employee_manage_appointment(request, appointment_id):
    """Funcionário gerencia status do agendamento"""
    if not (hasattr(request.user, 'profile') and request.user.profile.user_type == 'employee'):
        messages.error(request, 'Acesso negado. Você precisa ser um funcionário para acessar esta área.')
        return redirect('accounts:dashboard')

    employee = request.user.employee_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, employee=employee)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'confirm':
            appointment.status = 'confirmed'
            appointment.save()
            messages.success(request, 'Agendamento confirmado com sucesso!')

        elif action == 'reschedule':
            new_date = request.POST.get('rescheduled_date')
            new_time = request.POST.get('rescheduled_time')
            reason = request.POST.get('rescheduled_reason', '')

            if new_date and new_time:
                appointment.rescheduled_date = datetime.strptime(new_date, '%Y-%m-%d').date()
                appointment.rescheduled_time = datetime.strptime(new_time, '%H:%M').time()
                appointment.rescheduled_reason = reason
                appointment.status = 'rescheduled'
                appointment.save()

                messages.success(request, 'Proposta de reagendamento enviada ao cliente!')
            else:
                messages.error(request, 'Data e horário são obrigatórios para reagendamento.')

        elif action == 'cancel':
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, 'Agendamento cancelado.')

        elif action == 'complete':
            appointment.status = 'completed'
            appointment.save()

            # Criar registro financeiro automático para o serviço concluído
            from .models import FinancialRecord
            current_month = appointment.appointment_date.month
            current_year = appointment.appointment_date.year

            # Criar receita do serviço
            FinancialRecord.objects.create(
                salon=employee.salon,
                transaction_type='income',
                category='service',
                amount=appointment.service.price,
                description=f'Serviço: {appointment.service.name} - Cliente: {appointment.client.get_full_name() or appointment.client.username}',
                reference_month=current_month,
                reference_year=current_year,
                related_appointment=appointment,
                created_by=request.user
            )

            # Se o funcionário recebe por comissão, criar registro da comissão
            if employee.payment_type == 'percentage':
                commission_amount = appointment.service.price * (employee.commission_percentage / 100)
                FinancialRecord.objects.create(
                    salon=employee.salon,
                    transaction_type='expense',
                    category='employee_commission',
                    amount=commission_amount,
                    description=f'Comissão: {employee.user.get_full_name()} - {appointment.service.name}',
                    reference_month=current_month,
                    reference_year=current_year,
                    related_employee=employee,
                    related_appointment=appointment,
                    created_by=request.user
                )

            messages.success(request, 'Agendamento marcado como concluído!')

    return redirect('salons:employee_appointments')

# ============== GERENCIAMENTO DE LINKS DE AGENDAMENTO ==============

@subscription_required
def manage_client_links(request):
    """Gerenciar links de agendamento dos clientes"""
    salon = request.user.salon
    links = LinkAgendamento.objects.filter(salon=salon).order_by('-created_at')

    return render(request, 'salons/manage_client_links.html', {
        'salon': salon,
        'links': links
    })


@subscription_required
def manage_salon_status(request):
    """Controlar status aberto/fechado do salão"""
    salon = request.user.salon

    if request.method == 'POST':
        form = SalonStatusForm(request.POST, instance=salon)
        if form.is_valid():
            form.save()

            if salon.is_temporarily_closed:
                if salon.closed_until:
                    messages.success(request, f'Salão fechado até {salon.closed_until.strftime("%d/%m/%Y %H:%M")}')
                else:
                    messages.success(request, 'Salão fechado indefinidamente')
            else:
                messages.success(request, 'Salão reaberto para agendamentos')

            return redirect('salons:owner_dashboard')
    else:
        form = SalonStatusForm(instance=salon)

    return render(request, 'salons/manage_status.html', {
        'form': form,
        'salon': salon
    })


@subscription_required  
def toggle_salon_status(request):
    """Toggle rápido do status do salão (AJAX)"""
    salon = request.user.salon

    if request.method == 'POST':
        salon.is_temporarily_closed = not salon.is_temporarily_closed

        if not salon.is_temporarily_closed:
            # Se está reabrindo, limpar campos relacionados
            salon.closed_until = None
            salon.closure_note = None

        salon.save()

        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'is_closed': salon.is_temporarily_closed,
            'message': 'Salão fechado' if salon.is_temporarily_closed else 'Salão aberto'
        })

    return JsonResponse({'success': False})

@subscription_required
def create_client_link(request):
    """Criar novo link de agendamento para cliente"""
    salon = request.user.salon

    if request.method == 'POST':
        try:
            link = LinkAgendamento.objects.create(salon=salon)
            messages.success(request, f'Link criado com sucesso! Token: {link.token}')
            return redirect('salons:manage_client_links')
        except Exception as e:
            messages.error(request, f'Erro ao criar link: {str(e)}')

    return redirect('salons:manage_client_links')

@subscription_required
def toggle_client_link(request, link_id):
    """Ativar/desativar link de agendamento"""
    salon = request.user.salon
    link = get_object_or_404(LinkAgendamento, id=link_id, salon=salon)

    link.is_active = not link.is_active
    link.save()

    status = "ativado" if link.is_active else "desativado"
    messages.success(request, f'Link {status} com sucesso!')

    return redirect('salons:manage_client_links')

@subscription_required  
def manage_appointment_status(request, appointment_id):
    """Gerenciar status do agendamento (confirmar, reagendar, etc.)"""
    salon = request.user.salon
    appointment = get_object_or_404(Appointment, id=appointment_id, salon=salon)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'confirm':
            appointment.status = 'confirmed'
            appointment.save()
            messages.success(request, 'Agendamento confirmado com sucesso!')

        elif action == 'reschedule':
            new_date = request.POST.get('rescheduled_date')
            new_time = request.POST.get('rescheduled_time')
            reason = request.POST.get('rescheduled_reason', '')

            if new_date and new_time:
                appointment.rescheduled_date = datetime.strptime(new_date, '%Y-%m-%d').date()
                appointment.rescheduled_time = datetime.strptime(new_time, '%H:%M').time()
                appointment.rescheduled_reason = reason
                appointment.status = 'rescheduled'
                appointment.save()

                messages.success(request, 'Proposta de reagendamento enviada ao cliente!')
            else:
                messages.error(request, 'Data e horário são obrigatórios para reagendamento.')

        elif action == 'cancel':
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, 'Agendamento cancelado.')

        elif action == 'complete':
            appointment.status = 'completed'
            appointment.save()

            # Criar registro financeiro automático para o serviço concluído
            from .models import FinancialRecord
            current_month = appointment.appointment_date.month
            current_year = appointment.appointment_date.year

            # Criar receita do serviço
            FinancialRecord.objects.create(
                salon=salon,
                transaction_type='income',
                category='service',
                amount=appointment.service.price,
                description=f'Serviço: {appointment.service.name} - Cliente: {appointment.client.get_full_name() or appointment.client.username}',
                reference_month=current_month,
                reference_year=current_year,
                related_appointment=appointment,
                created_by=request.user
            )

            # Se o funcionário recebe por comissão, criar registro da comissão
            if appointment.employee and appointment.employee.payment_type == 'percentage':
                commission_amount = appointment.service.price * (appointment.employee.commission_percentage / 100)
                FinancialRecord.objects.create(
                    salon=salon,
                    transaction_type='expense',
                    category='employee_commission',
                    amount=commission_amount,
                    description=f'Comissão: {appointment.employee.user.get_full_name()} - {appointment.service.name}',
                    reference_month=current_month,
                    reference_year=current_year,
                    related_employee=appointment.employee,
                    related_appointment=appointment,
                    created_by=request.user
                )

            messages.success(request, 'Agendamento marcado como concluído e registros financeiros atualizados!')

    return redirect('salons:appointments_list')

# ============== GERENCIAMENTO FINANCEIRO ==============

@subscription_required 
def financial_dashboard(request):
    """Painel financeiro do salão"""
    salon = request.user.salon

    # Período atual (mês e ano)
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Buscar registros do mês atual
    current_records = FinancialRecord.objects.filter(
        salon=salon,
        reference_month=current_month,
        reference_year=current_year
    )

    # Cálculos do mês atual
    current_income = current_records.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Separar despesas de funcionários das outras despesas
    employee_expenses = current_records.filter(
        transaction_type='expense',
        category__in=['employee_salary', 'employee_commission']
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Outras despesas (excluindo funcionários)
    current_expenses = current_records.filter(
        transaction_type='expense'
    ).exclude(
        category__in=['employee_salary', 'employee_commission']
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Calcular custos estimados de funcionários (salários fixos não registrados)
    estimated_employee_costs = 0
    for employee in salon.employees.filter(is_active=True):
        if employee.payment_type != 'percentage':  # Apenas salários fixos
            estimated_employee_costs += employee.calculate_monthly_cost()

    # Total de custos com funcionários (registrados + estimados)
    total_employee_costs = employee_expenses + estimated_employee_costs

    # Últimas transações
    recent_transactions = FinancialRecord.objects.filter(
        salon=salon
    ).order_by('-created_at')[:10]

    # Resumo por categoria de despesas
    expense_categories = current_records.filter(
        transaction_type='expense'
    ).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'salon': salon,
        'current_month': current_month,
        'current_year': current_year,
        'current_income': current_income,
        'current_expenses': current_expenses,
        'employee_costs': total_employee_costs,
        'employee_expenses_recorded': employee_expenses,
        'employee_costs_estimated': estimated_employee_costs,
        'net_result': current_income - (current_expenses + total_employee_costs),
        'recent_transactions': recent_transactions,
        'expense_categories': expense_categories,
    }

    return render(request, 'salons/financial_dashboard.html', context)

@subscription_required
def add_financial_record(request):
    """Adicionar novo registro financeiro"""
    salon = request.user.salon

    if request.method == 'POST':
        transaction_type = request.POST.get('transaction_type')
        category = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        reference_month = request.POST.get('reference_month')
        reference_year = request.POST.get('reference_year')

        try:
            # Criar registro financeiro
            record = FinancialRecord.objects.create(
                salon=salon,
                transaction_type=transaction_type,
                category=category,
                amount=float(amount),
                description=description,
                reference_month=int(reference_month),
                reference_year=int(reference_year),
                created_by=request.user
            )

            tipo = "receita" if transaction_type == 'income' else "despesa"
            messages.success(request, f'{tipo.capitalize()} adicionada com sucesso!')
            return redirect('salons:financial_dashboard')

        except Exception as e:
            messages.error(request, f'Erro ao adicionar registro: {str(e)}')

    # Valores padrão para o formulário
    now = timezone.now()
    default_month = now.month
    default_year = now.year

    context = {
        'salon': salon,
        'default_month': default_month,
        'default_year': default_year,
        'expense_categories': FinancialRecord.EXPENSE_CATEGORIES,
        'income_categories': FinancialRecord.INCOME_CATEGORIES,
    }

    return render(request, 'salons/add_financial_record.html', context)

@subscription_required
def financial_records_list(request):
    """Listar todos os registros financeiros"""
    salon = request.user.salon

    # Filtros
    month_filter = request.GET.get('month')
    year_filter = request.GET.get('year')
    type_filter = request.GET.get('type')
    category_filter = request.GET.get('category')

    records = FinancialRecord.objects.filter(salon=salon)

    if month_filter:
        records = records.filter(reference_month=int(month_filter))
    if year_filter:
        records = records.filter(reference_year=int(year_filter))
    if type_filter:
        records = records.filter(transaction_type=type_filter)
    if category_filter:
        records = records.filter(category=category_filter)

    records = records.order_by('-reference_year', '-reference_month', '-created_at')

    # Totalizadores
    total_income = records.filter(transaction_type='income').aggregate(
        total=Sum('amount')
    )['total'] or 0

    total_expenses = records.filter(transaction_type='expense').aggregate(
        total=Sum('amount')
    )['total'] or 0

    context = {
        'records': records,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_result': total_income - total_expenses,
        'filters': {
            'month': month_filter,
            'year': year_filter,
            'type': type_filter,
            'category': category_filter,
        }
    }

    return render(request, 'salons/financial_records_list.html', context)

@subscription_required
def generate_employee_expenses(request):
    """Gerar despesas automáticas dos funcionários para o mês atual"""
    salon = request.user.salon

    if request.method == 'POST':
        month = int(request.POST.get('month', timezone.now().month))
        year = int(request.POST.get('year', timezone.now().year))

        # Verificar se já existem registros para funcionários no mês
        existing_records = FinancialRecord.objects.filter(
            salon=salon,
            reference_month=month,
            reference_year=year,
            category='employee_salary'
        ).count()

        if existing_records > 0:
            messages.warning(request, f'Já existem {existing_records} registros de salários para {month}/{year}')
            return redirect('salons:financial_dashboard')

        # Criar registros para funcionários ativos
        created_count = 0
        for employee in salon.employees.filter(is_active=True):
            if employee.payment_type != 'percentage':  # Não criar para comissionados
                monthly_cost = employee.calculate_monthly_cost()
                if monthly_cost > 0:
                    FinancialRecord.objects.create(
                        salon=salon,
                        transaction_type='expense',
                        category='employee_salary',
                        amount=monthly_cost,
                        description=f'Salário - {employee.user.get_full_name()} ({employee.get_payment_type_display()})',
                        reference_month=month,
                        reference_year=year,
                        related_employee=employee,
                        created_by=request.user
                    )
                    created_count += 1

        messages.success(request, f'{created_count} registros de salários gerados para {month}/{year}!')
        return redirect('salons:financial_dashboard')

    return redirect('salons:financial_dashboard')

# ============== LOJA DE PRODUTOS ==============

# @subscription_required
# def store_products(request):
    """Página da loja com todos os produtos disponíveis"""
    salon = request.user.salon

    # Buscar produtos ativos
    products = Product.objects.filter(is_active=True).order_by('-is_featured', '-created_at')

    # Filtros
    category_filter = request.GET.get('category', '')
    search_filter = request.GET.get('search', '')

    if category_filter:
        products = products.filter(category=category_filter)

    if search_filter:
        products = products.filter(
            Q(name__icontains=search_filter) |
            Q(brand__icontains=search_filter) |
            Q(description__icontains=search_filter)
        )

    # Categorias para o filtro
    categories = Product.CATEGORY_CHOICES

    return render(request, 'salons/store_products.html', {
        'salon': salon,
        'products': products,
        'categories': categories,
        'category_filter': category_filter,
        'search_filter': search_filter,
    })

# ============== LINK DE AGENDAMENTO ==============

@subscription_required
@require_POST
def mark_cancellation_fee_paid(request, fee_id):
    """Marcar multa de cancelamento como paga"""
    salon = request.user.salon

    try:
        fee = get_object_or_404(CancellationFee, 
                               id=fee_id, 
                               appointment__salon=salon,
                               is_paid=False)

        fee.is_paid = True
        fee.paid_at = timezone.now()
        fee.save()

        client_name = fee.appointment.client.get_full_name() or fee.appointment.client.username
        messages.success(request, f'Multa de R$ {fee.amount:.2f} de {client_name} marcada como paga!')

    except Exception as e:
        messages.error(request, f'Erro ao marcar multa como paga: {str(e)}')

    return redirect('salons:owner_dashboard')