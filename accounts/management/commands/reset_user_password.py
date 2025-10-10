
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

class Command(BaseCommand):
    help = 'Reseta a senha de um usuário para uma senha temporária'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email do usuário')
        parser.add_argument('--password', type=str, default='Senha123!', help='Nova senha (padrão: Senha123!)')

    def handle(self, *args, **options):
        email = options['email'].lower().strip()
        new_password = options['password']
        
        try:
            # Buscar usuário pelo email
            user = User.objects.filter(email__iexact=email).first()
            
            if not user:
                # Tentar buscar pelo username também
                user = User.objects.filter(username__iexact=email).first()
            
            if not user:
                self.stdout.write(self.style.ERROR(f'❌ Usuário não encontrado: {email}'))
                return
            
            self.stdout.write(f"👤 Usuário encontrado:")
            self.stdout.write(f"   - ID: {user.id}")
            self.stdout.write(f"   - Username: {user.username}")
            self.stdout.write(f"   - Email: {user.email}")
            self.stdout.write(f"   - Nome: {user.first_name} {user.last_name}")
            
            if hasattr(user, 'profile'):
                self.stdout.write(f"   - Tipo: {user.profile.get_user_type_display()}")
            
            if hasattr(user, 'subscription'):
                sub = user.subscription
                self.stdout.write(f"   - Assinatura: {sub.get_plan_type_display()}")
                self.stdout.write(f"   - Ativa: {'✅ Sim' if sub.is_active() else '❌ Não'}")
                if sub.end_date:
                    self.stdout.write(f"   - Válida até: {sub.end_date}")
            
            # Resetar senha
            with transaction.atomic():
                user.set_password(new_password)
                user.save()
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Senha resetada com sucesso!'))
            self.stdout.write(f'📧 Email: {user.email}')
            self.stdout.write(f'🔑 Nova senha: {new_password}')
            self.stdout.write(f'\n🌐 Faça login em: https://agenda-django-0dr6.onrender.com/accounts/login/')
            self.stdout.write(f'\n⚠️  IMPORTANTE: Altere a senha após o primeiro login!')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {str(e)}'))
