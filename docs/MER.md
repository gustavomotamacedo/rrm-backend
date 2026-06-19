# MER — Modelo Entidade Relacionamento

## Objetivo

Sistema multi-tenant para gestão de residências compartilhadas, permitindo administração de moradores, tarefas, agenda, finanças, estoque, saúde, pets, comunicação e listas de desejos.

A entidade central do domínio é a residência.

---

# Domínio de Identidade

## Users

Representa a identidade autenticável do sistema.

Responsabilidades:

* Login
* Recuperação de senha
* Controle de acesso

Relacionamentos:

* 1:1 Profile
* 1:N Residents
* 1:N Notifications

---

## Profiles

Representa informações cadastrais.

Responsabilidades:

* Nome
* Apelido
* Avatar
* Telefone

Relacionamentos:

* N:1 Users

---

## User Preferences

Preferências individuais do usuário.

Responsabilidades:

* Idioma
* Tema
* Horário silencioso
* Configuração de push

Relacionamentos:

* N:1 Users

---

# Domínio de Residência

## Residences

Tenant principal do sistema.

Responsabilidades:

* Nome
* Timezone
* Configurações globais

Relacionamentos:

* 1:N Residents
* 1:N Guests
* 1:N Tasks
* 1:N Events
* 1:N Messages
* 1:N Debits
* 1:N Items
* 1:N ShoppingItems
* 1:N Pets
* 1:N WishLists

---

## Residence Settings

Configurações operacionais da residência.

Responsabilidades:

* Método de rateio
* Retenção de convidados
* Configuração financeira

Relacionamentos:

* N:1 Residences

---

## Residents

Representa um morador.

Responsabilidades:

* Participação na residência
* Permissões
* Peso financeiro

Relacionamentos:

* N:1 Residences
* N:1 Users

---

## Guests

Visitantes temporários.

Responsabilidades:

* Controle de visitas
* Retenção temporária

Relacionamentos:

* N:1 Residences
* N:1 Residents

---

# Domínio de Tarefas

## Tasks

Tarefas domésticas.

Relacionamentos:

* N:1 Residences
* N:1 Residents
* N:1 Recurrences

---

## Task Executions

Histórico de execução.

Relacionamentos:

* N:1 Tasks
* N:1 Residents

---

# Domínio de Agenda

## Events

Eventos da residência.

Relacionamentos:

* N:1 Residences
* N:1 Residents
* N:1 Recurrences

---

## Event Guests

Participação de convidados.

Relacionamentos:

* N:1 Events
* N:1 Guests

---

# Domínio de Comunicação

## Messages

Recados e avisos.

Relacionamentos:

* N:1 Residences
* N:1 Residents

---

## Message Reads

Confirmação de leitura.

Relacionamentos:

* N:1 Messages
* N:1 Residents

---

# Domínio Financeiro

## Debits

Despesas pessoais ou compartilhadas.

Relacionamentos:

* N:1 Residences
* N:1 Residents
* N:1 Categories

---

## Debit Shares

Rateios.

Relacionamentos:

* N:1 Debits
* N:1 Residents

---

## Reimbursements

Reembolsos.

Relacionamentos:

* N:1 Debits
* N:1 Residents

---

# Domínio de Estoque

## Items

Itens controlados pela residência.

Relacionamentos:

* N:1 Residences
* N:1 Categories

---

## Item Movements

Movimentação de estoque.

Relacionamentos:

* N:1 Items
* N:1 Residents

---

## Shopping Items

Lista de compras.

Relacionamentos:

* N:1 Residences

---

# Domínio de Saúde

## Health Records

Registros médicos.

Relacionamentos:

* N:1 Residents (opcional)
* N:1 Pets (opcional)
* N:1 Categories

Regra:

* pertence a um morador OU a um pet

---

# Domínio de Pets

## Pets

Animais da residência.

Relacionamentos:

* N:1 Residences
* N:1 Residents

---

# Domínio de Desejos

## Wish Lists

Lista principal.

Relacionamentos:

* N:1 Residences
* N:1 Residents

---

## Wish List Items

Itens desejados.

Relacionamentos:

* N:1 Wish Lists
* N:1 Categories

---

# Domínio Compartilhado

## Categories

Categorias reutilizáveis.

Domínios:

* debit
* inventory
* health
* wish_list

Relacionamentos:

* 1:N Debits
* 1:N Items
* 1:N HealthRecords
* 1:N WishListItems

---

## Attachments

Anexos genéricos.

Relacionamentos:

* Polimórfico

Entidades suportadas:

* tasks
* events
* messages
* debits
* health_records
* pets

---

## Recurrences

Motor de recorrência.

Relacionamentos:

* 1:N Tasks
* 1:N Events

---

# Domínio de Notificações

## Notifications

Notificações lógicas.

Relacionamentos:

* N:1 Users

---

## Notification Deliveries

Entregas físicas.

Relacionamentos:

* N:1 Notifications
* N:1 Users
