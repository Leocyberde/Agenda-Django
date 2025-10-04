from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import mercadopago
import json
import logging

from .models import Payment
from admin_panel.models import PlanPricing
from subscriptions.models import Subscription

logger = logging.getLogger(__name__)

@login_required
def gerar_pix(request, plan_id):
    """Gera pagamento PIX usando Mercado Pago"""
    plan = get_object_or_404(PlanPricing, id=plan_id, is_active=True)
    
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        messages.error(request, 'Configuração de pagamento não disponível. Contate o administrador.')
        return redirect('subscriptions:detail')
    
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    
    # Criar registro de pagamento
    payment = Payment.objects.create(
        user=request.user,
        amount=plan.price,
        plan_type=plan.plan_type,
        status='pending'
    )
    
    # Criar pagamento PIX
    payment_data = {
        "transaction_amount": float(plan.price),
        "description": f"{plan.get_plan_type_display()} - Agende sua Beleza",
        "payment_method_id": "pix",
        "payer": {
            "email": request.user.email,
            "first_name": request.user.first_name or request.user.username,
            "last_name": request.user.last_name or "",
        },
        "external_reference": str(payment.id),
        "notification_url": settings.WEBHOOK_URL
    }
    
    try:
        logger.info(f"🔵 INICIANDO PAGAMENTO PIX")
        logger.info(f"👤 Usuário: {request.user.email}")
        logger.info(f"💰 Valor: R$ {plan.price}")
        logger.info(f"📦 Dados do pagamento: {payment_data}")
        
        payment_response = sdk.payment().create(payment_data)
        
        logger.info(f"📨 RESPOSTA COMPLETA DO MERCADO PAGO:")
        logger.info(f"Status: {payment_response.get('status')}")
        logger.info(f"Response: {json.dumps(payment_response.get('response', {}), indent=2)}")
        
        if payment_response["status"] != 201:
            logger.error(f"❌ ERRO: Status diferente de 201")
            logger.error(f"Resposta: {payment_response}")
            messages.error(request, f'Erro ao processar pagamento: Status {payment_response.get("status")}')
            payment.delete()
            return redirect('subscriptions:detail')
        
        payment_info = payment_response["response"]
        
        # Salvar informações do pagamento
        payment.payment_id = str(payment_info["id"])
        payment.save()
        logger.info(f"✅ Payment ID salvo: {payment.payment_id}")
        
        # Extrair informações do PIX - ESTRUTURA ATUALIZADA
        logger.info(f"🔍 === ANÁLISE COMPLETA DA RESPOSTA DO MERCADO PAGO ===")
        logger.info(f"📦 Resposta completa (JSON formatado):")
        logger.info(json.dumps(payment_info, indent=2, ensure_ascii=False))
        
        # Listar todas as chaves disponíveis no nível raiz
        logger.info(f"🔑 Chaves no nível raiz: {list(payment_info.keys())}")
        
        # Tentar diferentes caminhos para o QR Code
        qr_code = ""
        qr_code_base64 = ""
        
        # Caminho 1: point_of_interaction.transaction_data
        if "point_of_interaction" in payment_info:
            poi = payment_info["point_of_interaction"]
            logger.info(f"📍 point_of_interaction encontrado!")
            logger.info(f"   Tipo: {type(poi)}")
            logger.info(f"   Chaves: {list(poi.keys()) if isinstance(poi, dict) else 'N/A'}")
            logger.info(f"   Conteúdo: {json.dumps(poi, indent=2, ensure_ascii=False)}")
            
            if isinstance(poi, dict) and "transaction_data" in poi:
                tx_data = poi["transaction_data"]
                logger.info(f"💳 transaction_data encontrado!")
                logger.info(f"   Tipo: {type(tx_data)}")
                logger.info(f"   Chaves: {list(tx_data.keys()) if isinstance(tx_data, dict) else 'N/A'}")
                logger.info(f"   Conteúdo: {json.dumps(tx_data, indent=2, ensure_ascii=False)}")
                
                qr_code = tx_data.get("qr_code", "")
                qr_code_base64 = tx_data.get("qr_code_base64", "")
        else:
            logger.warning(f"⚠️ point_of_interaction NÃO encontrado na resposta!")
        
        # Caminho 2: Diretamente na resposta (algumas versões da API)
        if not qr_code:
            logger.info(f"🔄 Tentando extrair QR Code diretamente da resposta raiz...")
            qr_code = payment_info.get("qr_code", "")
            qr_code_base64 = payment_info.get("qr_code_base64", "")
        
        # Caminho 3: Tentar em 'pix' se existir
        if not qr_code and "pix" in payment_info:
            logger.info(f"🔄 Tentando extrair de payment_info['pix']...")
            pix_data = payment_info["pix"]
            logger.info(f"   Conteúdo de 'pix': {json.dumps(pix_data, indent=2, ensure_ascii=False)}")
            if isinstance(pix_data, dict):
                qr_code = pix_data.get("qr_code", "")
                qr_code_base64 = pix_data.get("qr_code_base64", "")
        
        logger.info(f"🎯 === RESULTADO FINAL ===")
        logger.info(f"QR Code (string): {'✅ SIM' if qr_code else '❌ NÃO'} - Tamanho: {len(qr_code) if qr_code else 0}")
        logger.info(f"QR Code (base64): {'✅ SIM' if qr_code_base64 else '❌ NÃO'} - Tamanho: {len(qr_code_base64) if qr_code_base64 else 0}")
        
        if qr_code:
            logger.info(f"📝 Primeiros 50 caracteres do QR Code: {qr_code[:50]}...")
        if qr_code_base64:
            logger.info(f"📝 Primeiros 50 caracteres do QR Code Base64: {qr_code_base64[:50]}...")
        
        if not qr_code and not qr_code_base64:
            logger.error(f"❌ === ERRO: QR CODE NÃO ENCONTRADO ===")
            logger.error(f"Estrutura completa recebida:")
            logger.error(json.dumps(payment_info, indent=2, ensure_ascii=False))
            
            # Criar mensagem de erro detalhada
            error_msg = 'Erro ao gerar QR Code PIX. '
            error_msg += f'Resposta recebida do Mercado Pago não contém QR Code. '
            error_msg += f'Status do pagamento: {payment_info.get("status", "desconhecido")}. '
            
            messages.error(request, error_msg + 'Verifique suas credenciais do Mercado Pago ou entre em contato com o suporte.')
            payment.delete()
            return redirect('subscriptions:detail')
        
        logger.info(f"✅ QR Code gerado com sucesso!")
        
        context = {
            'payment': payment,
            'plan': plan,
            'qr_code': qr_code,
            'qr_code_base64': qr_code_base64,
            'payment_id': payment_info["id"],
        }
        
        return render(request, 'payments/pix.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao gerar PIX: {e}", exc_info=True)
        messages.error(request, f'Erro ao gerar pagamento PIX: {str(e)}')
        payment.delete()
        return redirect('subscriptions:detail')

@login_required
def verificar_pagamento(request, payment_id):
    """Verifica status do pagamento via AJAX"""
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
        
        if payment.status == 'approved':
            return JsonResponse({
                'status': 'approved',
                'message': 'Pagamento aprovado!',
                'redirect': '/subscriptions/detail/'
            })
        elif payment.status == 'rejected':
            return JsonResponse({
                'status': 'rejected',
                'message': 'Pagamento rejeitado.'
            })
        else:
            return JsonResponse({
                'status': 'pending',
                'message': 'Aguardando pagamento...'
            })
            
    except Payment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Pagamento não encontrado'
        }, status=404)

