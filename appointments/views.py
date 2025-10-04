from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, date
from .models import LinkAgendamento, Appointment, CancellationFee
from salons.models import Salon, Service, Employee
from accounts.models import UserProfile
from .utils.scheduling import validate_appointment_request, compute_end_time, get_available_time_slots

def client_booking(request, token):
    """Página de agendamento do cliente via link único"""
    try:
        link = get_object_or_404(LinkAgendamento, token=token, is_active=True)
        salon = link.salon

        # Se o link já está vinculado a um cliente, mostrar histórico e formulário de novo agendamento
        if link.client:
            client = link.client
            appointments = link.get_client_appointments()

            # Verificar se há reagendamentos pendentes
            pending_reschedules = appointments.filter(status='rescheduled')

            # Verificar se há multas de cancelamento pendentes
            pending_fees = CancellationFee.objects.filter(
                appointment__client=client,
                appointment__salon=salon,
                is_paid=False
            )
            pending_fees_total = sum(fee.amount for fee in pending_fees)


            if request.method == 'POST':
                print(f"POST REQUEST RECEBIDO - Cliente existente")
                print(f"POST data: {dict(request.POST)}")
                action = request.POST.get('action')

                # Verifica se há multas pendentes antes de permitir novo agendamento
                if pending_fees_total > 0:
                    messages.error(request, f'Você possui multas pendentes no valor total de R$ {pending_fees_total:.2f}. Por favor, regularize para agendar novos serviços.')
                    return redirect('appointments:client_booking', token=token)

                if action == 'new_appointment':
                    # Criar novo agendamento
                    service_id = request.POST.get('service_id')
                    employee_id = request.POST.get('employee_id') or None
                    appointment_date = request.POST.get('appointment_date')
                    appointment_time = request.POST.get('appointment_time')
                    notes = request.POST.get('notes', '').strip()

                    # Validações básicas
                    if not all([service_id, appointment_date, appointment_time]):
                        messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
                        return redirect('appointments:client_booking', token=token)

                    try:
                        with transaction.atomic():
                            service = Service.objects.get(id=service_id, salon=salon, is_active=True)

                            # Preparar funcionário se especificado
                            employee = None
                            if employee_id:
                                employee = Employee.objects.get(id=employee_id, salon=salon, is_active=True)

                            # Verificar data/hora
                            appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                            appointment_time_obj = datetime.strptime(appointment_time, '%H:%M').time()

                            # Calcular horários de início e fim
                            start_dt = datetime.combine(appointment_date_obj, appointment_time_obj)
                            start_dt = timezone.make_aware(start_dt)
                            end_dt = compute_end_time(appointment_date_obj, appointment_time_obj, service)
                            end_dt = timezone.make_aware(end_dt)

                            # Verificar se já existe agendamento para este horário específico
                            existing_appointment = Appointment.objects.select_for_update().filter(
                                salon=salon,
                                appointment_date=appointment_date_obj,
                                appointment_time=appointment_time_obj,
                                status__in=['scheduled', 'confirmed']
                            )

                            if employee:
                                existing_appointment = existing_appointment.filter(employee=employee)

                            if existing_appointment.exists():
                                messages.error(request, 'Este horário já está ocupado. Por favor, escolha outro horário.')
                                return redirect('appointments:client_booking', token=token)

                            # Validar agendamento usando lógica centralizada
                            is_valid, error_msg, assigned_employee = validate_appointment_request(
                                salon=salon,
                                service=service,
                                client=client,
                                start_dt=start_dt,
                                end_dt=end_dt,
                                employee=employee,
                                use_locking=True
                            )

                            if not is_valid:
                                messages.error(request, error_msg)
                                return redirect('appointments:client_booking', token=token)

                            # Criar agendamento
                            appointment = Appointment.objects.create(
                                client=client,
                                salon=salon,
                                service=service,
                                employee=assigned_employee,
                                appointment_date=appointment_date_obj,
                                appointment_time=appointment_time_obj,
                                notes=notes,
                                status='scheduled'
                            )

                            messages.success(request, 'Agendamento realizado com sucesso!')
                            return redirect('appointments:client_booking', token=token)

                    except Exception as e:
                        from django.db import IntegrityError
                        print(f"ERRO AGENDAMENTO CLIENTE EXISTENTE: {str(e)}")
                        print(f"Service ID: {service_id}")
                        print(f"Employee ID: {employee_id}")
                        print(f"Date: {appointment_date}")
                        print(f"Time: {appointment_time}")
                        import traceback
                        traceback.print_exc()

                        if isinstance(e, IntegrityError) and 'UNIQUE constraint failed' in str(e):
                            messages.error(request, 'Este horário já está ocupado. Por favor, escolha outro horário.')
                        else:
                            messages.error(request, f'Erro ao criar agendamento: {str(e)}')
                        return redirect('appointments:client_booking', token=token)

            # Mostrar histórico e formulário
            services = salon.services.filter(is_active=True)
            employees = salon.employees.filter(is_active=True)
            
            # Verificar se é o primeiro agendamento (flag na query string)
            show_pwa_prompt = request.GET.get('first_booking') == '1'

            return render(request, 'appointments/client_booking.html', {
                'link': link,
                'salon': salon,
                'client': client,
                'appointments': appointments,
                'pending_reschedules': pending_reschedules,
                'services': services,
                'employees': employees,
                'is_existing_client': True,
                'today': timezone.localtime(timezone.now()).date(),
                'pending_fees_total': pending_fees_total,
                'show_pwa_prompt': show_pwa_prompt,
                'booking_token': str(token)
            })

        else:
            # Link não vinculado - formulário de primeiro agendamento
            if request.method == 'POST':
                print(f"POST REQUEST RECEBIDO - Cliente novo")
                print(f"POST data: {dict(request.POST)}")
                try:
                    with transaction.atomic():
                        # Dados do cliente
                        client_name = request.POST.get('client_name', '').strip()
                        client_email = request.POST.get('client_email', '').strip()
                        client_phone = request.POST.get('client_phone', '').strip()

                        # Dados do agendamento
                        service_id = request.POST.get('service_id')
                        employee_id = request.POST.get('employee_id') or None
                        appointment_date = request.POST.get('appointment_date')
                        appointment_time = request.POST.get('appointment_time')
                        notes = request.POST.get('notes', '').strip()

                        # Validações
                        if not all([client_name, client_email, service_id, appointment_date, appointment_time]):
                            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
                            return redirect('appointments:client_booking', token=token)

                        # Verificar se já existe usuário com este email
                        existing_user = User.objects.filter(email=client_email).first()
                        if existing_user:
                            # Se já existe, usar o usuário existente
                            client = existing_user
                        else:
                            # Criar novo usuário
                            client = User.objects.create_user(
                                username=client_email,
                                email=client_email,
                                first_name=client_name.split()[0] if client_name.split() else client_name,
                                last_name=' '.join(client_name.split()[1:]) if len(client_name.split()) > 1 else ''
                            )

                        # Criar ou atualizar perfil
                        profile, created = UserProfile.objects.get_or_create(user=client)
                        if client_phone:
                            profile.phone = client_phone
                        profile.user_type = 'client'
                        profile.save()

                        # Vincular cliente ao link
                        link.client = client
                        link.save()

                        # Criar agendamento
                        service = Service.objects.get(id=service_id, salon=salon, is_active=True)

                        # Preparar funcionário se especificado
                        employee = None
                        if employee_id:
                            employee = Employee.objects.get(id=employee_id, salon=salon, is_active=True)

                        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                        appointment_time_obj = datetime.strptime(appointment_time, '%H:%M').time()

                        # Calcular horários de início e fim
                        start_dt = datetime.combine(appointment_date_obj, appointment_time_obj)
                        start_dt = timezone.make_aware(start_dt)
                        end_dt = compute_end_time(appointment_date_obj, appointment_time_obj, service)
                        end_dt = timezone.make_aware(end_dt)

                        # Verificar se já existe agendamento para este horário específico
                        existing_appointment = Appointment.objects.select_for_update().filter(
                            salon=salon,
                            appointment_date=appointment_date_obj,
                            appointment_time=appointment_time_obj,
                            status__in=['scheduled', 'confirmed']
                        )

                        if employee:
                            existing_appointment = existing_appointment.filter(employee=employee)

                        if existing_appointment.exists():
                            messages.error(request, 'Este horário já está ocupado. Por favor, escolha outro horário.')
                            return redirect('appointments:client_booking', token=token)

                        # Validar agendamento usando lógica centralizada
                        is_valid, error_msg, assigned_employee = validate_appointment_request(
                            salon=salon,
                            service=service,
                            client=client,
                            start_dt=start_dt,
                            end_dt=end_dt,
                            employee=employee,
                            use_locking=True
                        )

                        if not is_valid:
                            messages.error(request, error_msg)
                            return redirect('appointments:client_booking', token=token)

                        appointment = Appointment.objects.create(
                            client=client,
                            salon=salon,
                            service=service,
                            employee=assigned_employee,
                            appointment_date=appointment_date_obj,
                            appointment_time=appointment_time_obj,
                            notes=notes,
                            status='scheduled'
                        )

                        messages.success(request, 'Cadastro e agendamento realizados com sucesso!')
                        # Redirecionar com flag para mostrar prompt do PWA (primeiro agendamento)
                        return redirect(f'/appointments/booking/{token}/?first_booking=1')

                except Exception as e:
                    from django.db import IntegrityError
                    print(f"ERRO CLIENTE NOVO: {str(e)}")
                    print(f"Client Name: {request.POST.get('client_name', '')}")
                    print(f"Client Email: {request.POST.get('client_email', '')}")
                    print(f"Service ID: {request.POST.get('service_id', '')}")
                    print(f"Date: {request.POST.get('appointment_date', '')}")
                    print(f"Time: {request.POST.get('appointment_time', '')}")
                    import traceback
                    traceback.print_exc()

                    if isinstance(e, IntegrityError) and 'UNIQUE constraint failed' in str(e):
                        messages.error(request, 'Este horário já está ocupado. Por favor, escolha outro horário.')
                    else:
                        messages.error(request, f'Erro ao processar: {str(e)}')
                    return redirect('appointments:client_booking', token=token)

            # Formulário inicial para cliente não vinculado
            services = salon.services.filter(is_active=True)
            employees = salon.employees.filter(is_active=True)

            # Verificar multas pendentes para cliente não vinculado (caso o link já tenha sido associado a um cliente mas ele ainda não agendou)
            pending_fees = CancellationFee.objects.filter(
                appointment__client=link.client,
                appointment__salon=salon,
                is_paid=False
            )
            pending_fees_total = sum(fee.amount for fee in pending_fees)

            # Se houver multas pendentes, redirecionar para uma página de aviso ou mostrar mensagem
            if pending_fees_total > 0:
                messages.error(request, f'Você possui multas pendentes no valor total de R$ {pending_fees_total:.2f}. Por favor, regularize para agendar novos serviços.')
                # Poderia redirecionar para uma página específica de pagamento de multas se existisse
                # return redirect('appointments:pay_fees', token=token) 
                # Por enquanto, apenas impede o agendamento e exibe a mensagem
                return render(request, 'appointments/client_booking.html', {
                    'link': link,
                    'salon': salon,
                    'services': services,
                    'employees': employees,
                    'is_existing_client': False,
                    'today': timezone.localtime(timezone.now()).date(),
                    'pending_fees_total': pending_fees_total
                })


            return render(request, 'appointments/client_booking.html', {
                'link': link,
                'salon': salon,
                'services': services,
                'employees': employees,
                'is_existing_client': False,
                'today': timezone.localtime(timezone.now()).date(),
                'booking_token': str(token)
            })

    except LinkAgendamento.DoesNotExist:
        return render(request, 'appointments/invalid_link.html')

