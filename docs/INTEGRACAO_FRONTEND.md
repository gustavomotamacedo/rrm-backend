# Guia de Integração do Frontend - Fase 1

Este guia fornece especificações técnicas, exemplos de payloads (Request/Response) e instruções de consumo das rotas do backend para desenvolvedores frontend do projeto **rrm-backend**.

---

## 🔑 1. Padrões de Comunicação

### Cabeçalhos Padrão (Headers)
Para todas as requisições autenticadas (exceto webhooks externos):
```http
Authorization: Bearer <SUPABASE_JWT_TOKEN>
Content-Type: application/json
```

### Formato de Erro Padronizado
Quando a requisição falha (HTTP Status `4xx` ou `5xx`), o backend retorna:
```json
{
  "detail": "Mensagem explicativa sobre o erro ocorrido."
}
```

---

## 👤 2. Autenticação e Perfis

### Obter Perfil do Usuário Autenticado
Retorna os metadados do usuário logado (gerados automaticamente a partir do token JWT).
* **Rota**: `GET /api/v1/auth/me`
* **Response (`200 OK`)**:
```json
{
  "id": "u438c823-149d-4340-a1cf-d07f2df1209b",
  "email": "morador@exemplo.com",
  "is_active": true,
  "created_at": "2026-06-21T18:00:00Z"
}
```

### Obter Perfil Adicional
* **Rota**: `GET /api/v1/profile`
* **Response (`200 OK`)**:
```json
{
  "user_id": "u438c823-149d-4340-a1cf-d07f2df1209b",
  "display_name": "Gustavo Macedo",
  "nickname": "Guto",
  "phone": "+5511999998888",
  "avatar_url": "https://supabase-storage-url/avatars/u438c823.png"
}
```

### Atualizar Perfil
* **Rota**: `PATCH /api/v1/profile`
* **Request Payload**:
```json
{
  "display_name": "Gustavo Macedo Alterado",
  "nickname": "Guga",
  "phone": "+5511988887777"
}
```
* **Response (`200 OK`)**:
```json
{
  "user_id": "u438c823-149d-4340-a1cf-d07f2df1209b",
  "display_name": "Gustavo Macedo Alterado",
  "nickname": "Guga",
  "phone": "+5511988887777",
  "avatar_url": "https://supabase-storage-url/avatars/u438c823.png"
}
```

### Atualizar Preferências
* **Rota**: `PATCH /api/v1/preferences`
* **Request Payload**:
```json
{
  "language": "en",
  "theme": "dark"
}
```
* **Response (`200 OK`)**:
```json
{
  "user_id": "u438c823-149d-4340-a1cf-d07f2df1209b",
  "language": "en",
  "theme": "dark",
  "notification_settings": {}
}
```

---

## 🏠 3. Residências e Moradores

### Criar uma Residência
* **Rota**: `POST /api/v1/residences`
* **Request Payload**:
```json
{
  "name": "Apartamento Pinheiros",
  "description": "República dos devs em SP"
}
```
* **Response (`201 Created`)**:
```json
{
  "id": "r774da38-202a-438e-a89c-a11122233344",
  "name": "Apartamento Pinheiros",
  "description": "República dos devs em SP",
  "invite_code": "PINH-9843",
  "created_at": "2026-06-21T18:05:00Z"
}
```
> [!NOTE]
> O usuário que cria a residência é registrado automaticamente como membro `MASTER` da mesma.

### Atualizar Configurações Internas da Residência
Apenas usuários com papel `MASTER` ou `ADMIN` na residência podem chamar este endpoint.
* **Rota**: `PATCH /api/v1/residences/{residence_id}/settings`
* **Request Payload**:
```json
{
  "max_residents": 6,
  "financial_split_type": "INCOME_PROPORTIONAL",
  "allow_guest_retention": true
}
```
* **Response (`200 OK`)**:
```json
{
  "residence_id": "r774da38-202a-438e-a89c-a11122233344",
  "max_residents": 6,
  "financial_split_type": "INCOME_PROPORTIONAL",
  "allow_guest_retention": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00"
}
```

