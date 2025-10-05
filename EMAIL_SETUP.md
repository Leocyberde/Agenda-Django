
# Configuração de Email

Para que o sistema envie emails após pagamentos aprovados, configure as seguintes variáveis de ambiente:

## Gmail (Recomendado para desenvolvimento)

1. Crie uma senha de aplicativo no Google:
   - Acesse: https://myaccount.google.com/apppasswords
   - Crie uma nova senha de aplicativo

2. Configure as variáveis no Replit (Secrets):
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=seu-email@gmail.com
   EMAIL_HOST_PASSWORD=sua-senha-de-aplicativo
   DEFAULT_FROM_EMAIL=seu-email@gmail.com
   ```

## Outros Provedores

### SendGrid
```
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=sua-api-key
DEFAULT_FROM_EMAIL=seu-email-verificado@dominio.com
```

### Mailgun
```
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_HOST_USER=postmaster@seu-dominio.mailgun.org
EMAIL_HOST_PASSWORD=sua-senha
DEFAULT_FROM_EMAIL=noreply@seu-dominio.com
```

## Testando Localmente (Desenvolvimento)

Para testar sem configurar email real, use o console backend:

```python
# Em settings.py (temporário)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Os emails aparecerão no console do servidor.
