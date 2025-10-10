# Configuração das Variáveis de Ambiente (Secrets)

## Como adicionar os Secrets no Replit:

1. **Abra o painel de Secrets:**
   - Clique no ícone de "Tools" (🔧) na barra lateral esquerda
   - Selecione "Secrets"

2. **Adicione cada variável de ambiente:**

### Secrets Necessários:

```
SECRET_KEY=WiExXB+fKi/mA//OnyKyzkICuph0eKv6WI9KmD6zdvriZAXmknAKS725CjYqHqxUMO7+Ge0fVw8E0lXZ5SKXrQ==

MAIL_USERNAME=havyhost05@gmail.com

MAIL_PASSWORD=obeb xgqb qpjn rhnd

MERCADOPAGO_ACCESS_TOKEN=APP_USR-1870886593519827-100215-1a66c1141ae0c66812f8ff69e6441629-251913876

MP_PUBLIC_KEY=APP_USR-101fe950-862c-4457-a616-fb1e32ff1b55

WEBHOOK_URL=https://agenda-django-0dr6.onrender.com/payments/webhook/

DJANGO_SUPERUSER_EMAIL=leolulu842@gmail.com

DJANGO_SUPERUSER_PASSWORD=leoluh123

DEBUG=True
```

## Para cada secret:
- Clique em "New Secret"
- Cole o **nome** da variável (ex: SECRET_KEY)
- Cole o **valor** correspondente
- Clique em "Add Secret"

## Depois de adicionar os secrets:

1. **Reinicie o servidor:**
   - O servidor Django será reiniciado automaticamente
   
2. **Crie o superusuário (se necessário):**
   ```bash
   python manage.py initadmin
   ```

3. **Acesse o sistema:**
   - Página inicial: Use o botão "Webview" no Replit
   - Admin: /admin/
   - Login: /accounts/login/

## Status Atual:
✅ Servidor Django rodando na porta 5000
✅ Banco de dados SQLite configurado
✅ Migrações aplicadas
✅ Arquivos estáticos coletados
✅ Interface moderna carregando corretamente
✅ PWA e Service Worker funcionando
✅ Deployment configurado para produção (autoscale)

## Deployment (Publicar):
Quando estiver pronto para publicar:
1. Adicione todos os secrets listados acima
2. Clique no botão "Deploy" no Replit
3. O sistema usará Gunicorn em produção automaticamente

## Observações:
- O WEBHOOK_URL deve ser atualizado quando você fizer deploy
- Em produção, mude DEBUG=False
- As credenciais do Mercado Pago são para pagamentos via PIX
- O email é usado para notificações do sistema
