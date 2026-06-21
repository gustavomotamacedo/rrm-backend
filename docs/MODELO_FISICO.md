# MODELO FÍSICO (3FN)

### Convenções

#### Extensões

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
```

#### Chaves

```text
PK = UUID
FK = UUID
```

#### Auditoria Padrão

Aplicada em todas as entidades de negócio.

```text
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL

created_by UUID NULL
updated_by UUID NULL

deleted_at TIMESTAMPTZ NULL
deleted_by UUID NULL
```

---

## IDENTIDADE

### users

| campo         | tipo          |
| ------------- | ------------- |
| id            | uuid pk       |
| email         | citext unique |
| password_hash | text          |
| last_login_at | timestamptz   |

---

### profiles

| campo      | tipo           |
| ---------- | -------------- |
| id         | uuid pk        |
| user_id    | uuid fk unique |
| first_name | varchar(100)   |
| last_name  | varchar(100)   |
| nickname   | varchar(100)   |
| phone      | varchar(30)    |
| avatar_url | text           |
| birth_date | date           |

---

### user_preferences

| campo             | tipo           |
| ----------------- | -------------- |
| id                | uuid pk        |
| user_id           | uuid fk unique |
| language          | varchar(10)    |
| theme             | varchar(20)    |
| push_enabled      | boolean        |
| quiet_hours_start | time           |
| quiet_hours_end   | time           |

---

## RESIDÊNCIA

### residences

| campo    | tipo         |
| -------- | ------------ |
| id       | uuid pk      |
| name     | varchar(200) |
| timezone | varchar(100) |

---

### residence_settings

| campo                  | tipo           |
| ---------------------- | -------------- |
| id                     | uuid pk        |
| residence_id           | uuid fk unique |
| financial_split_method | enum           |
| guest_retention_days   | integer        |
| notifications_enabled  | boolean        |
| default_currency       | varchar(10)    |

---

### residents

| campo         | tipo           |
| ------------- | -------------- |
| id            | uuid pk        |
| residence_id  | uuid fk        |
| user_id       | uuid fk unique |
| role          | resident_role  |
| income_weight | numeric(10,4)  |
| joined_at     | timestamptz    |
| left_at       | timestamptz    |

---

### guests

| campo            | tipo         |
| ---------------- | ------------ |
| id               | uuid pk      |
| residence_id     | uuid fk      |
| host_resident_id | uuid fk      |
| name             | varchar(200) |
| arrival_date     | date         |
| departure_date   | date         |
| notes            | text         |
| expires_at       | timestamptz  |

---

## RECORRÊNCIA

### recurrences

| campo          | tipo        |
| -------------- | ----------- |
| id             | uuid pk     |
| frequency      | enum        |
| interval_value | integer     |
| by_week_day    | varchar(50) |
| by_month_day   | integer     |
| start_date     | date        |
| end_date       | date        |

---

## TAREFAS

### tasks

| campo                | tipo         |
| -------------------- | ------------ |
| id                   | uuid pk      |
| residence_id         | uuid fk      |
| assigned_resident_id | uuid fk      |
| recurrence_id        | uuid fk null |
| title                | varchar(255) |
| description          | text         |
| status               | enum         |
| due_at               | timestamptz  |
| completed_at         | timestamptz  |

---

### task_executions

| campo       | tipo        |
| ----------- | ----------- |
| id          | uuid pk     |
| task_id     | uuid fk     |
| resident_id | uuid fk     |
| executed_at | timestamptz |
| notes       | text        |

---

## AGENDA

### events

| campo             | tipo         |
| ----------------- | ------------ |
| id                | uuid pk      |
| residence_id      | uuid fk      |
| owner_resident_id | uuid fk      |
| recurrence_id     | uuid fk null |
| title             | varchar(255) |
| description       | text         |
| start_at          | timestamptz  |
| end_at            | timestamptz  |
| generate_task     | boolean      |

---

### event_guests

| campo             | tipo    |
| ----------------- | ------- |
| id                | uuid pk |
| event_id          | uuid fk |
| guest_id          | uuid fk |
| attendance_status | enum    |

---

## COMUNICAÇÃO

### messages

| campo        | tipo         |
| ------------ | ------------ |
| id           | uuid pk      |
| residence_id | uuid fk      |
| title        | varchar(255) |
| body         | text         |
| pinned       | boolean      |
| expires_at   | timestamptz  |

---

### message_reads

| campo       | tipo        |
| ----------- | ----------- |
| id          | uuid pk     |
| message_id  | uuid fk     |
| resident_id | uuid fk     |
| read_at     | timestamptz |

---

## FINANCEIRO

### categories

| campo        | tipo            |
| ------------ | --------------- |
| id           | uuid pk         |
| residence_id | uuid fk null    |
| is_system    | boolean         |
| domain       | category_domain |
| name         | varchar(100)    |
| description  | text            |

---

### debits

| campo             | tipo          |
| ----------------- | ------------- |
| id                | uuid pk       |
| residence_id      | uuid fk       |
| payer_resident_id | uuid fk       |
| category_id       | uuid fk       |
| visibility        | enum          |
| amount            | numeric(14,2) |
| description       | text          |
| due_date          | date          |
| paid_at           | timestamptz   |

---

### debit_shares

| campo       | tipo          |
| ----------- | ------------- |
| id          | uuid pk       |
| debit_id    | uuid fk       |
| resident_id | uuid fk       |
| amount      | numeric(14,2) |

---

### reimbursements

| campo            | tipo          |
| ---------------- | ------------- |
| id               | uuid pk       |
| debit_id         | uuid fk       |
| from_resident_id | uuid fk       |
| to_resident_id   | uuid fk       |
| amount           | numeric(14,2) |
| paid_at          | timestamptz   |

---

### resident_balances

| campo                | tipo          |
| -------------------- | ------------- |
| id                   | uuid pk       |
| residence_id         | uuid fk       |
| creditor_resident_id | uuid fk       |
| debtor_resident_id   | uuid fk       |
| amount               | numeric(14,2) |
| updated_at           | timestamptz   |

---

## ESTOQUE

### items

| campo            | tipo          |
| ---------------- | ------------- |
| id               | uuid pk       |
| residence_id     | uuid fk       |
| category_id      | uuid fk       |
| name             | varchar(255)  |
| quantity         | numeric(12,3) |
| minimum_quantity | numeric(12,3) |
| unit             | varchar(20)   |

---

### item_movements

| campo         | tipo          |
| ------------- | ------------- |
| id            | uuid pk       |
| item_id       | uuid fk       |
| resident_id   | uuid fk       |
| movement_type | enum          |
| quantity      | numeric(12,3) |

---

### shopping_lists

| campo        | tipo         |
| ------------ | ------------ |
| id           | uuid pk      |
| residence_id | uuid fk      |
| title        | varchar(255) |

---

### shopping_list_items

| campo            | tipo          |
| ---------------- | ------------- |
| id               | uuid pk       |
| shopping_list_id | uuid fk       |
| name             | varchar(255)  |
| quantity         | numeric(12,3) |
| unit             | varchar(50)   |
| purchased        | boolean       |
| purchased_at     | timestamptz   |

---

## PETS

### pets

| campo                         | tipo         |
| ----------------------------- | ------------ |
| id                            | uuid pk      |
| residence_id                  | uuid fk      |
| primary_caregiver_resident_id | uuid fk null |
| name                          | varchar(100) |
| species                       | varchar(50)  |
| breed                         | varchar(100) |
| birth_date                    | date         |

---

## SAÚDE

### health_records

| campo          | tipo               |
| -------------- | ------------------ |
| id             | uuid pk            |
| resident_id    | uuid fk null       |
| pet_id         | uuid fk null       |
| category_id    | uuid fk            |
| record_type    | health_record_type |
| visibility     | visibility_type    |
| consent_shared | boolean            |
| title          | varchar(255)       |
| description    | text               |
| record_date    | date               |

Constraint:

```sql
CHECK (
  (resident_id IS NOT NULL AND pet_id IS NULL)
  OR
  (resident_id IS NULL AND pet_id IS NOT NULL)
)
```

---

## DESEJOS

### wish_lists

| campo             | tipo         |
| ----------------- | ------------ |
| id                | uuid pk      |
| residence_id      | uuid fk      |
| owner_resident_id | uuid fk      |
| title             | varchar(255) |

---

### wish_list_items

| campo                   | tipo         |
| ----------------------- | ------------ |
| id                      | uuid pk      |
| wish_list_id            | uuid fk      |
| category_id             | uuid fk      |
| title                   | varchar(255) |
| description             | text         |
| priority                | integer      |
| reserved_by_resident_id | uuid fk null |

---

## ANEXOS

### attachments

| campo            | tipo         |
| ---------------- | ------------ |
| id               | uuid pk      |
| storage_provider | varchar(50)  |
| storage_bucket   | varchar(255) |
| storage_key      | text         |
| file_name        | varchar(255) |
| mime_type        | varchar(255) |
| file_size        | bigint       |
| checksum         | varchar(255) |

---

### tabelas de ligação

* task_attachments
* event_attachments
* message_attachments
* debit_attachments
* health_record_attachments
* pet_attachments
* wish_list_item_attachments

Estrutura padrão:

| campo         | tipo    |
| ------------- | ------- |
| attachment_id | uuid fk |
| entity_id     | uuid fk |

PK composta:

```text
(entity_id, attachment_id)
```

---

## NOTIFICAÇÕES

### notifications

| campo              | tipo                 |
| ------------------ | -------------------- |
| id                 | uuid pk              |
| user_id            | uuid fk              |
| source_entity_type | varchar(100)         |
| source_entity_id   | uuid                 |
| type               | varchar(100)         |
| title              | varchar(255)         |
| body               | text                 |
| status             | notification_status  |

---

### notification_deliveries

| campo           | tipo        |
| --------------- | ----------- |
| id              | uuid pk     |
| notification_id | uuid fk     |
| user_id         | uuid fk     |
| channel         | enum        |
| sent_at         | timestamptz |
| delivered_at    | timestamptz |
| read_at         | timestamptz |
| failed_at       | timestamptz |

---


---

## AUDITORIA

### audit_logs

| campo        | tipo                 |
| ------------ | -------------------- |
| id           | uuid pk              |
| request_id   | uuid                 |
| user_id      | uuid fk              |
| residence_id | uuid fk null         |
| entity_name  | varchar(100)         |
| entity_id    | uuid                 |
| operation    | audit_operation_enum |
| old_data     | jsonb                |
| new_data     | jsonb                |
| ip_address   | inet                 |
| user_agent   | text                 |
| created_at   | timestamptz          |

---

## Enum

### audit_operation_enum

```text
INSERT
UPDATE
DELETE
RESTORE
```

---

### resident_role

```text
MASTER
RESIDENT
```

---

### notification_status

```text
PENDING
SENT
READ
FAILED
```

---

### health_record_type

```text
ALLERGY
MEDICATION
CONSULTATION
EXAM
NOTE
```

---

### visibility_type

```text
PRIVATE
RESIDENCE
```

---

## Índices

```sql
(entity_name, entity_id)
```

```sql
(user_id, created_at)
```

```sql
(residence_id, created_at)
```

---

## Normalização

* 1FN: atributos atômicos.
* 2FN: sem dependências parciais.
* 3FN: sem dependências transitivas.
* Categorias isoladas.
* Recorrência isolada.
* Configurações isoladas.
* Preferências isoladas.
* Anexos isolados.
* Notificações isoladas.