def confirm_reschedule(request, token, appointment_id):
    """Cliente confirma o reagendamento proposto"""
    try:
        link = get_object_or_404(LinkAgendamento, token=token, is_active=True)
        appointment = get_object_or_404(Appointment, 
                                      id=appointment_id, 
                                      client=link.client,
                                      salon=link.salon,
                                      status='rescheduled')

        # Confirmar reagendamento
        appointment.appointment_date = appointment.rescheduled_date
        appointment.appointment_time = appointment.rescheduled_time
        appointment.rescheduled_date = None
        appointment.rescheduled_time = None
        appointment.rescheduled_reason = ''
        appointment.status = 'confirmed'
        appointment.save()

        messages.success(request, 'Reagendamento confirmado com sucesso!')

    except Exception as e:
        messages.error(request, f'Erro ao confirmar reagendamento: {str(e)}')

    return redirect('appointments:client_booking', token=token)

def reject_reschedule(request, token, appointment_id):
    """Cliente rejeita o reagendamento proposto"""
    try:
        link = get_object_or_404(LinkAgendamento, token=token, is_active=True)
        appointment = get_object_or_404(Appointment, 
                                      id=appointment_id, 
                                      client=link.client,
                                      salon=link.salon,
                                      status='rescheduled')

        # Cancelar agendamento
        appointment.status = 'cancelled'
        appointment.rescheduled_date = None
        appointment.rescheduled_time = None
        appointment.rescheduled_reason = ''
        appointment.save()

        messages.success(request, 'Reagendamento rejeitado. Agendamento foi cancelado.')

    except Exception as e:
        messages.error(request, f'Erro ao rejeitar reagendamento: {str(e)}')

    return redirect('appointments:client_booking', token=token)

