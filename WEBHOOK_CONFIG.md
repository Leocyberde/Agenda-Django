# Configuração do Webhook do Mercado Pago

Este documento explica como configurar o webhook do Mercado Pago para processar pagamentos automaticamente no sistema de agendamento.

## O que é um Webhook?

Um webhook é uma URL que o Mercado Pago chama automaticamente quando um evento acontece (como aprovação de pagamento). Isso permite que o sistema processe pagamentos em tempo real sem necessidade de verificação manual.

## URL do Webhook

A URL do webhook do sistema é:
```
https://SEU-DOMINIO.onrender.com/payments/webhook/
```

**Importante**: Substitua `SEU-DOMINIO` pelo nome real da sua aplicação no Render.

Exemplo: Se sua aplicação está em `agenda-django-0dr6.onrender.com`, a URL será:
```
https://agenda-django-0dr6.onrender.com/payments/webhook/
```

## Passo a Passo para Configurar

### 1. Obter o Token de Acesso do Mercado Pago

1. Acesse: https://www.mercadopago.com.br/developers/panel
2. Faça login com sua conta Mercado Pago
3. Vá em **Suas integrações** ou crie uma nova aplicação
4. Copie o **Access Token** (Production ou Test, dependendo do ambiente)

### 2. Configurar Variáveis de Ambiente no Render

