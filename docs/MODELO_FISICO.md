# Modelo Físico (3FN)

## Convenções

### Chaves

* PK: UUID v7
* FK: UUID v7

### Datas

* TIMESTAMPTZ

### Auditoria

Todas as tabelas de domínio possuem:

```text
created_at
updated_at
created_by
updated_by
deleted_at
deleted_by
```

### Soft Delete

```text
deleted_at IS NULL
```

define registro ativo.

---

# USERS

```text
id PK
email UNIQUE
password_hash
last_login_at
created_at
updated_at
```

---

# PROFILES

```text
id PK
user_id FK UNIQUE

first_name
last_name
nickname
phone
avatar_url
birth_date

created_at
updated_at
deleted_at
```

---

# USER_PREFERENCES

```text
id PK
user_id FK UNIQUE

language
theme
push_enabled
quiet_hours_start
quiet_hours_end
```

---

# RESIDENCES

```text
id PK

name
timezone

created_by
created_at
updated_at
deleted_at
```

---

# RESIDENCE_SETTINGS

```text
id PK
residence_id FK UNIQUE

financial_split_method
guest_retention_days
notifications_enabled
default_currency
```

---

# RESIDENTS

```text
id PK

residence_id FK
user_id FK

role
income_weight

joined_at
left_at
```

---

# GUESTS

```text
id PK

residence_id FK
host_resident_id FK

name
arrival_date
departure_date
notes
expires_at
```

---

# RECURRENCES

```text
id PK

frequency
interval_value

by_week_day
by_month_day

start_date
end_date
```

---

# TASKS

```text
id PK

residence_id FK
assigned_resident_id FK
recurrence_id FK

title
description

status
due_at
completed_at
```

---

# TASK_EXECUTIONS

```text
id PK

task_id FK
resident_id FK

executed_at
notes
```

---

# EVENTS

```text
id PK

residence_id FK
owner_resident_id FK
recurrence_id FK

title
description

start_at
end_at

generate_task
```

---

# EVENT_GUESTS

```text
id PK

event_id FK
guest_id FK

attendance_status
```

---

# MESSAGES

```text
id PK

residence_id FK
created_by_resident_id FK

title
body

pinned
expires_at
```

---

# MESSAGE_READS

```text
id PK

message_id FK
resident_id FK

read_at
```

---

# CATEGORIES

```text
id PK

residence_id FK

domain

name
description
```

---

# DEBITS

```text
id PK

residence_id FK
payer_resident_id FK

category_id FK

visibility

amount
description

due_date
paid_at
```

---

# DEBIT_SHARES

```text
id PK

debit_id FK
resident_id FK

amount
```

---

# REIMBURSEMENTS

```text
id PK

debit_id FK

from_resident_id FK
to_resident_id FK

amount

paid_at
```

---

# ITEMS

```text
id PK

residence_id FK
category_id FK

name

quantity
minimum_quantity

unit
```

---

# ITEM_MOVEMENTS

```text
id PK

item_id FK
resident_id FK

movement_type
quantity

created_at
```

---

# SHOPPING_ITEMS

```text
id PK

residence_id FK

name
quantity

purchased
purchased_at
```

---

# PETS

```text
id PK

residence_id FK
owner_resident_id FK

name
species
breed
birth_date
```

---

# HEALTH_RECORDS

```text
id PK

resident_id FK NULL
pet_id FK NULL

category_id FK

visibility
consent_shared

title
description

record_date
```

Constraint:

```text
resident_id XOR pet_id
```

---

# WISH_LISTS

```text
id PK

residence_id FK
owner_resident_id FK

title
```

---

# WISH_LIST_ITEMS

```text
id PK

wish_list_id FK
category_id FK

title
description

priority

reserved
reserved_by_resident_id FK NULL
```

---

# ATTACHMENTS

```text
id PK

entity_type
entity_id

file_name
file_path

mime_type
file_size

uploaded_by
```

---

# NOTIFICATIONS

```text
id PK

user_id FK

type
title
body

read_at
```

---

# NOTIFICATION_DELIVERIES

```text
id PK

notification_id FK
user_id FK

channel

sent_at
delivered_at
read_at
failed_at
```

---

# Índices Obrigatórios

```sql
users(email)
```

```sql
residents(residence_id, user_id)
```

```sql
tasks(residence_id, status)
```

```sql
events(residence_id, start_at)
```

```sql
debits(residence_id, due_date)
```

```sql
items(residence_id, category_id)
```

```sql
health_records(resident_id)
```

```sql
health_records(pet_id)
```

```sql
notifications(user_id, read_at)
```

```sql
attachments(entity_type, entity_id)
```
