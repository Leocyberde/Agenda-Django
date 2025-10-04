from django import forms
from django.contrib.auth.models import User
from .models import Salon, Service, Employee

class SalonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatar o valor da porcentagem como inteiro se for um número inteiro
        if self.instance and self.instance.pk and self.instance.cancellation_fee_percentage:
            percentage = self.instance.cancellation_fee_percentage
            if percentage == int(percentage):
                self.fields['cancellation_fee_percentage'].widget.attrs['value'] = str(int(percentage))
    
    class Meta:
        model = Salon
        exclude = ['owner']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            
            # Horários simplificados
            'weekdays_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'weekdays_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'saturday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'saturday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'sunday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'sunday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            
            # Status de funcionamento
            'is_temporarily_closed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'closed_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'closure_note': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Motivo do fechamento (opcional)'}),
            
            # Política de cancelamento
            'cancellation_policy_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
            'cancellation_fee_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '1', 
                'min': '0', 
                'max': '100',
                'placeholder': '10'
            }),
            'cancellation_hours_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        exclude = ['salon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EmployeeForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        label="Nome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        label="Sobrenome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        min_length=8,
        label="Senha",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Employee
        fields = ['services', 'is_active', 'payment_type', 'salary_amount', 'commission_percentage']
        widgets = {
            'services': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_payment_type'}),
            'salary_amount': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'id': 'id_salary_amount',
                'placeholder': 'Digite o valor'
            }),
            'commission_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'max': '100',
                'min': '0',
                'id': 'id_commission_percentage',
                'placeholder': 'Ex: 15.50'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        salon = kwargs.pop('salon', None)
        super().__init__(*args, **kwargs)
        if salon:
            self.fields['services'].queryset = salon.services.all()
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Um usuário com este email já existe.")
        return email

class EmployeeEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        label="Nome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        label="Sobrenome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Employee
        fields = ['services', 'is_active', 'payment_type', 'salary_amount', 'commission_percentage']
        widgets = {
            'services': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_payment_type_edit'}),
            'salary_amount': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'id': 'id_salary_amount_edit',
                'placeholder': 'Digite o valor'
            }),
            'commission_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'max': '100',
                'min': '0',
                'id': 'id_commission_percentage_edit',
                'placeholder': 'Ex: 15.50'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        salon = kwargs.pop('salon', None)
        super().__init__(*args, **kwargs)
        if salon:
            self.fields['services'].queryset = salon.services.all()
        if self.instance and self.instance.pk:
            # Preencher campos do usuário
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if self.instance and self.instance.pk:
            # Permitir o mesmo email do usuário atual
            if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
                raise forms.ValidationError("Um usuário com este email já existe.")
        else:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Um usuário com este email já existe.")
        return email
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        if commit:
            # Atualizar dados do usuário
            user = employee.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.username = self.cleaned_data['email']  # Usar email como username
            user.save()
            employee.save()
            self.save_m2m()  # Salvar many-to-many relationships
        return employee


class SalonStatusForm(forms.ModelForm):
    """Formulário específico para controlar status aberto/fechado do salão"""
    
    class Meta:
        model = Salon
        fields = ['is_temporarily_closed', 'closed_until', 'closure_note']
        widgets = {
            'is_temporarily_closed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'closed_until': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local',
                'placeholder': 'Deixe vazio para fechar indefinidamente'
            }),
            'closure_note': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Reforma, Feriado, Emergência...',
                'maxlength': 200
            }),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        is_closed = cleaned_data.get('is_temporarily_closed')
        closed_until = cleaned_data.get('closed_until')
        
        if is_closed and closed_until:
            from django.utils import timezone
            if closed_until <= timezone.now():
                raise forms.ValidationError('A data de reabertura deve ser no futuro.')
        
        return cleaned_data