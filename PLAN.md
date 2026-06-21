# Planejamento de Rotas API REST

Baseado exclusivamente no modelo físico apresentado.

---

# Convenções

## Prefixo

```http
/api/v1
```

## Recursos

```text
users
profiles
residences
residents
tasks
events
messages
debits
inventory
pets
health-records
wish-lists
notifications
attachments
```

---

# 1. Autenticação

## Auth

```http
POST   /auth/register
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
POST   /auth/forgot-password
POST   /auth/reset-password
GET    /auth/me
```

---

# 2. Usuário

## Users

```http
GET    /users/me
PATCH  /users/me
DELETE /users/me
```

## Profile

```http
GET    /profile
PATCH  /profile
```

## Preferences

```http
GET    /preferences
PATCH  /preferences
```

---

# 3. Residências

## Residences

```http
GET    /residences
POST   /residences

GET    /residences/:id
PATCH  /residences/:id
DELETE /residences/:id
```

## Residence Settings

```http
GET    /residences/:id/settings
PATCH  /residences/:id/settings
```

---

# 4. Moradores

## Residents

```http
GET    /residences/:id/residents
POST   /residences/:id/residents

GET    /residents/:id
PATCH  /residents/:id
DELETE /residents/:id
```

### Convites

```http
POST   /residences/:id/invitations
GET    /invitations
POST   /invitations/:id/accept
POST   /invitations/:id/reject
```

> Embora não exista tabela ainda, a funcionalidade é obrigatória para onboarding.

---

# 5. Hóspedes

## Guests

```http
GET    /residences/:id/guests
POST   /residences/:id/guests

GET    /guests/:id
PATCH  /guests/:id
DELETE /guests/:id
```

---

# 6. Recorrência

## Recurrences

```http
POST   /recurrences
GET    /recurrences/:id
PATCH  /recurrences/:id
DELETE /recurrences/:id
```

---

# 7. Tarefas

## Tasks

```http
GET    /residences/:id/tasks
POST   /residences/:id/tasks

GET    /tasks/:id
PATCH  /tasks/:id
DELETE /tasks/:id
```

## Task Executions

```http
GET    /tasks/:id/executions
POST   /tasks/:id/executions
```

## Task Attachments

```http
POST   /tasks/:id/attachments
DELETE /tasks/:id/attachments/:attachment_id
```

---

# 8. Eventos

## Events

```http
GET    /residences/:id/events
POST   /residences/:id/events

GET    /events/:id
PATCH  /events/:id
DELETE /events/:id
```

## Event Guests

```http
POST   /events/:id/guests
PATCH  /events/:id/guests/:guest_id
DELETE /events/:id/guests/:guest_id
```

## Event Attachments

```http
POST   /events/:id/attachments
DELETE /events/:id/attachments/:attachment_id
```

---

# 9. Mural de Recados

## Messages

```http
GET    /residences/:id/messages
POST   /residences/:id/messages

GET    /messages/:id
PATCH  /messages/:id
DELETE /messages/:id
```

## Reads

```http
POST   /messages/:id/read
GET    /messages/:id/readers
```

## Attachments

```http
POST   /messages/:id/attachments
DELETE /messages/:id/attachments/:attachment_id
```

---

# 10. Categorias

## Categories

```http
GET    /categories
POST   /categories

GET    /categories/:id
PATCH  /categories/:id
DELETE /categories/:id
```

### Filtros

```http
GET /categories?domain=DEBIT
GET /categories?domain=INVENTORY
GET /categories?domain=HEALTH
GET /categories?domain=WISH_LIST
```

---

# 11. Financeiro

## Debits

```http
GET    /residences/:id/debits
POST   /residences/:id/debits

GET    /debits/:id
PATCH  /debits/:id
DELETE /debits/:id
```

## Shares

```http
POST   /debits/:id/shares
PATCH  /debits/:id/shares/:share_id
DELETE /debits/:id/shares/:share_id
```

## Reimbursements

```http
GET    /residences/:id/reimbursements
POST   /reimbursements

GET    /reimbursements/:id
PATCH  /reimbursements/:id
DELETE /reimbursements/:id
```

## Balances

```http
GET /residences/:id/balances
```

### Dashboard Financeiro

```http
GET /residences/:id/finance/summary
```

---

# 12. Estoque

## Items

```http
GET    /residences/:id/items
POST   /residences/:id/items

GET    /items/:id
PATCH  /items/:id
DELETE /items/:id
```

## Movements

```http
POST /items/:id/movements
GET  /items/:id/movements
```

### Alertas

```http
GET /residences/:id/items/low-stock
```

---

# 13. Compras

## Shopping Lists

```http
GET    /residences/:id/shopping-lists
POST   /residences/:id/shopping-lists

GET    /shopping-lists/:id
PATCH  /shopping-lists/:id
DELETE /shopping-lists/:id
```

## Shopping List Items

```http
POST   /shopping-lists/:id/items
PATCH  /shopping-lists/:id/items/:item_id
DELETE /shopping-lists/:id/items/:item_id
```

