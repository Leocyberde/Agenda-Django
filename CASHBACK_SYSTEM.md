
# Sistema de Cashback - Documentação

## Como Funciona

O sistema de cashback rastreia automaticamente as compras dos usuários através dos links de afiliados e credita o cashback conforme configurado.

### Fluxo do Sistema

1. **Clique no Produto**: O usuário clica em "Comprar Produto" na loja
2. **Rastreamento**: Sistema cria um registro de `PurchaseTracking` com:
   - Dados do usuário e produto
   - IP, User Agent, e Referrer para auditoria
   - Status inicial: "pending"
   - ID único de rastreamento

3. **Redirecionamento**: Usuario é redirecionado para o link de afiliado com parâmetros de tracking:
   ```
   https://loja-afiliado.com/produto?utm_source=salon_booking&tracking_id=UUID
   ```

4. **Confirmação de Compra**: A loja de afiliados envia um webhook para:
   ```
   POST /admin-panel/webhook/purchase-confirmation/
   ```
   
   Payload:
   ```json
   {
     "tracking_id": "uuid-do-rastreamento",
     "order_id": "pedido-123",
     "purchase_amount": 89.90,
     "status": "confirmed"
   }
   ```

5. **Processamento do Cashback**: Sistema automaticamente:
   - Atualiza status da compra
   - Calcula cashback baseado no valor real
   - Cria transação de cashback
   - Atualiza saldo do usuário

### Modelos de Dados

#### PurchaseTracking
- Rastreia cada clique e compra
- Armazena dados de auditoria (IP, User Agent)
- Status: pending, confirmed, rejected, cancelled

#### CashbackTransaction
- Registra todas as movimentações de cashback
- Tipos: earned, paid, cancelled

#### UserCashbackBalance
- Saldo consolidado do usuário
- Atualizado automaticamente via transações

### Configuração do Webhook

Para integrar com sistemas de afiliados, configure o webhook endpoint:

**URL**: `https://seu-dominio.com/admin-panel/webhook/purchase-confirmation/`
**Método**: POST
**Autenticação**: Nenhuma (use validação por IP ou token se necessário)

### Exemplo de Integração

#### 1. Configurar Webhook na Loja de Afiliados
```javascript
// Exemplo para Hotmart, Monetizze, etc.
const webhook_url = "https://salon-booking.com/admin-panel/webhook/purchase-confirmation/";

// Configurar para enviar:
// - tracking_id (obtido do parâmetro utm)
// - order_id (ID do pedido)
// - purchase_amount (valor da compra)
// - status ("confirmed", "rejected", "cancelled")
```

#### 2. Webhook de Confirmação Manual (Para Testes)
```bash
curl -X POST https://salon-booking.com/admin-panel/webhook/purchase-confirmation/ \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_id": "uuid-do-rastreamento",
    "order_id": "PEDIDO123",
    "purchase_amount": 89.90,
    "status": "confirmed"
  }'
```

### Recursos Implementados

✅ **Rastreamento de Cliques**: Cada clique é registrado com dados de auditoria
✅ **Cashback Automático**: Calculado automaticamente após confirmação
✅ **Dashboard do Usuário**: Visualização de saldo e histórico
✅ **Webhook para Confirmação**: API para receber confirmações de compra
✅ **Solicitação de Saque**: Usuários podem solicitar pagamento do saldo
✅ **Painel Administrativo**: Gestão de cashbacks pelo admin
✅ **Auditoria Completa**: Logs e rastreamento detalhado

### Próximos Passos

1. **Integração com PIX**: Para pagamentos automáticos de cashback
2. **Notificações**: Email/SMS quando cashback é creditado
3. **Programa de Fidelidade**: Cashback progressivo baseado em volume
4. **Analytics**: Dashboard com métricas de conversão
5. **Anti-fraude**: Validações adicionais para prevenir abusos

### Configurações Recomendadas

- **Saque Mínimo**: R$ 10,00
- **Prazo de Processamento**: 30 dias úteis
- **Cashback Máximo por Produto**: 20%
- **Limite Mensal por Usuário**: R$ 500,00

### Monitoramento

Acompanhe as métricas em:
- `/admin-panel/cashback/admin/` - Painel administrativo
- Logs do sistema para debugging
- Dashboard de cada usuário
