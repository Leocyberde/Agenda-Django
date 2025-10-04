from django.db import models
from django.contrib.auth.models import User

class Salon(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome do Salão")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    photo = models.ImageField(upload_to='salon_photos/', blank=True, null=True, verbose_name="Foto do Salão")
    address = models.CharField(max_length=200, verbose_name="Endereço")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    state = models.CharField(max_length=2, verbose_name="Estado")
    zip_code = models.CharField(max_length=10, verbose_name="CEP")
    phone = models.CharField(max_length=15, verbose_name="Telefone")
    email = models.EmailField(verbose_name="Email")
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salon', verbose_name="Proprietário")

    # Horários de funcionamento simplificados
    weekdays_open = models.TimeField(blank=True, null=True, verbose_name="Segunda à Sexta - Abertura")
    weekdays_close = models.TimeField(blank=True, null=True, verbose_name="Segunda à Sexta - Fechamento")
    saturday_open = models.TimeField(blank=True, null=True, verbose_name="Sábado - Abertura")
    saturday_close = models.TimeField(blank=True, null=True, verbose_name="Sábado - Fechamento")
    sunday_open = models.TimeField(blank=True, null=True, verbose_name="Domingo - Abertura")
    sunday_close = models.TimeField(blank=True, null=True, verbose_name="Domingo - Fechamento")

    # Status de funcionamento
    is_temporarily_closed = models.BooleanField(default=False, verbose_name="Temporariamente Fechado")
    closed_until = models.DateTimeField(blank=True, null=True, verbose_name="Fechado até")
    closure_note = models.CharField(max_length=200, blank=True, null=True, verbose_name="Motivo do Fechamento")
    
    # Política de cancelamento
    cancellation_policy_enabled = models.BooleanField(default=False, verbose_name="Política de Cancelamento Habilitada")
    cancellation_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=50.00,
        verbose_name="Multa de Cancelamento (%)",
        help_text="Porcentagem do valor do serviço cobrada como multa"
    )
    cancellation_hours_threshold = models.PositiveIntegerField(
        default=12,
        verbose_name="Prazo para Cancelamento sem Multa (horas)",
        help_text="Cancelamentos com menos tempo que isso serão multados"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_working_hours(self, day_of_week):
        """Retorna horário de funcionamento para um dia específico (0=segunda, 6=domingo)"""
        if 0 <= day_of_week <= 4:  # Segunda a sexta (0-4)
            return self.weekdays_open, self.weekdays_close
        elif day_of_week == 5:  # Sábado (5)
            return self.saturday_open, self.saturday_close
        elif day_of_week == 6:  # Domingo (6)
            return self.sunday_open, self.sunday_close
        return None, None
    
    def is_open_at(self, date_time):
        """Verifica se o salão está aberto em um determinado momento"""
        from django.utils import timezone
        
        # Verificar se está temporariamente fechado
        if self.is_temporarily_closed:
            # Se tem data limite, verificar se ainda está dentro do período
            if self.closed_until:
                if date_time < self.closed_until:
                    return False
                else:
                    # Período de fechamento expirou, remover status
                    self.is_temporarily_closed = False
                    self.closed_until = None
                    self.closure_note = None
                    self.save()
            else:
                # Fechado indefinidamente
                return False
        
        # Verificar horário de funcionamento
        day_of_week = date_time.weekday()
        open_time, close_time = self.get_working_hours(day_of_week)
        
        if not open_time or not close_time:
            return False  # Não funciona neste dia
            
        current_time = date_time.time()
        return open_time <= current_time <= close_time

    def get_cancellation_fee_percentage_display(self):
        """Retorna a porcentagem de multa formatada como inteiro se for um número inteiro"""
        if self.cancellation_fee_percentage == int(self.cancellation_fee_percentage):
            return int(self.cancellation_fee_percentage)
        return float(self.cancellation_fee_percentage)

    class Meta:
        verbose_name = "Salão"
        verbose_name_plural = "Salões"

class Service(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='services', verbose_name="Salão")
    name = models.CharField(max_length=100, verbose_name="Nome do Serviço")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    duration = models.PositiveIntegerField(verbose_name="Duração (minutos)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.salon.name} - {self.name}"

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ['name']

class Employee(models.Model):
    PAYMENT_CHOICES = [
        ('monthly', 'Mensal'),
        ('weekly', 'Semanal'),
        ('daily', 'Diário'),
        ('percentage', 'Porcentagem por Serviço'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile', verbose_name="Usuário")
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='employees', verbose_name="Salão")
    services = models.ManyToManyField(Service, blank=True, verbose_name="Serviços que pode executar")
    
    # Campos de pagamento
    payment_type = models.CharField(
        max_length=10, 
        choices=PAYMENT_CHOICES, 
        default='monthly', 
        verbose_name="Tipo de Pagamento"
    )
    salary_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Valor do Salário",
        help_text="Valor mensal, semanal ou diário conforme tipo escolhido"
    )
    commission_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Porcentagem de Comissão (%)",
        help_text="Porcentagem sobre cada serviço realizado (apenas se tipo for 'Porcentagem por Serviço')"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    hire_date = models.DateField(auto_now_add=True, verbose_name="Data de contratação")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.salon.name}"
    
    def calculate_monthly_cost(self):
        """Calcula o custo mensal estimado baseado no tipo de pagamento"""
        if self.payment_type == 'monthly':
            return self.salary_amount
        elif self.payment_type == 'weekly':
            return self.salary_amount * 4  # Aproximação: 4 semanas por mês
        elif self.payment_type == 'daily':
            return self.salary_amount * 22  # Aproximação: 22 dias úteis por mês
        elif self.payment_type == 'percentage':
            # Para porcentagem, retornamos 0 pois depende dos serviços realizados
            return 0.00
        return 0.00
    
    def get_payment_type_display_friendly(self):
        """Retorna descrição amigável do tipo de pagamento"""
        payment_dict = {
            'monthly': f"Mensal: R$ {self.salary_amount:.2f}",
            'weekly': f"Semanal: R$ {self.salary_amount:.2f}",
            'daily': f"Diário: R$ {self.salary_amount:.2f}",
            'percentage': f"Comissão: {self.commission_percentage:g}% por serviço"
        }
        return payment_dict.get(self.payment_type, "Não definido")

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        unique_together = ['user', 'salon']


class FinancialRecord(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Receita'),
        ('expense', 'Despesa'),
    ]
    
    EXPENSE_CATEGORIES = [
        ('employee_salary', 'Salário de Funcionário'),
        ('employee_commission', 'Comissão de Funcionário'),
        ('rent', 'Aluguel'),
        ('utilities', 'Contas (Água, Luz, Internet)'),
        ('products', 'Produtos e Materiais'),
        ('maintenance', 'Manutenção'),
        ('marketing', 'Marketing'),
        ('other', 'Outros'),
    ]
    
    INCOME_CATEGORIES = [
        ('service', 'Serviços Prestados'),
        ('products_sale', 'Venda de Produtos'),
        ('other_income', 'Outras Receitas'),
    ]
    
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='financial_records', verbose_name="Salão")
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES, verbose_name="Tipo de Transação")
    category = models.CharField(max_length=20, verbose_name="Categoria")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    description = models.CharField(max_length=200, verbose_name="Descrição")
    
    # Data de referência da transação
    reference_month = models.PositiveIntegerField(verbose_name="Mês de Referência (1-12)")
    reference_year = models.PositiveIntegerField(verbose_name="Ano de Referência")
    
    # Relacionamentos opcionais para rastreabilidade
    related_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Funcionário Relacionado")
    related_appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Agendamento Relacionado")
    
    # Campos de auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Criado por")
    
    def __str__(self):
        tipo = "Receita" if self.transaction_type == 'income' else "Despesa"
        return f"{self.salon.name} - {tipo}: R$ {self.amount:.2f} ({self.reference_month}/{self.reference_year})"
    
    def get_category_display_friendly(self):
        """Retorna a descrição amigável da categoria"""
        if self.transaction_type == 'expense':
            categories = dict(self.EXPENSE_CATEGORIES)
        else:
            categories = dict(self.INCOME_CATEGORIES)
        return categories.get(self.category, self.category)
    
    class Meta:
        verbose_name = "Registro Financeiro"
        verbose_name_plural = "Registros Financeiros"
        ordering = ['-reference_year', '-reference_month', '-created_at']
        indexes = [
            models.Index(fields=['salon', 'reference_year', 'reference_month']),
            models.Index(fields=['transaction_type', 'category']),
        ]