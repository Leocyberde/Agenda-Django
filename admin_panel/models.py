from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


# class Product(models.Model):
    """Modelo para produtos de salão com links de afiliados"""
    
    CATEGORY_CHOICES = [
        ('shampoo', 'Shampoo'),
        ('condicionador', 'Condicionador'),
        ('mascara', 'Máscara Capilar'),
        ('oleo', 'Óleo Capilar'),
        ('creme', 'Creme de Pentear'),
        ('gel', 'Gel'),
        ('mousse', 'Mousse'),
        ('spray', 'Spray'),
        ('coloracao', 'Coloração'),
        ('descolorante', 'Descolorante'),
        ('tools', 'Ferramentas'),
        ('acessorios', 'Acessórios'),
        ('outros', 'Outros'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Nome do Produto')
    description = models.TextField(verbose_name='Descrição')
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        verbose_name='Categoria'
    )
    brand = models.CharField(max_length=100, verbose_name='Marca')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Preço (R$)'
    )
    affiliate_link = models.URLField(verbose_name='Link de Afiliado')
    image_url = models.URLField(
        blank=True, 
        null=True, 
        verbose_name='URL da Imagem'
    )
    is_featured = models.BooleanField(
        default=False, 
        verbose_name='Produto em Destaque'
    )
    cashback_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        verbose_name='Cashback (%)',
        help_text='Percentual de cashback que o comerciante receberá após a compra (0-100%)'
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name='Ativo'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='Atualizado em'
    )
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return f"{self.brand} - {self.name}"
    
    @property
    def price_formatted(self):
        """Retorna o preço formatado em reais"""
        return f"R$ {self.price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def cashback_amount(self):
        """Calcula o valor em reais do cashback"""
        if self.cashback_percentage > 0:
            return (self.price * self.cashback_percentage) / 100
        return Decimal('0.00')
    
    @property
    def cashback_amount_formatted(self):
        """Retorna o valor do cashback formatado em reais"""
        amount = self.cashback_amount
        return f"R$ {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def has_cashback(self):
        """Verifica se o produto oferece cashback"""
        return self.cashback_percentage > 0


class PlanPricing(models.Model):
    PLAN_CHOICES = [
        ('trial_10', 'Plano Explorador (10 dias)'),
        ('vip_30', 'Plano Revolucionário (30 dias)'),
    ]
    
    plan_type = models.CharField(
        max_length=10, 
        choices=PLAN_CHOICES, 
        unique=True,
        verbose_name="Tipo de Plano"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Preço (R$)"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrição"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_plan_type_display()} - R$ {self.price}"
    
    @classmethod
    def get_plan_price(cls, plan_type):
        """Retorna o preço de um plano específico"""
        try:
            plan = cls.objects.get(plan_type=plan_type, is_active=True)
            return plan.price
        except cls.DoesNotExist:
            # Valores padrão caso não existam na base
            defaults = {
                'trial_10': Decimal('0.00'),
                'vip_30': Decimal('49.90'),
            }
            return defaults.get(plan_type, Decimal('0.00'))
    
    class Meta:
        verbose_name = "Preço do Plano"
        verbose_name_plural = "Preços dos Planos"
        ordering = ['plan_type']




# class PurchaseTracking(models.Model):
    """Rastreia compras feitas através dos links de afiliados"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmada'),
        ('rejected', 'Rejeitada'),
        ('cancelled', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchases')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    
    # Dados da compra
    purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor da Compra')
    cashback_percentage_at_purchase = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='% Cashback na Compra',
        help_text='Percentual de cashback no momento da compra'
    )
    cashback_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Valor do Cashback'
    )
    
    # Rastreamento
    click_timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Clique no Link')
    purchase_confirmation_date = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name='Data de Confirmação da Compra'
    )
    
    # Status e controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    affiliate_order_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='ID do Pedido no Sistema de Afiliados'
    )
    
    # Dados adicionais para auditoria
    ip_address = models.GenericIPAddressField(verbose_name='IP do Usuário')
    user_agent = models.TextField(verbose_name='User Agent')
    referrer = models.URLField(blank=True, null=True, verbose_name='Página de Origem')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Compra {self.id} - {self.user.email} - {self.product.name}"
    
    @property
    def is_confirmed(self):
        return self.status == 'confirmed'
    
    @property
    def days_since_purchase(self):
        if self.purchase_confirmation_date:
            return (timezone.now() - self.purchase_confirmation_date).days
        return (timezone.now() - self.click_timestamp).days
    
    class Meta:
        verbose_name = "Rastreamento de Compra"
        verbose_name_plural = "Rastreamentos de Compras"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]


# class CashbackTransaction(models.Model):
    """Transações de cashback dos usuários"""
    
    TRANSACTION_TYPES = [
        ('earned', 'Cashback Ganho'),
        ('paid', 'Cashback Pago'),
        ('cancelled', 'Cashback Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cashback_transactions')
    purchase_tracking = models.OneToOneField(
        PurchaseTracking, 
        on_delete=models.CASCADE, 
        related_name='cashback_transaction'
    )
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor')
    description = models.CharField(max_length=200, verbose_name='Descrição')
    
    # Controle de pagamento
    payment_date = models.DateTimeField(blank=True, null=True, verbose_name='Data do Pagamento')
    payment_method = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        verbose_name='Método de Pagamento'
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Referência do Pagamento'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.user.email} - R$ {self.amount}"
    
    class Meta:
        verbose_name = "Transação de Cashback"
        verbose_name_plural = "Transações de Cashback"
        ordering = ['-created_at']


# class UserCashbackBalance(models.Model):
    """Saldo de cashback do usuário"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cashback_balance')
    total_earned = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Total Ganho'
    )
    total_paid = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Total Pago'
    )
    available_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name='Saldo Disponível'
    )
    
    last_payment_date = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name='Último Pagamento'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - Saldo: R$ {self.available_balance}"
    
    def update_balance(self):
        """Atualiza o saldo baseado nas transações"""
        earned = self.user.cashback_transactions.filter(
            transaction_type='earned'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        paid = self.user.cashback_transactions.filter(
            transaction_type='paid'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        self.total_earned = earned
        self.total_paid = paid
        self.available_balance = earned - paid
        self.save()
    
    class Meta:
        verbose_name = "Saldo de Cashback"
        verbose_name_plural = "Saldos de Cashback"
