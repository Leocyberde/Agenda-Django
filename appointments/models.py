from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from salons.models import Salon, Service
import uuid

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('scheduled', 'Agendado'),
        ('confirmed', 'Confirmado'),
        ('rescheduled', 'Reagendado'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Concluído'),
        ('no_show', 'Não compareceu'),
    )
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', verbose_name="Cliente")
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='appointments', verbose_name="Salão")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments', verbose_name="Serviço")
    employee = models.ForeignKey('salons.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments', verbose_name="Funcionário responsável")
    appointment_date = models.DateField(verbose_name="Data do Agendamento")
    appointment_time = models.TimeField(verbose_name="Horário do Agendamento")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    # Campos para reagendamento
    rescheduled_date = models.DateField(blank=True, null=True, verbose_name="Nova Data (Reagendamento)")
    rescheduled_time = models.TimeField(blank=True, null=True, verbose_name="Novo Horário (Reagendamento)")
    rescheduled_reason = models.TextField(blank=True, null=True, verbose_name="Motivo do Reagendamento")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.client.username} - {self.salon.name} - {self.appointment_date} {self.appointment_time}"
    
    def can_be_cancelled(self):
        """Verifica se o agendamento pode ser cancelado"""
        from datetime import datetime
        
        # Agendamentos já cancelados ou concluídos não podem ser cancelados novamente
        if self.status in ['cancelled', 'completed']:
            return False
        
        # Agendamentos pendentes, agendados ou confirmados podem ser cancelados
        # A multa é aplicada separadamente na view de cancelamento
        if self.status in ['pending', 'scheduled', 'confirmed']:
            # Verificar se não é no passado
            appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
            appointment_datetime = timezone.make_aware(appointment_datetime)
            return timezone.now() < appointment_datetime
        
        return False
    
    def get_end_time(self):
        """Calcula o horário de término baseado na duração do serviço"""
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(self.appointment_date, self.appointment_time)
        end_datetime = start_datetime + timedelta(minutes=self.service.duration)
        return end_datetime.time()
    
    def has_rescheduled_proposal(self):
        """Verifica se existe uma proposta de reagendamento"""
        return self.status == 'rescheduled' and self.rescheduled_date and self.rescheduled_time
    
    def get_rescheduled_end_time(self):
        """Calcula o horário de término da proposta de reagendamento"""
        if not self.has_rescheduled_proposal():
            return None
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(self.rescheduled_date, self.rescheduled_time)
        end_datetime = start_datetime + timedelta(minutes=self.service.duration)
        return end_datetime.time()
    
    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['appointment_date', 'appointment_time']
        indexes = [
            models.Index(fields=['salon', 'appointment_date']),
            models.Index(fields=['employee', 'appointment_date']),
            models.Index(fields=['status']),
            models.Index(fields=['appointment_date', 'appointment_time']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['salon', 'employee', 'appointment_date', 'appointment_time'],
                condition=models.Q(employee__isnull=False) & models.Q(status__in=['scheduled', 'confirmed']),
                name='unique_employee_appointment_time'
            ),
            models.UniqueConstraint(
                fields=['salon', 'appointment_date', 'appointment_time'],
                condition=models.Q(employee__isnull=True) & models.Q(status__in=['scheduled', 'confirmed']),
                name='unique_salon_appointment_time_no_employee'
            )
        ]


class CancellationFee(models.Model):
    """Registro de multas por cancelamento tardio"""
    appointment = models.OneToOneField(
        'Appointment', 
        on_delete=models.CASCADE, 
        related_name='cancellation_fee',
        verbose_name="Agendamento"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Valor da Multa"
    )
    fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="Porcentagem Aplicada (%)"
    )
    service_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Valor do Serviço"
    )
    hours_before_appointment = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Horas antes do agendamento"
    )
    cancelled_at = models.DateTimeField(
        verbose_name="Data e Hora do Cancelamento"
    )
    cancelled_by_employee = models.ForeignKey(
        'salons.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Funcionário do Agendamento"
    )
    is_paid = models.BooleanField(default=False, verbose_name="Multa Paga")
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name="Data do Pagamento")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        status = "Paga" if self.is_paid else "Pendente"
        return f"Multa: R$ {self.amount:.2f} - {self.appointment.client.get_full_name()} - {status}"
    
    class Meta:
        verbose_name = "Multa de Cancelamento"
        verbose_name_plural = "Multas de Cancelamento"
        ordering = ['-created_at']


class LinkAgendamento(models.Model):
    """Link único por cliente para agendamentos sem necessidade de cadastro/senha"""
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="Token único")
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='client_links', verbose_name="Salão")
    client = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, 
                                related_name='booking_link', verbose_name="Cliente vinculado")
    
    # Dados temporários do cliente (até ele fazer o primeiro agendamento)
    temp_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome temporário")
    temp_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Telefone temporário")
    temp_email = models.EmailField(blank=True, null=True, verbose_name="Email temporário")
    
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.client:
            return f"Link {self.token} - {self.client.get_full_name() or self.client.username}"
        return f"Link {self.token} - {self.salon.name} (não vinculado)"
    
    def is_linked(self):
        """Verifica se o link já está vinculado a um cliente"""
        return self.client is not None
    
    def get_client_appointments(self):
        """Retorna agendamentos do cliente vinculado ordenados por data decrescente"""
        if not self.client:
            return []
        return self.client.appointments.filter(salon=self.salon).order_by('-appointment_date', '-appointment_time')
    
    def get_booking_url(self):
        """Retorna a URL para acessar o link de agendamento"""
        from django.urls import reverse
        return reverse('appointments:client_booking', kwargs={'token': str(self.token)})
    
    def has_pending_rescheduled_appointments(self):
        """Verifica se há agendamentos reagendados aguardando resposta do cliente"""
        if not self.client:
            return False
        return self.client.appointments.filter(salon=self.salon, status='rescheduled').exists()
    
    class Meta:
        verbose_name = "Link de Agendamento"
        verbose_name_plural = "Links de Agendamento"
        ordering = ['-created_at']
