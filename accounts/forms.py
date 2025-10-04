from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction, models
from django.core.exceptions import ValidationError
from .models import UserProfile
from salons.models import Salon

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=30, required=True, label="Sobrenome")
    phone = forms.CharField(max_length=15, required=False, label="Telefone")

    # Campos do salão
    salon_name = forms.CharField(max_length=100, required=True, label="Nome do Salão")
    salon_address = forms.CharField(max_length=200, required=True, label="Endereço do Salão")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, plan_type='trial_10', **kwargs):
        super().__init__(*args, **kwargs)
        self.plan_type = plan_type
        # Customizar labels e placeholders
        self.fields['password1'].label = "Senha"
        self.fields['password2'].label = "Confirmar senha"
        self.fields['email'].widget.attrs['placeholder'] = "seu@email.com"
        self.fields['salon_name'].widget.attrs['placeholder'] = "Ex: Salão Beleza & Estilo"
        self.fields['salon_address'].widget.attrs['placeholder'] = "Ex: Rua das Flores, 123, Centro"

        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    def clean_email(self):
        """Validar se o email é único e normalizar"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()  # Normalizar email
            # Verificar se o email já existe tanto no campo email quanto no username
            if User.objects.filter(
                models.Q(username__iexact=email) | models.Q(email__iexact=email)
            ).exists():
                raise ValidationError('Este email já está sendo usado por outro usuário.')
        return email
    def save(self, commit=True):
        user = super().save(commit=False)
        normalized_email = self.cleaned_data['email'].lower().strip()
        user.email = normalized_email
        user.username = normalized_email  # Usar email como username
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            # Usar transação para garantir integridade dos dados
            with transaction.atomic():
                user.save()
                # Atualizar o perfil do usuário (sempre proprietário)
                profile = user.profile
                profile.user_type = 'owner'
                profile.phone = self.cleaned_data['phone'] or ''
                profile.save()
                # Criar salão automaticamente
                Salon.objects.create(
                    owner=user,
                    name=self.cleaned_data['salon_name'],
                    address=self.cleaned_data['salon_address'],
                    email=user.email,
                    phone=self.cleaned_data['phone'] or '',
                    city='',  # Será preenchido depois pelo usuário
                    state='',
                    zip_code=''
                )

                # Assinatura será criada após aprovação do pagamento via webhook
                # Não criar assinatura automaticamente aqui
        return user

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=30, required=True, label="Sobrenome")
    email = forms.EmailField(required=True, label="Email")
    class Meta:
        model = UserProfile
        fields = ['phone', 'birth_date', 'profile_picture']
        labels = {
            'phone': 'Telefone',
            'birth_date': 'Data de Nascimento',
            'profile_picture': 'Foto de Perfil',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        # Preencher campos do usuário se existir instância
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    def clean_email(self):
        """Validar se o email é único (excluindo o usuário atual)"""
        email = self.cleaned_data.get('email')
        if email and self.instance and self.instance.user:
            email = email.lower().strip()  # Normalizar email
            current_user = self.instance.user
            # Verificar se o email já existe tanto no campo email quanto no username
            if User.objects.filter(
                models.Q(username__iexact=email) | models.Q(email__iexact=email)
            ).exclude(pk=current_user.pk).exists():
                raise ValidationError('Este email já está sendo usado por outro usuário.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Usar transação para manter sincronia email/username
            with transaction.atomic():
                # Atualizar dados do usuário
                user = profile.user
                user.first_name = self.cleaned_data['first_name']
                user.last_name = self.cleaned_data['last_name']
                normalized_email = self.cleaned_data['email'].lower().strip()
                user.email = normalized_email
                user.username = normalized_email  # Manter sincronia email/username
                user.save()

                profile.save()

        return profile
