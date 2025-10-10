
from django.core.management.base import BaseCommand
from admin_panel.models import PlanPricing
from decimal import Decimal

class Command(BaseCommand):
    help = 'Ensure VIP plan exists in database'

    def handle(self, *args, **options):
        # Criar ou atualizar plano VIP
        vip_plan, created = PlanPricing.objects.get_or_create(
            plan_type='vip_30',
            defaults={
                'price': Decimal('49.90'),
                'description': 'Plano Revolucionário com acesso completo por 30 dias',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Plano VIP criado com ID {vip_plan.id}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Plano VIP já existe com ID {vip_plan.id}')
            )
        
        # Criar ou atualizar plano trial
        trial_plan, created = PlanPricing.objects.get_or_create(
            plan_type='trial_10',
            defaults={
                'price': Decimal('0.00'),
                'description': 'Plano Explorador gratuito por 10 dias',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Plano Trial criado com ID {trial_plan.id}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Plano Trial já existe com ID {trial_plan.id}')
            )
