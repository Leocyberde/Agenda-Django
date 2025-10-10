
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from subscriptions.models import Subscription

class Command(BaseCommand):
    help = 'Fix subscription plans for users who registered with VIP but got trial'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Fix subscription for specific user ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Check all recent subscriptions',
        )

    def handle(self, *args, **options):
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                subscription = user.subscription
                if subscription.plan_type == 'trial_10':
                    subscription.renew_subscription('vip_30')
                    self.stdout.write(
                        self.style.SUCCESS(f'Fixed subscription for user {user.username} to VIP 30 days')
                    )
                else:
                    self.stdout.write(f'User {user.username} already has plan: {subscription.get_plan_type_display()}')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {options["user_id"]} not found'))
            except Subscription.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No subscription found for user ID {options["user_id"]}'))
        
        elif options['all']:
            # Lista todas as assinaturas trial recentes (últimas 24 horas)
            from django.utils import timezone
            from datetime import timedelta
            
            recent_trials = Subscription.objects.filter(
                plan_type='trial_10',
                created_at__gte=timezone.now() - timedelta(hours=24)
            )
            
            self.stdout.write(f'Found {recent_trials.count()} recent trial subscriptions:')
            for sub in recent_trials:
                self.stdout.write(f'  - User: {sub.user.username} (ID: {sub.user.id}) - Created: {sub.created_at}')
            
            self.stdout.write('\nTo fix a specific user, run:')
            self.stdout.write('python manage.py fix_subscription_plans --user-id <USER_ID>')
        
        else:
            self.stdout.write(self.style.ERROR('Please specify --user-id <ID> or --all'))
