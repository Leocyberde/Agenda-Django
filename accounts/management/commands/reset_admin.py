
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Reseta a senha do usuário administrador'

    def handle(self, *args, **options):
        email = 'leolulu842@gmail.com'
        password = 'leoluh123'
        
        try:
            # Buscar usuário por email
            user = User.objects.get(email=email)
            
            # Resetar senha
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Senha resetada com sucesso para {email}'))
            self.stdout.write(self.style.SUCCESS(f'Username: {user.username}'))
            self.stdout.write(self.style.SUCCESS(f'Email: {user.email}'))
            self.stdout.write(self.style.SUCCESS(f'É superusuário: {user.is_superuser}'))
            self.stdout.write(self.style.SUCCESS(f'É staff: {user.is_staff}'))
            
        except User.DoesNotExist:
            # Se não existe, criar o usuário
            self.stdout.write(self.style.WARNING(f'Usuário não encontrado. Criando novo superusuário...'))
            
            user = User.objects.create_superuser(
                username='leolulu842',
                email=email,
                password=password
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Superusuário criado com sucesso!'))
            self.stdout.write(self.style.SUCCESS(f'Username: {user.username}'))
            self.stdout.write(self.style.SUCCESS(f'Email: {user.email}'))