### Convidar/Adicionar Residente
* **Rota**: `POST /api/v1/residences/{residence_id}/residents`
* **Request Payload**:
```json
{
  "user_id": "u999c999-999d-9999-99cf-d07f2df1209b",
  "role": "MEMBER",
  "income_weight": 0.5
}
```
* **Response (`201 Created`)**:
```json
{
  "id": "res_888d888-8888-8888-8888-999999999999",
  "residence_id": "r774da38-202a-438e-a89c-a11122233344",
  "user_id": "u999c999-999d-9999-99cf-d07f2df1209b",
  "role": "MEMBER",
  "income_weight": 0.5,
  "joined_at": "2026-06-21T18:10:00Z"
}
```

---

## 🧹 4. Tarefas e Execuções

### Criar uma Tarefa com Recorrência
* **Rota**: `POST /api/v1/residences/{residence_id}/tasks`
* **Request Payload**:
```json
{
  "title": "Limpar a Cozinha",
  "description": "Lavar pratos, fogão e retirar lixo",
  "assigned_resident_id": "res_888d888-8888-8888-8888-999999999999",
  "due_at": "2026-06-23T12:00:00Z",
  "recurrence": {
    "frequency": "WEEKLY",
    "interval": 1,
    "by_day": "2,4,6"
  }
}
```
* **Response (`201 Created`)**:
```json
{
  "id": "t111a111-2222-3333-4444-555555555555",
  "residence_id": "r774da38-202a-438e-a89c-a11122233344",
  "title": "Limpar a Cozinha",
  "description": "Lavar pratos, fogão e retirar lixo",
  "status": "PENDING",
  "assigned_resident_id": "res_888d888-8888-8888-8888-999999999999",
  "due_at": "2026-06-23T12:00:00Z",
  "created_at": "2026-06-21T18:15:00Z",
  "recurrence": {
    "frequency": "WEEKLY",
    "interval": 1,
    "by_day": "2,4,6"
  }
}
```

### Registrar a Execução da Tarefa
* **Rota**: `POST /api/v1/tasks/{task_id}/executions`
* **Request Payload**:
```json
{
  "notes": "Lavei tudo e limpei os armários de cima também."
}
```
* **Response (`201 Created`)**:
```json
{
  "id": "e999f999-8888-7777-6666-555555555555",
  "task_id": "t111a111-2222-3333-4444-555555555555",
  "resident_id": "res_888d888-8888-8888-8888-999999999999",
  "executed_at": "2026-06-21T18:20:00Z",
  "notes": "Lavei tudo e limpei os armários de cima também."
}
```

---

## 📅 5. Eventos e Mural

### Criar Evento no Calendário
* **Rota**: `POST /api/v1/residences/{residence_id}/events`
* **Request Payload**:
```json
{
  "title": "Churrasco de Integração",
  "description": "Comemoração de início de co-living",
  "start_at": "2026-06-27T14:00:00Z",
  "end_at": "2026-06-27T22:00:00Z",
  "generate_task": false
}
```
* **Response (`201 Created`)**:
```json
{
  "id": "evt_222b222-3333-4444-5555-666666666666",
  "residence_id": "r774da38-202a-438e-a89c-a11122233344",
  "title": "Churrasco de Integração",
  "description": "Comemoração de início de co-living",
  "start_at": "2026-06-27T14:00:00Z",
  "end_at": "2026-06-27T22:00:00Z",
  "created_by": "res_888d888-8888-8888-8888-999999999999"
}
```

