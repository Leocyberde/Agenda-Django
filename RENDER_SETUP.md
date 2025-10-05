# Como fazer Deploy no Render

Este guia mostra como fazer deploy do sistema de agendamento de salão no Render.

## Pré-requisitos

1. Conta no Render (https://render.com)
2. Banco de dados PostgreSQL criado no Render

## Passos para Deploy

### 1. Configure o Banco de Dados PostgreSQL

Se você ainda não criou:

1. No dashboard do Render, clique em **New +** → **PostgreSQL**
2. Configure:
   - **Name**: `salon-booking-db` (ou nome de sua preferência)
   - **Database**: `salon_booking`
   - **User**: `salon_booking_user`
   - **Region**: escolha a mais próxima
   - **PostgreSQL Version**: 16
   - **Plan**: Free (ou o plano desejado)
3. Clique em **Create Database**
4. Aguarde a criação (status "Available")
5. **Copie a URL Externa (External Database URL)** - você vai precisar dela

### 2. Crie o Web Service

#### Opção A: Usando render.yaml (Recomendado)

1. Faça commit e push de todo o código para seu repositório Git
2. No dashboard do Render, clique em **New +** → **Blueprint**
3. Conecte seu repositório
4. O Render detectará automaticamente o arquivo `render.yaml`
5. Configure as variáveis de ambiente (veja seção abaixo)
6. Clique em **Apply**

#### Opção B: Configuração Manual

1. No dashboard do Render, clique em **New +** → **Web Service**
2. Conecte seu repositório GitHub/GitLab
3. Configure:
   - **Name**: `salon-booking`
   - **Environment**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn salon_booking.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan**: Free (ou o plano desejado)

### 3. Configure as Variáveis de Ambiente

No painel **Environment** do seu Web Service, adicione:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `DATABASE_URL` | `postgresql://user:password@host/database` | URL Externa do PostgreSQL copiada no passo 1 |
| `SECRET_KEY` | String aleatória de 50+ caracteres | Chave secreta do Django (use um gerador de senhas) |
| `DEBUG` | `False` | Desabilita modo debug em produção |
| `PYTHON_VERSION` | `3.12.0` | Versão do Python |
| `MERCADOPAGO_ACCESS_TOKEN` | Token de acesso do Mercado Pago | Token para processar pagamentos (obtenha em https://www.mercadopago.com.br/developers) |
| `WEBHOOK_BASE_URL` | `https://seu-app.onrender.com` | URL base da sua aplicação no Render (sem barra no final) |

#### Como gerar uma SECRET_KEY segura:

**Opção 1 - Usando Python:**
```python
import secrets
print(secrets.token_urlsafe(50))
```

**Opção 2 - Usar o gerador do Render:**
Ao criar a variável `SECRET_KEY`, o Render oferece a opção "Generate" para criar automaticamente.

**Opção 3 - Online:**
Use um gerador de senhas forte com pelo menos 50 caracteres.

### 4. Deploy

1. Após configurar as variáveis de ambiente, clique em **Save Changes**
2. O Render iniciará o build automaticamente
3. Aguarde o deploy completar (cerca de 5-10 minutos no primeiro deploy)
4. Quando o status mudar para "Live", seu app estará no ar!

### 5. Acesse sua Aplicação

- URL: `https://salon-booking.onrender.com` (ou o nome que você escolheu)
- Acesse `/admin` para o painel administrativo do Django
- Crie um superusuário (veja próxima seção)

### 6. Criar Superusuário (Admin)

Para criar um usuário admin no Django:

1. No dashboard do Render, vá para seu Web Service
2. Clique na aba **Shell**
3. Execute:
```bash
python manage.py createsuperuser
```
4. Siga as instruções para criar username, email e senha

## Estrutura de Arquivos para Deploy

Os seguintes arquivos foram criados/modificados para o deploy:

- `build.sh` - Script de build do Render
- `render.yaml` - Configuração Infrastructure-as-Code do Render
- `requirements.txt` - Dependências Python (com psycopg2-binary, dj-database-url, whitenoise)
- `salon_booking/settings.py` - Configurado para usar variáveis de ambiente

## Configurações Importantes

### Database

O settings.py agora detecta automaticamente:
- **Produção (Render)**: Usa PostgreSQL via `DATABASE_URL`
- **Desenvolvimento (Replit/Local)**: Usa SQLite

### Static Files

Os arquivos estáticos são servidos usando WhiteNoise:
- Automaticamente comprimidos e com cache
- Não precisa de servidor separado para arquivos estáticos

### Debug Mode

- **Desenvolvimento**: `DEBUG=True` (padrão se não definir a variável)
- **Produção**: `DEBUG=False` (configure a variável de ambiente)

## Configurar Webhook do Mercado Pago

Para que os pagamentos sejam processados automaticamente, é necessário configurar o webhook no painel do Mercado Pago:

### 1. Obter URL do Webhook

A URL do webhook será:
```
https://seu-app.onrender.com/payments/webhook/
```

Substitua `seu-app.onrender.com` pelo domínio real da sua aplicação no Render.

### 2. Configurar no Mercado Pago

1. Acesse o [Painel de Desenvolvedores do Mercado Pago](https://www.mercadopago.com.br/developers/panel)
2. Vá em **Suas integrações** → Selecione sua aplicação
3. No menu lateral, clique em **Webhooks**
4. Clique em **Configurar notificações**
5. Em **URL de produção**, cole: `https://seu-app.onrender.com/payments/webhook/`
6. Selecione os eventos:
   - ✅ **Pagamentos** (payment)
   - ✅ **Atualizações de pagamento** (payment.updated)
7. Clique em **Salvar**

### 3. Testar Webhook

Após configurar, você pode testar:

1. Faça um pagamento de teste na aplicação
2. Verifique os logs no Render (aba "Logs")
3. Procure por mensagens como: `🔔 WEBHOOK MERCADO PAGO RECEBIDO`

### 4. Variáveis de Ambiente Necessárias

Certifique-se de que as seguintes variáveis estão configuradas no Render:

- `MERCADOPAGO_ACCESS_TOKEN`: Token de acesso da sua aplicação no Mercado Pago
- `WEBHOOK_BASE_URL`: URL base da sua aplicação (ex: `https://seu-app.onrender.com`)

## Próximos Passos Após Deploy

1. **Criar dados iniciais**:
   - Crie planos de assinatura: `python manage.py setup_default_pricing`
   - Crie plano VIP: `python manage.py ensure_vip_plan`

2. **Configurar domínio personalizado** (opcional):
   - No Render, vá em Settings → Custom Domain
   - Adicione seu domínio e configure o DNS

3. **Monitoramento**:
   - Verifique logs em tempo real na aba "Logs"
   - Configure alertas para downtime

## Troubleshooting

### Build falha

- Verifique se `build.sh` tem permissões de execução
- Verifique os logs de build para mensagens de erro
- Confirme que `requirements.txt` está completo

### Database connection error

- Verifique se a variável `DATABASE_URL` está correta
- Confirme que o banco PostgreSQL está "Available"
- Use a URL **Externa**, não a interna

### Static files não carregam

- Execute `python manage.py collectstatic` localmente para testar
- Verifique se WhiteNoise está no MIDDLEWARE
- Confirme que `STATIC_ROOT` está configurado

### 502 Bad Gateway

- Verifique se o comando de start está correto
- Confirme que Gunicorn está instalado
- Verifique os logs da aplicação

## Custos

- **Free Tier**: Grátis por 750 horas/mês
- **Limitações Free**: 
  - App "hiberna" após 15 min de inatividade
  - PostgreSQL free expira após 90 dias
  - 512 MB RAM

Para produção, considere upgrade para plano pago.

## Suporte

- Documentação oficial: https://render.com/docs
- Comunidade Render: https://community.render.com
- Docs Django: https://docs.djangoproject.com/en/stable/howto/deployment/