@login_required
def checkout(request, plan_id):
    """Cria uma preferência de pagamento no Mercado Pago"""
    plan = get_object_or_404(PlanPricing, id=plan_id, is_active=True)
    
    logger.info(f"🔵 INICIANDO CHECKOUT")
    logger.info(f"👤 Usuário: {request.user.email}")
    logger.info(f"💰 Plano: {plan.get_plan_type_display()} - R$ {plan.price}")
    
    if not settings.MERCADOPAGO_ACCESS_TOKEN or not settings.MP_PUBLIC_KEY:
        logger.error(f"❌ Credenciais do Mercado Pago não configuradas")
        messages.error(request, 'Configuração de pagamento não disponível. Contate o administrador.')
        return redirect('subscriptions:detail')
    
    logger.info(f"✅ Credenciais do Mercado Pago encontradas")
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    
    payment = Payment.objects.create(
        user=request.user,
        amount=plan.price,
        plan_type=plan.plan_type,
        status='pending'
    )
    
    preference_data = {
        "items": [
            {
                "title": plan.get_plan_type_display(),
                "quantity": 1,
                "unit_price": float(plan.price),
                "currency_id": "BRL"
            }
        ],
        "payer": {
            "name": request.user.get_full_name() or request.user.username,
            "email": request.user.email
        },
        "back_urls": {
            "success": request.build_absolute_uri('/payments/success/'),
            "failure": request.build_absolute_uri('/payments/failure/'),
            "pending": request.build_absolute_uri('/payments/success/')
        },
        "auto_return": "approved",
        "external_reference": str(payment.id),
        "notification_url": settings.WEBHOOK_URL
    }
    
    try:
        preference_response = sdk.preference().create(preference_data)
        
        logger.info(f"📨 RESPOSTA DA PREFERÊNCIA:")
        logger.info(f"Status: {preference_response.get('status')}")
        logger.info(f"Response: {preference_response}")
        
        if preference_response["status"] != 201:
            logger.error(f"❌ ERRO: Status diferente de 201")
            logger.error(f"Resposta: {preference_response}")
            messages.error(request, f'Erro ao criar preferência de pagamento: Status {preference_response.get("status")}')
            payment.delete()
            return redirect('subscriptions:detail')
        
        preference = preference_response["response"]
        
        if 'id' not in preference:
            logger.error(f"❌ ERRO: ID não encontrado na resposta da preferência")
            logger.error(f"Resposta completa: {preference}")
            messages.error(request, 'Erro ao criar preferência de pagamento. Verifique suas credenciais do Mercado Pago.')
            payment.delete()
            return redirect('subscriptions:detail')
        
        payment.preference_id = preference["id"]
        payment.save()
        
        context = {
            'preference_id': preference["id"],
            'mp_public_key': settings.MP_PUBLIC_KEY,
            'plan': plan,
            'payment': payment
        }
        
        return render(request, 'payments/checkout.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao criar preferência: {e}", exc_info=True)
        messages.error(request, f'Erro ao processar pagamento: {str(e)}')
        payment.delete()
        return redirect('subscriptions:detail')

def payment_success(request):
    """Página de sucesso do pagamento"""
    payment_id = request.GET.get('payment_id')
    external_reference = request.GET.get('external_reference')
    
    context = {
        'payment_id': payment_id,
        'external_reference': external_reference
    }
    
    return render(request, 'payments/success.html', context)

def payment_failure(request):
    """Página de falha do pagamento"""
    return render(request, 'payments/failure.html')

@csrf_exempt
@require_http_methods(["POST"])
def webhook(request):
    """Webhook para receber notificações do Mercado Pago"""
    try:
        data = json.loads(request.body)
        logger.info(f"Webhook recebido: {data}")
        
        if data.get('type') == 'payment':
            payment_id = data['data']['id']
            
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            payment_info = sdk.payment().get(payment_id)
            payment_data = payment_info["response"]
            
            logger.info(f"Dados do pagamento: {payment_data}")
            
            external_reference = payment_data.get('external_reference')
            if not external_reference:
                logger.warning("External reference não encontrado")
                return JsonResponse({'status': 'error', 'message': 'External reference not found'}, status=400)
            
            try:
                payment = Payment.objects.get(id=external_reference)
            except Payment.DoesNotExist:
                logger.error(f"Payment com ID {external_reference} não encontrado")
                return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
            
            payment.payment_id = str(payment_id)
            old_status = payment.status
            new_status = payment_data['status']
            payment.status = new_status
            payment.save()
            
            logger.info(f"Status do pagamento atualizado: {old_status} -> {new_status}")
            
            if new_status == 'approved' and old_status != 'approved':
                subscription, created = Subscription.objects.get_or_create(
                    user=payment.user,
                    defaults={'plan_type': payment.plan_type}
                )
                
                # Atualizar ou renovar a assinatura
                subscription.plan_type = payment.plan_type
                subscription.start_date = timezone.now()
                
                # Calcular data de término baseado no tipo de plano
                if payment.plan_type == 'trial_10':
                    subscription.end_date = timezone.now() + timedelta(days=10)
                elif payment.plan_type == 'vip_30':
                    subscription.end_date = timezone.now() + timedelta(days=30)
                else:
                    subscription.end_date = timezone.now() + timedelta(days=30)
                
                subscription.status = 'active'
                subscription.last_renewal = timezone.now()
                subscription.save()
                
                logger.info(f"✅ Assinatura {payment.plan_type} ativada para {payment.user.email} até {subscription.end_date}")
                
                if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                    try:
                        send_mail(
                            subject='Pagamento Aprovado - Agende sua Beleza',
                            message=f'''
Olá {payment.user.get_full_name() or payment.user.username},

Seu pagamento foi aprovado com sucesso!

Detalhes:
- Valor: R$ {payment.amount}
- Plano: {subscription.get_plan_type_display()}
- Válido até: {subscription.end_date.strftime('%d/%m/%Y')}

Agora você tem acesso completo a todos os recursos do sistema.

Obrigado por escolher Agende sua Beleza!

Atenciosamente,
Equipe Agende sua Beleza
                            ''',
                            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@salonbooking.com',
                            recipient_list=[payment.user.email],
                            fail_silently=True,
                        )
                        logger.info(f"Email enviado para {payment.user.email}")
                    except Exception as e:
                        logger.error(f"Erro ao enviar email: {e}")
                else:
                    logger.warning("Configuração de email não disponível, email não enviado")
            
            return JsonResponse({'status': 'success'})
        
        return JsonResponse({'status': 'ignored'})
    
    except json.JSONDecodeError:
        logger.error("Erro ao decodificar JSON")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
