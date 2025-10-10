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
import threading

from .models import Payment
from admin_panel.models import PlanPricing
from subscriptions.models import Subscription

logger = logging.getLogger(__name__)

def enviar_email_confirmacao_pagamento(user_email, user_name, amount, plan_name, end_date, payment_id):
    """
    Envia email de confirmação de pagamento em background (thread separada)
    """
    try:
        # Obter URL do site de forma segura
        site_url = settings.WEBHOOK_BASE_URL or 'https://agenda-django-0dr6.onrender.com'
        
        logger.info(f"📧 [BACKGROUND] Tentando enviar email para {user_email}...")
        send_mail(
            subject='✅ Pagamento Aprovado - Agende sua Beleza',
            message=f'''
Olá {user_name}!

🎉 Seu pagamento foi aprovado com sucesso!

📋 Detalhes da Assinatura:
━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Valor Pago: R$ {amount}
📦 Plano: {plan_name}
📅 Válido até: {end_date}
🆔 ID do Pagamento: {payment_id}

✨ Agora você tem acesso completo a todos os recursos do sistema!

Acesse: {site_url}

Obrigado por escolher Agende sua Beleza! 💖

Atenciosamente,
Equipe Agende sua Beleza
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@salonbooking.com',
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info(f"✅ [BACKGROUND] Email de confirmação ENVIADO com sucesso para {user_email}")
    except Exception as e:
        logger.error(f"❌ [BACKGROUND] ERRO ao enviar email: {e}", exc_info=True)
        logger.error(f"❌ [BACKGROUND] Tipo do erro: {type(e).__name__}")
        logger.error(f"❌ [BACKGROUND] Mensagem: {str(e)}")

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
                'redirect': '/subscriptions/'
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
def aprovar_pagamento_manual(request, payment_id):
    """APENAS PARA TESTE: Aprova pagamento manualmente"""
    if not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para fazer isso.')
        return redirect('subscriptions:detail')
    
    try:
        payment = Payment.objects.get(id=payment_id)
        
        if payment.status == 'approved':
            messages.info(request, 'Pagamento já foi aprovado anteriormente.')
            return redirect('admin_panel:dashboard')
        
        # Aprovar pagamento
        payment.status = 'approved'
        payment.save()
        
        # Criar/atualizar assinatura
        subscription, created = Subscription.objects.get_or_create(
            user=payment.user,
            defaults={'plan_type': payment.plan_type}
        )
        
        subscription.plan_type = payment.plan_type
        subscription.start_date = timezone.now()
        subscription.status = 'active'
        subscription.last_renewal = timezone.now()
        
        if payment.plan_type == 'trial_10':
            subscription.end_date = timezone.now() + timedelta(days=10)
        elif payment.plan_type == 'vip_30':
            subscription.end_date = timezone.now() + timedelta(days=30)
        else:
            subscription.end_date = timezone.now() + timedelta(days=30)
        
        subscription.save()
        
        logger.info(f"✅ [MANUAL] Pagamento {payment_id} aprovado para {payment.user.email}")
        messages.success(request, f'Pagamento aprovado! Assinatura ativada até {subscription.end_date.strftime("%d/%m/%Y")}')
        
        return redirect('admin_panel:owner_detail', owner_id=payment.user.profile.id)
        
    except Payment.DoesNotExist:
        messages.error(request, 'Pagamento não encontrado.')
        return redirect('admin_panel:dashboard')
    except Exception as e:
        logger.error(f"Erro ao aprovar pagamento: {e}")
        messages.error(request, f'Erro ao aprovar pagamento: {str(e)}')
        return redirect('admin_panel:dashboard')

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
@require_http_methods(["POST", "GET"])
def webhook(request):
    """Webhook para receber notificações do Mercado Pago"""
    try:
        # 1. Tentar obter o ID e o TIPO de notificação dos parâmetros GET/URL
        # Este é o formato padrão que o Mercado Pago usa para notificação V4
        # Ex: /payments/webhook?data.id=123456789&type=payment
        
        # O ID do pagamento é o dado mais importante
        payment_id_from_get = request.GET.get('data.id') or request.GET.get('id')
        
        # O tipo de notificação ('payment', 'refund', etc.)
        notification_type = request.GET.get('type') or request.GET.get('topic')
        
        logger.info(f"🔔 WEBHOOK MERCADO PAGO RECEBIDO")
        logger.info(f"📦 Método: {request.method}")
        logger.info(f"📌 Tipo (GET): {notification_type}")
        logger.info(f"💳 ID (GET): {payment_id_from_get}")

        # Se for um GET, apenas confirmar que o endpoint está ativo.
        if request.method == 'GET':
            if payment_id_from_get and notification_type:
                # Se o MP estiver validando (enviando GET com params), vamos processar,
                # mas o processamento real é melhor feito com POST. Aqui, apenas confirmamos o recebimento.
                logger.info(f"✅ Requisição GET com parâmetros de notificação. Retornando 200.")
                return JsonResponse({'status': 'received_get', 'id': payment_id_from_get})
            
            logger.info(f"✅ Requisição GET simples. Webhook ativo.")
            return JsonResponse({'status': 'webhook_active'})

        # 2. Processar POST (A requisição real de notificação)
        
        # Tentar carregar o corpo JSON. Se falhar, é um Bad Request por JSON inválido.
        try:
            data = json.loads(request.body)
            logger.info(f"📦 Dados parseados do BODY (JSON): {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            # Captura a exceção se o corpo não for JSON (explicando os 400 Bad Request)
            logger.error(f"❌ Erro ao decodificar JSON: Corpo da requisição não é um JSON válido. Body: {request.body.decode('utf-8')}")
            # Se a falha for aqui, e não houver ID no GET, não há o que processar.
            if not payment_id_from_get:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON in POST body or missing ID in GET parameters'}, status=400)
            
            # Se houver ID no GET, vamos continuar, pois pode ser uma notificação malformada com ID na URL.
            data = {} # Usar um dicionário vazio para evitar erros posteriores

        # 3. Determinar o ID e o TIPO (prioridade: GET, depois JSON Body)
        
        # Se o ID já veio do GET, usamos ele.
        payment_id = payment_id_from_get
        
        # Se não veio do GET, tentamos extrair do corpo JSON.
        if not payment_id:
            payment_id = data.get('data', {}).get('id') or data.get('id')
            
        # Se o tipo não veio do GET, tentamos extrair do corpo JSON.
        if not notification_type:
            notification_type = data.get('type') or data.get('topic')
        
        logger.info(f"📌 Tipo de notificação (FINAL): {notification_type}")
        logger.info(f"💳 Payment ID (FINAL): {payment_id}")

        if notification_type == 'payment':
            
            if not payment_id:
                logger.error("❌ Payment ID não encontrado na notificação (GET ou BODY)")
                return JsonResponse({'status': 'error', 'message': 'Payment ID not found in notification'}, status=400)
            
            # --- O restante da sua lógica (Buscar no MP, Buscar no BD, Atualizar status, Assinatura) pode continuar daqui ---

            # Buscar informações do pagamento no Mercado Pago
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            # ... (O resto do seu código permanece o mesmo, começando daqui: payment_info = sdk.payment().get(payment_id)) ...
            
            # ------------------------------------------------------------------------------------------------------------------
            
            payment_info = sdk.payment().get(payment_id)
            
            logger.info(f"📨 Resposta do Mercado Pago: Status={payment_info.get('status')}")
            
            if payment_info["status"] != 200:
                logger.error(f"❌ Erro ao buscar pagamento: {payment_info}")
                return JsonResponse({'status': 'error', 'message': 'Failed to fetch payment'}, status=400)
            
            payment_data = payment_info["response"]
            logger.info(f"💰 Dados do pagamento: {json.dumps(payment_data, indent=2)}")
            
            # Buscar external_reference
            external_reference = payment_data.get('external_reference')
            payment = None
            if external_reference:
                logger.info(f"🔍 Tentando buscar Payment pelo external_reference (ID interno): {external_reference}")
                try:
                    payment = Payment.objects.get(id=external_reference)
                    logger.info(f"✅ Pagamento encontrado pelo ID interno: {payment.id}")
                except Payment.DoesNotExist:
                    logger.warning(f"⚠️ Payment com ID interno {external_reference} não encontrado. Tentando buscar pelo payment_id do Mercado Pago.")
            
            if not payment and payment_id:
                logger.info(f"🔍 Tentando buscar Payment pelo payment_id do Mercado Pago: {payment_id}")
                try:
                    payment = Payment.objects.get(payment_id=str(payment_id))
                    logger.info(f"✅ Pagamento encontrado pelo payment_id do Mercado Pago: {payment.id}")
                except Payment.DoesNotExist:
                    logger.error(f"❌ Nenhum pagamento encontrado com payment_id={payment_id} ou external_reference={external_reference}")
                    return JsonResponse({"status": "error", "message": "Payment not found"}, status=404)
            
            if not payment:
                logger.error(f"❌ Não foi possível encontrar o Payment correspondente para payment_id={payment_id} e external_reference={external_reference}")
                return JsonResponse({"status": "error", "message": "Payment not found"}, status=404)

            
            # Atualizar status do pagamento
            old_status = payment.status
            new_status = payment_data.get('status', 'pending')
            
            logger.info(f"🔄 Atualizando status: {old_status} -> {new_status}")
            
            payment.payment_id = str(payment_id)
            payment.status = new_status
            payment.save()
            
            logger.info(f"💾 Pagamento {payment.id} salvo com status {new_status}")
            
            # Se o pagamento foi aprovado, ativar/renovar assinatura
            if new_status == 'approved' and old_status != 'approved':
                logger.info(f"✅ PAGAMENTO APROVADO! Processando assinatura...")
                
                try:
                    # Buscar ou criar assinatura
                    subscription, created = Subscription.objects.get_or_create(
                        user=payment.user,
                        defaults={
                            'plan_type': payment.plan_type,
                            'status': 'active'
                        }
                    )
                    
                    if created:
                        logger.info(f"📝 Nova assinatura criada para {payment.user.email}")
                    else:
                        logger.info(f"🔄 Assinatura existente encontrada, atualizando...")
                    
                    # Atualizar dados da assinatura
                    subscription.plan_type = payment.plan_type
                    subscription.start_date = timezone.now()
                    subscription.status = 'active'
                    subscription.last_renewal = timezone.now()
                    
                    # Calcular data de término
                    if payment.plan_type == 'trial_10':
                        subscription.end_date = timezone.now() + timedelta(days=10)
                        logger.info(f"📅 Plano Trial: 10 dias")
                    elif payment.plan_type == 'vip_30':
                        subscription.end_date = timezone.now() + timedelta(days=30)
                        logger.info(f"📅 Plano VIP: 30 dias")
                    else:
                        subscription.end_date = timezone.now() + timedelta(days=30)
                        logger.info(f"📅 Plano padrão: 30 dias")
                    
                    subscription.save()
                    
                    logger.info(f"✅ ASSINATURA ATIVADA!")
                    # ... (O resto da sua lógica de envio de email em background e retorno de sucesso) ...
                    
                    # Enviar email de confirmação EM SEGUNDO PLANO (background)
                    logger.info(f"📧 Preparando para enviar email em BACKGROUND...")
                    
                    # A configuração de email agora é via SMTP do Gmail, não há necessidade de verificar SENDGRID_API_KEY
                    if settings.DEFAULT_FROM_EMAIL: # Verifica apenas se o email remetente está configurado
                        # Criar thread para enviar email em background
                        email_thread = threading.Thread(
                            target=enviar_email_confirmacao_pagamento,
                            args=(
                                payment.user.email,
                                payment.user.get_full_name() or payment.user.username,
                                payment.amount,
                                subscription.get_plan_type_display(),
                                subscription.end_date.strftime('%d/%m/%Y às %H:%M'),
                                payment_id
                            ),
                            daemon=True
                        )
                        email_thread.start()
                        logger.info(f"✅ Thread de email iniciada em BACKGROUND (não vai bloquear a resposta do webhook)")
                    else:
                        logger.warning("⚠️ Configuração de email não disponível")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar assinatura: {e}", exc_info=True)
                    return JsonResponse({'status': 'error', 'message': f'Subscription error: {str(e)}'}, status=500)
            
            elif new_status == 'rejected':
                logger.warning(f"❌ Pagamento {payment_id} foi REJEITADO")
            elif new_status == 'cancelled':
                logger.warning(f"❌ Pagamento {payment_id} foi CANCELADO")
            else:
                logger.info(f"⏳ Pagamento {payment_id} está {new_status}")
            
            return JsonResponse({
                'status': 'success',
                'payment_id': str(payment_id),
                'payment_status': new_status,
                'subscription_activated': new_status == 'approved'
            })
        
        logger.info(f"ℹ️ Notificação ignorada: tipo {notification_type}")
        return JsonResponse({'status': 'ignored', 'type': notification_type})
    
    except Exception as e:
        logger.error(f"❌ ERRO NO WEBHOOK: {e}", exc_info=True)
        # Este 500 indica um erro interno não relacionado ao JSON
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
