
from django import template
from admin_panel.models import PlanPricing

register = template.Library()

@register.simple_tag
def get_plan_price(plan_type):
    """Retorna o preço de um plano"""
    return PlanPricing.get_plan_price(plan_type)

@register.simple_tag  
def get_plan_description(plan_type):
    """Retorna a descrição de um plano"""
    try:
        plan = PlanPricing.objects.get(plan_type=plan_type, is_active=True)
        return plan.description
    except PlanPricing.DoesNotExist:
        defaults = {
            'trial_10': 'Teste gratuito por 10 dias com acesso completo',
            'vip_30': 'Plano premium com todos os recursos por 30 dias',
        }
        return defaults.get(plan_type, '')