### Criar Mensagem no Mural
* **Rota**: `POST /api/v1/residences/{residence_id}/messages`
* **Request Payload**:
```json
{
  "title": "Aviso: Manutenção do Elevador",
  "body": "O elevador de serviço ficará parado na terça das 13h às 17h.",
  "pinned": true
}
```
* **Response (`201 Created`)**:
```json
{
  "id": "msg_333c333-4444-5555-6666-777777777777",
  "residence_id": "r774da38-202a-438e-a89c-a11122233344",
  "title": "Aviso: Manutenção do Elevador",
  "body": "O elevador de serviço ficará parado na terça das 13h às 17h.",
  "pinned": true,
  "author_id": "res_888d888-8888-8888-8888-999999999999",
  "created_at": "2026-06-21T18:30:00Z"
}
```

### Rastrear Leitura do Recado
Chame este endpoint para registrar que um morador leu/visualizou um aviso importante.
* **Rota**: `POST /api/v1/messages/{message_id}/read`
* **Response (`200 OK`)**:
```json
{
  "message_id": "msg_333c333-4444-5555-6666-777777777777",
  "resident_id": "res_888d888-8888-8888-8888-999999999999",
  "read_at": "2026-06-21T18:35:00Z"
}
```

---

## 📥 6. Upload de Anexos (Tarefas e Mural)

Os uploads utilizam codificação `multipart/form-data`. O frontend deve enviar um objeto de formulário em JS/TS contendo o arquivo físico.

* **Rotas**: 
  * Tarefa: `POST /api/v1/tasks/{task_id}/attachments`
  * Recado: `POST /api/v1/messages/{message_id}/attachments`
* **Form-data Field**: `file` (Contém o arquivo de upload)

### Exemplo de implementação em Javascript
```javascript
const uploadAttachment = async (taskId, fileObject, jwtToken) => {
  const formData = new FormData();
  formData.append('file', fileObject);

  const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}/attachments`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`
      // Nota: NÃO adicione Content-Type no header ao enviar FormData,
      // o próprio navegador adiciona a boundary necessária.
    },
    body: formData
  });
  
  if (!response.ok) {
    throw new Error('Falha ao subir arquivo');
  }
  
  const data = await response.json();
  return data;
};
```
* **Response (`201 Created`)**:
```json
{
  "id": "att_444d444-5555-6666-7777-888888888888",
  "name": "comprovante_reparacao.jpg",
  "file_path": "tasks/t111a111.../comprovante_reparacao.jpg",
  "mime_type": "image/jpeg",
  "size": 245102,
  "uploaded_at": "2026-06-21T18:40:00Z",
  "url": "https://supabase-storage-signed-temporary-url-here..."
}
```

---

## 📊 7. Dashboard e Notificações

### Obter Dashboard Geral
* **Rota**: `GET /api/v1/dashboard`
* **Response (`200 OK`)**:
```json
{
  "today_tasks": [
    {
      "id": "t111a111-2222-3333-4444-555555555555",
      "title": "Limpar a Cozinha",
      "due_at": "2026-06-23T12:00:00Z",
      "status": "PENDING"
    }
  ],
  "recent_messages": [
    {
      "id": "msg_333c333-4444-5555-6666-777777777777",
      "title": "Aviso: Manutenção do Elevador",
      "created_at": "2026-06-21T18:30:00Z"
    }
  ],
  "unread_notifications_count": 1
}
```

### Notificações do Usuário
* **Listar**: `GET /api/v1/notifications`
* **Response (`200 OK`)**:
```json
[
  {
    "id": "not_555e555-6666-7777-8888-999999999999",
    "title": "Nova Tarefa Designada",
    "body": "Você foi designado para a tarefa: Limpar a Cozinha",
    "type": "TASK_ASSIGNED",
    "is_read": false,
    "created_at": "2026-06-21T18:15:00Z"
  }
]
```

### Marcar Notificações como Lidas
* **Individual**: `POST /api/v1/notifications/{id}/read`
* **Em Massa**: `POST /api/v1/notifications/read-all`
* **Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Notifications marked as read"
}
```
