
from django.core.management.base import BaseCommand
from django.db.models import Q
from appointments.models import Appointment
from salons.models import FinancialRecord
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Gera registros financeiros para agendamentos concluídos que ainda não possuem registro'

    def add_arguments(self, parser):
        parser.add_argument(
            '--salon-id',
            type=int,
            help='ID específico do salão para processar (opcional)',
        )

    def handle(self, *args, **options):
        salon_id = options.get('salon_id')
        
        # Filtrar agendamentos concluídos
        completed_appointments = Appointment.objects.filter(status='completed')
        
        if salon_id:
            completed_appointments = completed_appointments.filter(salon_id=salon_id)
        
        # Buscar agendamentos que não possuem registros financeiros
        appointments_without_records = completed_appointments.exclude(
            id__in=FinancialRecord.objects.filter(
                related_appointment__isnull=False
            ).values_list('related_appointment_id', flat=True)
        ).select_related('salon', 'service', 'employee', 'client')
        
        count = 0
        commission_count = 0
        
        # Pegar o primeiro usuário admin como criador dos registros
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_staff=True).first()
        
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('Nenhum usuário admin encontrado para criar os registros')
            )
            return
        
        for appointment in appointments_without_records:
            current_month = appointment.appointment_date.month
            current_year = appointment.appointment_date.year
            
            # Criar receita do serviço
            FinancialRecord.objects.create(
                salon=appointment.salon,
                transaction_type='income',
                category='service',
                amount=appointment.service.price,
                description=f'Serviço: {appointment.service.name} - Cliente: {appointment.client.get_full_name() or appointment.client.username}',
                reference_month=current_month,
                reference_year=current_year,
                related_appointment=appointment,
                created_by=admin_user
            )
            count += 1
            
            # Se o funcionário recebe por comissão, criar registro da comissão
            if appointment.employee and appointment.employee.payment_type == 'percentage':
                commission_amount = appointment.service.price * (appointment.employee.commission_percentage / 100)
                FinancialRecord.objects.create(
                    salon=appointment.salon,
                    transaction_type='expense',
                    category='employee_commission',
                    amount=commission_amount,
                    description=f'Comissão: {appointment.employee.user.get_full_name()} - {appointment.service.name}',
                    reference_month=current_month,
                    reference_year=current_year,
                    related_employee=appointment.employee,
                    related_appointment=appointment,
                    created_by=admin_user
                )
                commission_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processados {count} registros de receita e {commission_count} registros de comissão.'
            )
        )
