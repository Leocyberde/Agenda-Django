
from django.core.management.base import BaseCommand
from admin_panel.models import PlanPricing

class Command(BaseCommand):
    help = 'Configura os preços padrão dos planos'

    def handle(self, *args, **options):
        # Criar ou atualizar plano Explorador
        trial_plan, created = PlanPricing.objects.get_or_create(
            plan_type='trial_10',
            defaults={
                'price': 0.00,
                'description': 'Teste gratuito por 10 dias com acesso completo aos recursos',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Plano Explorador criado: R$ {trial_plan.price}')
            )
        else:
            self.stdout.write(f'- Plano Explorador já existe: R$ {trial_plan.price}')

        # Criar ou atualizar plano Revolucionário
        vip_plan, created = PlanPricing.objects.get_or_create(
            plan_type='vip_30',
            defaults={
                'price': 49.90,
                'description': 'Plano premium com todos os recursos por 30 dias',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Plano Revolucionário criado: R$ {vip_plan.price}')
            )
        else:
            self.stdout.write(f'- Plano Revolucionário já existe: R$ {vip_plan.price}')

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Configuração de preços concluída!')
        )
        self.stdout.write(
            'Acesse o painel administrativo > Preços dos Planos para gerenciar os valores.'
        )
