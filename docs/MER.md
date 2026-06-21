# MER (Modelo Entidade-Relacionamento)

## Premissas Arquiteturais

* Multi-tenant por residência.
* Um usuário só pode pertencer a uma residência.
* Soft delete em entidades de negócio.
* Auditoria completa.
* Categorias globais e por residência.
* Anexos com integridade referencial forte.
* Recorrência compartilhada entre tarefas e eventos.
* Financeiro pessoal e compartilhado coexistem.
* Pets não são moradores, mas pertencem à residência.
* Saúde pode pertencer a um morador ou a um pet.

---

# Identidade

## Users

Responsável pela autenticação.

### Relacionamentos

* 1:1 Profiles
* 1:1 UserPreferences
* 1:N Notifications
* 1:1 Residents

---

## Profiles

Dados cadastrais do usuário.

### Relacionamentos

* N:1 Users

---

## UserPreferences

Preferências operacionais.

### Relacionamentos

* N:1 Users

---

# Residência

## Residences

Agregador principal do sistema.

### Relacionamentos

* 1:1 ResidenceSettings
* 1:N Residents
* 1:N Guests
* 1:N Tasks
* 1:N Events
* 1:N Messages
* 1:N Debits
* 1:N Items
* 1:N ShoppingLists
* 1:N Pets
* 1:N WishLists
* 1:N Categories

---

## ResidenceSettings

Configurações globais.

### Relacionamentos

* N:1 Residences

---

## Residents

Moradores.

### Relacionamentos

* N:1 Users
* N:1 Residences

---

## Guests

Visitantes temporários.

### Relacionamentos

* N:1 Residences
* N:1 Residents (host)

---

# Operação

## Recurrences

Motor único de recorrência.

### Relacionamentos

* 1:N Tasks
* 1:N Events

---

## Tasks

Tarefas domésticas.

### Relacionamentos

* N:1 Residences
* N:1 Residents
* N:1 Recurrences
* 1:N TaskExecutions

---

## TaskExecutions

Histórico de execução.

### Relacionamentos

* N:1 Tasks
* N:1 Residents

---

## Events

Agenda.

### Relacionamentos

* N:1 Residences
* N:1 Residents
* N:1 Recurrences
* 1:N EventGuests

---

## EventGuests

Participação de visitantes.

### Relacionamentos

* N:1 Events
* N:1 Guests

---

# Comunicação

## Messages

Recados.

### Relacionamentos

* N:1 Residences
* 1:N MessageReads

---

## MessageReads

Confirmações de leitura.

### Relacionamentos

* N:1 Messages
* N:1 Residents

---

# Financeiro

## Debits

Despesas.

### Relacionamentos

* N:1 Residences
* N:1 Residents
* N:1 Categories
* 1:N DebitShares
* 1:N Reimbursements

---

## DebitShares

Rateios.

### Relacionamentos

* N:1 Debits
* N:1 Residents

---

## Reimbursements

Reembolsos.

### Relacionamentos

* N:1 Debits
* N:1 Residents

---

# Estoque

## Items

Itens de estoque.

### Relacionamentos

* N:1 Residences
* N:1 Categories
* 1:N ItemMovements

---

## ItemMovements

Movimentações.

### Relacionamentos

* N:1 Items
* N:1 Residents

---

## ShoppingLists

Listas de compras.

### Relacionamentos

* N:1 Residences
* 1:N ShoppingListItems

---

## ShoppingListItems

Itens da lista.

### Relacionamentos

* N:1 ShoppingLists

---

# Saúde

## HealthRecords

Prontuário simplificado.

### Relacionamentos

* N:1 Residents (opcional)
* N:1 Pets (opcional)
* N:1 Categories

---

# Pets

## Pets

Animais da residência.

### Relacionamentos

* N:1 Residences
* N:1 Residents
* 1:N HealthRecords

---

# Desejos

## WishLists

Lista principal.

### Relacionamentos

* N:1 Residences
* N:1 Residents
* 1:N WishListItems

---

## WishListItems

Itens desejados.

### Relacionamentos

* N:1 WishLists
* N:1 Categories

---

# Catálogos

## Categories

Categorias compartilhadas.

### Escopos

* Global
* Residência

### Domínios

* DEBIT
* INVENTORY
* HEALTH
* WISH_LIST

---

# Arquivos

## Attachments

Arquivo físico.

### Relacionamentos

* N:N Tasks
* N:N Events
* N:N Messages
* N:N Debits
* N:N HealthRecords
* N:N Pets
* N:N WishListItems

Implementados através de tabelas de ligação.

---

# Notificações

## Notifications

Evento lógico.

### Relacionamentos

* N:1 Users
* 1:N NotificationDeliveries

---

## NotificationDeliveries

Entrega física.

### Relacionamentos

* N:1 Notifications
* N:1 Users

---

# Auditoria

## AuditLogs

Responsável por registrar todas as alterações realizadas nas entidades do sistema.

### Objetivos

rastreabilidade
conformidade LGPD
investigação de incidentes
histórico operacional
suporte a auditorias futuras

### Relacionamentos

N:1 Users
N:1 Residences (opcional)

### Entidades auditáveis

residences
residents
guests
tasks
task_executions
events
messages
debits
reimbursements
items
item_movements
shopping_lists
shopping_list_items
pets
health_records
wish_lists
wish_list_items
categories
attachments
notifications