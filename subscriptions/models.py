from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Subscription(models.Model):
    PLAN_TYPES = (
        ('trial_10', 'Teste 10 dias'),
        ('vip_30', 'VIP 30 dias'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Ativo'),
        ('expired', 'Expirado'),
        ('cancelled', 'Cancelado'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPES, default='trial_10')
    start_date = models.DateTimeField(default=timezone.now, editable=False) # Adicionado editable=False para evitar edição manual no admin, admin, admin, mas permitir update programático
    end_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    last_renewal = models.DateTimeField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        """Define a data de término baseada no tipo de plano"""
        if not self.end_date:
            # Se start_date ainda não foi definido (primeira criação), usar agora
            start_time = self.start_date if self.start_date else timezone.now()
            
            if self.plan_type == 'trial_10':
                self.end_date = start_time + timedelta(days=10)
            elif self.plan_type == 'vip_30':
                self.end_date = start_time + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def is_active(self):
        """Verifica se a assinatura está ativa"""
        return self.status == 'active' and self.end_date > timezone.now()
    
    def days_remaining(self):
        """Retorna quantos dias restam na assinatura"""
        if self.is_active():
            remaining = self.end_date - timezone.now()
            return remaining.days
        return 0
    
    def renew_subscription(self, plan_type=None):
        """Renova a assinatura"""
        if plan_type:
            self.plan_type = plan_type
        
        self.start_date = timezone.now()
        if self.plan_type == 'trial_10':
            self.end_date = self.start_date + timedelta(days=10)
        elif self.plan_type == 'vip_30':
            self.end_date = self.start_date + timedelta(days=30)
        
        self.status = 'active'
        self.last_renewal = timezone.now()
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.get_plan_type_display()} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"