def get_available_slots(request, token):
    """API para retornar horários disponíveis via AJAX"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        link = get_object_or_404(LinkAgendamento, token=token, is_active=True)
        salon = link.salon

        # Parâmetros da requisição
        service_id = request.GET.get('service_id')
        employee_id = request.GET.get('employee_id') or None
        date_str = request.GET.get('date')

        if not service_id or not date_str:
            return JsonResponse({'error': 'Parâmetros obrigatórios: service_id e date'}, status=400)

        try:
            service = Service.objects.get(id=service_id, salon=salon, is_active=True)
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Verificar se a data não é no passado
            if appointment_date < timezone.now().date():
                return JsonResponse({'slots': []})

            # Buscar funcionário se especificado
            employee = None
            if employee_id:
                try:
                    employee = Employee.objects.get(id=employee_id, salon=salon, is_active=True)
                except Employee.DoesNotExist:
                    return JsonResponse({'error': 'Funcionário não encontrado'}, status=400)

            # Buscar horários disponíveis
            available_slots = get_available_time_slots(salon, service, appointment_date, employee)

            return JsonResponse({'slots': available_slots})

        except Service.DoesNotExist:
            return JsonResponse({'error': 'Serviço não encontrado'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Formato de data inválido'}, status=400)

    except LinkAgendamento.DoesNotExist:
        return JsonResponse({'error': 'Link não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def cancel_appointment(request, token, appointment_id):
    """Cliente cancela um agendamento - pode haver multa se for tarde demais"""
    if request.method != 'POST':
        messages.error(request, 'Método não permitido')
        return redirect('appointments:client_booking', token=token)

    try:
        with transaction.atomic():
            link = get_object_or_404(LinkAgendamento, token=token, is_active=True)

            # Verificar se o link está vinculado a um cliente
            if not link.client:
                messages.error(request, 'Link não está vinculado a um cliente.')
                return redirect('appointments:client_booking', token=token)

            appointment = get_object_or_404(
                Appointment, 
                id=appointment_id, 
                client=link.client,
                salon=link.salon
            )

            # Verificar se o agendamento pode ser cancelado
            if not appointment.can_be_cancelled():
                messages.error(request, 'Este agendamento não pode ser cancelado.')
                return redirect('appointments:client_booking', token=token)

            # Verificar se o agendamento está confirmado (só aplica multa se confirmado)
            apply_fee = False
            fee_amount = 0
            hours_before = 0

            if appointment.status == 'confirmed' and link.salon.cancellation_policy_enabled:
                # Calcular tempo até o agendamento
                appointment_datetime = datetime.combine(
                    appointment.appointment_date, 
                    appointment.appointment_time
                )
                appointment_datetime = timezone.make_aware(appointment_datetime)
                now = timezone.now()

                time_until = appointment_datetime - now
                hours_before = time_until.total_seconds() / 3600  # Converter para horas

                # Verificar se deve aplicar multa
                if hours_before < link.salon.cancellation_hours_threshold and hours_before > 0:
                    apply_fee = True
                    service_price = appointment.service.price
                    fee_percentage = link.salon.cancellation_fee_percentage
                    fee_amount = (service_price * fee_percentage) / 100

            # Cancelar o agendamento
            appointment.status = 'cancelled'
            appointment.save()

            # Criar registro de multa se aplicável
            if apply_fee and fee_amount > 0:
                CancellationFee.objects.create(
                    appointment=appointment,
                    amount=fee_amount,
                    fee_percentage=link.salon.cancellation_fee_percentage,
                    service_price=appointment.service.price,
                    hours_before_appointment=hours_before,
                    cancelled_at=timezone.now(),
                    cancelled_by_employee=appointment.employee,
                    notes=f'Cancelamento tardio - menos de {link.salon.cancellation_hours_threshold}h antes do agendamento'
                )
                messages.warning(
                    request, 
                    f'Agendamento cancelado. Foi aplicada uma multa de R$ {fee_amount:.2f} '
                    f'({link.salon.cancellation_fee_percentage}%) por cancelamento tardio.'
                )
            else:
                messages.success(request, 'Agendamento cancelado com sucesso!')

    except LinkAgendamento.DoesNotExist:
        messages.error(request, 'Link de agendamento não encontrado.')
    except Appointment.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
    except Exception as e:
        print(f"ERRO NO CANCELAMENTO: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Erro ao cancelar agendamento: {str(e)}')

    return redirect('appointments:client_booking', token=token)