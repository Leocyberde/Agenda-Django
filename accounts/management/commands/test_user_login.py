
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class Command(BaseCommand):
    help = 'Testa se um usuário consegue fazer login com a senha fornecida'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email do usuário')
        parser.add_argument('password', type=str, help='Senha para testar')

    def handle(self, *args, **options):
        email = options['email'].lower().strip()
        password = options['password']
        
        try:
            # Buscar usuário
            user = User.objects.filter(email__iexact=email).first()
            
            if not user:
                self.stdout.write(self.style.ERROR(f'❌ Usuário não encontrado: {email}'))
                
                # Tentar buscar por username
                user = User.objects.filter(username__iexact=email).first()
                if user:
                    self.stdout.write(self.style.WARNING(f'⚠️ Encontrado por username: {user.username}'))
                else:
                    return
            
            self.stdout.write(f"👤 Usuário encontrado:")
            self.stdout.write(f"   - ID: {user.id}")
            self.stdout.write(f"   - Username: {user.username}")
            self.stdout.write(f"   - Email: {user.email}")
            self.stdout.write(f"   - Nome: {user.first_name} {user.last_name}")
            self.stdout.write(f"   - Ativo: {'✅ Sim' if user.is_active else '❌ Não'}")
            
            if hasattr(user, 'profile'):
                self.stdout.write(f"   - Tipo: {user.profile.get_user_type_display()}")
            
            if hasattr(user, 'subscription'):
                sub = user.subscription
                self.stdout.write(f"   - Assinatura: {sub.get_plan_type_display()}")
                self.stdout.write(f"   - Ativa: {'✅ Sim' if sub.is_active() else '❌ Não'}")
                if sub.end_date:
                    self.stdout.write(f"   - Válida até: {sub.end_date}")
            
            # Testar autenticação
            self.stdout.write(f"\n🔐 Testando autenticação...")
            auth_user = authenticate(username=user.username, password=password)
            
            if auth_user:
                self.stdout.write(self.style.SUCCESS(f'\n✅ AUTENTICAÇÃO BEM-SUCEDIDA!'))
                self.stdout.write(f'O usuário {email} PODE fazer login com a senha fornecida.')
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ AUTENTICAÇÃO FALHOU!'))
                self.stdout.write(f'A senha fornecida está INCORRETA para o usuário {email}')
                self.stdout.write(f'\n💡 Dica: Use o comando reset_user_password para redefinir a senha.')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {str(e)}'))