### Compra rápida

```http
POST /shopping-lists/:id/items/:item_id/purchase
```

---

# 14. Pets

## Pets

```http
GET    /residences/:id/pets
POST   /residences/:id/pets

GET    /pets/:id
PATCH  /pets/:id
DELETE /pets/:id
```

## Attachments

```http
POST   /pets/:id/attachments
DELETE /pets/:id/attachments/:attachment_id
```

---

# 15. Saúde

## Health Records

```http
GET    /health-records
POST   /health-records

GET    /health-records/:id
PATCH  /health-records/:id
DELETE /health-records/:id
```

### Filtros

```http
GET /health-records?resident_id=
GET /health-records?pet_id=
GET /health-records?type=
```

## Attachments

```http
POST   /health-records/:id/attachments
DELETE /health-records/:id/attachments/:attachment_id
```

---

# 16. Lista de Desejos

## Wish Lists

```http
GET    /residences/:id/wish-lists
POST   /residences/:id/wish-lists

GET    /wish-lists/:id
PATCH  /wish-lists/:id
DELETE /wish-lists/:id
```

## Wish List Items

```http
POST   /wish-lists/:id/items
PATCH  /wish-lists/:id/items/:item_id
DELETE /wish-lists/:id/items/:item_id
```

### Reservas

```http
POST   /wish-list-items/:id/reserve
POST   /wish-list-items/:id/unreserve
```

---

# 17. Arquivos

## Attachments

```http
POST   /attachments/upload
GET    /attachments/:id
DELETE /attachments/:id
```

### Download

```http
GET /attachments/:id/download
```

### Presigned URL

```http
POST /attachments/presigned-url
```

---

# 18. Notificações

## Notifications

```http
GET /notifications
GET /notifications/:id
```

### Leitura

```http
POST /notifications/:id/read
```

### Preferências

```http
GET   /notifications/preferences
PATCH /notifications/preferences
```

---

# 19. Auditoria

## Audit Logs

```http
GET /audit-logs
GET /audit-logs/:id
```

### Filtros

```http
GET /audit-logs?entity=
GET /audit-logs?user=
GET /audit-logs?from=
GET /audit-logs?to=
```

---

# 20. Dashboard

## Home

```http
GET /dashboard
```

Resposta consolidada:

* tarefas pendentes
* próximos eventos
* saldo financeiro
* estoque crítico
* hóspedes ativos
* notificações não lidas

---

# Priorização das Fases

Pelo modelo atual, visitantes são uma funcionalidade periférica. O produto gera valor imediatamente com:

* gestão da residência;
* tarefas;
* eventos;
* comunicação;
* financeiro;
* estoque.

Visitantes agregam conveniência, mas não resolvem nenhuma dor principal do sistema.

---

# Fase 1 — Core da Residência

Objetivo: tornar a residência operacional.

```text
Auth
Users
Profiles
Preferences

Residences
Residence Settings
Residents

Tasks
Task Executions

Events

Messages
Message Reads

Notifications

Attachments

Dashboard Home
```

---

# Fase 2 — Financeiro

Objetivo: resolver divisão de gastos.

```text
Categories

Debits
Debit Shares

Reimbursements

Resident Balances

Finance Summary
```

---

# Fase 3 — Estoque e Compras

Objetivo: gestão operacional da casa.

```text
Items
Item Movements

Shopping Lists
Shopping List Items

Low Stock Alerts
```

---

# Fase 4 — Saúde e Pets

Objetivo: informações compartilhadas da residência.

```text
Pets

Health Records

Pet Attachments

Health Attachments
```

---

# Fase 5 — Lista de Desejos

Objetivo: funcionalidades sociais.

```text
Wish Lists

Wish List Items

Reservations
```

---

# Fase 6 — Governança e Observabilidade

Objetivo: operação madura.

```text
Audit Logs

Advanced Notifications

Residence Reports

Administrative Dashboards
```

---

# Fase 7 — Visitantes

Objetivo: funcionalidades complementares.

```text
Guests

Event Guests

Guest History

Guest Expiration

Guest Analytics
```

Motivos:

* não impacta onboarding;
* não impacta retenção inicial;
* não impacta monetização;
* não impacta recorrência de uso diária.

Pode inclusive ser removido do MVP sem afetar a proposta principal do produto.

---

# Fase 8 — Inteligência e Automações

Objetivo: diferenciação competitiva.

```text
LLM Assistant

Task Suggestions

Financial Insights

Inventory Predictions

Smart Notifications

Automated Workflows
```

---

# Ordem Recomendada de Entrega

```text
1. Residência
2. Tarefas
3. Eventos
4. Comunicação
5. Financeiro
6. Estoque
7. Compras
8. Pets
9. Saúde
10. Lista de Desejos
11. Auditoria
12. Visitantes
13. IA
```

Se o objetivo for lançar um MVP comercial o mais rápido possível, visitantes podem ficar fora da versão 1.0 inteira.