1. Acesse o [Dashboard do Render](https://dashboard.render.com/)
2. Selecione seu Web Service (ex: `agenda-django`)
3. Vá na aba **Environment**
4. Adicione as seguintes variáveis:

| Variável | Valor | Exemplo |
|----------|-------|---------|
| `MERCADOPAGO_ACCESS_TOKEN` | Seu token do Mercado Pago | `APP_USR-1234567890-abcdef-...` |
| `WEBHOOK_BASE_URL` | URL da sua aplicação | `https://agenda-django-0dr6.onrender.com` |

**Notas importantes**:
- Não coloque barra `/` no final da `WEBHOOK_BASE_URL`
- Use o token de **Produção** para ambiente real
- Use o token de **Teste** para ambiente de desenvolvimento

5. Clique em **Save Changes**
6. Aguarde o redeploy automático

### 3. Configurar Webhook no Mercado Pago

1. Acesse: https://www.mercadopago.com.br/developers/panel
2. Vá em **Suas integrações** → Selecione sua aplicação
3. No menu lateral, clique em **Webhooks**
4. Clique em **Configurar notificações** ou **Adicionar webhook**
5. Configure:
   - **URL de produção**: `https://SEU-DOMINIO.onrender.com/payments/webhook/`
   - **Eventos**: Selecione os seguintes:
     - ✅ Pagamentos (`payment`)
     - ✅ Atualizações de pagamento (`payment.updated`)
6. Clique em **Salvar**

### 4. Testar o Webhook

#### Teste Manual

1. Faça um pagamento de teste na aplicação
2. Acesse os **Logs** do Render:
   - Dashboard → Seu Web Service → Aba **Logs**
3. Procure por mensagens como:
   ```
   🔔 WEBHOOK MERCADO PAGO RECEBIDO
   📦 Dados completos: {...}
   ✅ PAGAMENTO APROVADO!
   ```

#### Teste via Mercado Pago

1. No painel do Mercado Pago, vá em **Webhooks**
2. Clique em **Testar webhook**
3. Envie uma notificação de teste
4. Verifique se o status mostra "Entregue com sucesso"

## Fluxo de Funcionamento

```
1. Cliente faz pagamento PIX
   ↓
2. Mercado Pago processa o pagamento
   ↓
3. Mercado Pago envia notificação para: /payments/webhook/
   ↓
4. Sistema recebe notificação e verifica status
   ↓
5. Se aprovado:
   - Cria usuário (se novo)
   - Ativa assinatura VIP
   - Envia email de boas-vindas
   ↓
6. Cliente recebe acesso ao sistema
```

## Variáveis de Ambiente Necessárias

### Obrigatórias para Pagamentos

| Variável | Descrição | Onde Obter |
|----------|-----------|------------|
| `MERCADOPAGO_ACCESS_TOKEN` | Token de acesso do MP | https://www.mercadopago.com.br/developers/panel |
| `WEBHOOK_BASE_URL` | URL base da aplicação | Dashboard do Render |

### Obrigatórias para Email

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `MAIL_USERNAME` | Email do remetente | `seu-email@gmail.com` |
| `MAIL_PASSWORD` | Senha de app do Gmail | `abcd efgh ijkl mnop` |

**Como obter senha de app do Gmail**:
1. Acesse: https://myaccount.google.com/security
2. Ative **Verificação em duas etapas**
3. Vá em **Senhas de app**
4. Gere uma senha para "Email"
5. Use essa senha na variável `MAIL_PASSWORD`

### Outras Variáveis Importantes

| Variável | Descrição | Valor Recomendado |
|----------|-----------|-------------------|
| `DATABASE_URL` | URL do PostgreSQL | Fornecida pelo Render |
| `SECRET_KEY` | Chave secreta do Django | String aleatória de 50+ caracteres |
| `DEBUG` | Modo debug | `False` (produção) |

## Troubleshooting

### Webhook não está sendo chamado

**Possíveis causas**:
- URL do webhook incorreta no Mercado Pago
- Aplicação não está acessível (verifique se está "Live" no Render)
- CSRF bloqueando requisições (já configurado corretamente no código)

**Solução**:
1. Verifique a URL no painel do Mercado Pago
2. Teste acessando manualmente: `https://SEU-DOMINIO.onrender.com/payments/webhook/`
3. Deve retornar erro 405 (Method Not Allowed) - isso é esperado para GET

### Pagamento não é processado

**Possíveis causas**:
- `MERCADOPAGO_ACCESS_TOKEN` não configurado ou inválido
- Webhook não está recebendo notificações
- Erro no processamento (verificar logs)

**Solução**:
1. Verifique se o token está correto no Render
2. Verifique os logs para mensagens de erro
3. Teste com pagamento de teste primeiro

### Email não é enviado

**Possíveis causas**:
- `MAIL_USERNAME` ou `MAIL_PASSWORD` não configurados
- Senha de app do Gmail incorreta
- Gmail bloqueando acesso

**Solução**:
1. Verifique as variáveis de ambiente
2. Gere nova senha de app no Gmail
3. Verifique os logs para erros de SMTP

### Usuário não é criado automaticamente

**Possíveis causas**:
- Email não está na descrição do pagamento
- Erro ao criar usuário (email duplicado, etc)
- Sessão expirada

**Solução**:
1. Verifique os logs para mensagens de erro
2. Confirme que o email está correto no pagamento
3. Verifique se o usuário já existe no banco

## Logs Importantes

Ao verificar os logs no Render, procure por:

### Webhook recebido
```
🔔 WEBHOOK MERCADO PAGO RECEBIDO
📦 Dados completos: {...}
```

### Pagamento aprovado
```
✅ PAGAMENTO APROVADO!
🎯 Processando ativação da assinatura
```

### Usuário criado
```
✅ Criando usuário com dados da sessão
✅ Usuário criado - ID: X, Username: email@example.com
```

### Email enviado
```
Email de boas-vindas enviado para email@example.com
```

### Erros comuns
```
❌ Erro ao buscar pagamento X no Mercado Pago
Pagamento não encontrado no banco: X
Erro no webhook do Mercado Pago: ...
```

## Segurança

### Boas Práticas

1. **Nunca compartilhe** o `MERCADOPAGO_ACCESS_TOKEN`
2. **Use tokens diferentes** para teste e produção
3. **Monitore os logs** regularmente para detectar problemas
4. **Configure alertas** no Render para erros críticos
5. **Teste sempre** em ambiente de teste antes de produção

### Validação de Webhook

O código já inclui validações de segurança:
- Verifica se o pagamento existe no banco
- Valida o status antes de processar
- Registra todas as notificações recebidas
- Evita processamento duplicado

## Suporte

### Documentação Oficial

- **Mercado Pago Webhooks**: https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks
- **Render Docs**: https://render.com/docs
- **Django Docs**: https://docs.djangoproject.com/

### Contato

Se precisar de ajuda:
1. Verifique os logs no Render
2. Consulte a documentação do Mercado Pago
3. Verifique se todas as variáveis de ambiente estão configuradas
4. Entre em contato com o suporte do Mercado Pago se o problema persistir

## Checklist de Configuração

Use este checklist para garantir que tudo está configurado:

- [ ] Token do Mercado Pago obtido
- [ ] Variável `MERCADOPAGO_ACCESS_TOKEN` configurada no Render
- [ ] Variável `WEBHOOK_BASE_URL` configurada no Render
- [ ] Webhook configurado no painel do Mercado Pago
- [ ] URL do webhook está correta (com `/payments/webhook/`)
- [ ] Eventos selecionados: `payment` e `payment.updated`
- [ ] Aplicação está "Live" no Render
- [ ] Teste de webhook realizado com sucesso
- [ ] Logs verificados e sem erros
- [ ] Pagamento de teste processado corretamente
- [ ] Email de boas-vindas recebido
- [ ] Usuário criado e assinatura ativada

## Conclusão

Com o webhook configurado corretamente, o sistema processará pagamentos automaticamente:
- ✅ Cria usuários novos
- ✅ Ativa assinaturas VIP
- ✅ Envia emails de boas-vindas
- ✅ Registra todas as transações

Tudo de forma automática e em tempo real! 🚀
