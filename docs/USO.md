# Guia de Uso da API - Fase 1

Este guia documenta o funcionamento, os padrões de arquitetura e a forma de interagir com os endpoints da **Fase 1: Core da Residência e Infraestrutura Inicial** do projeto **rrm-backend**.

---

## 🛠️ 1. Como Executar Localmente

### Pré-requisitos
1. Python 3.10+ instalado.
2. Banco de dados PostgreSQL configurado (local ou remoto via Supabase).
3. Arquivo `.env` configurado na raiz do projeto (use `.env.example` como base).

### Passos para inicialização
1. **Ativar o Ambiente Virtual**:
   ```powershell
   # Windows:
   .venv\Scripts\activate
   
   # Linux/macOS:
   source .venv/bin/activate
   ```
2. **Instalar Dependências**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Aplicar Migrações do Banco**:
   ```bash
   alembic upgrade head
   ```
4. **Iniciar o Servidor FastAPI**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
5. **Acessar Documentação Interativa**:
   * Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   * ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔐 2. Autenticação & Segurança

O backend utiliza o **Supabase Auth** para a gestão de usuários e sessões.

### Autenticação em Endpoints Protegidos
Para qualquer rota protegida, você deve enviar o JWT token gerado pelo Supabase no cabeçalho HTTP:
* **Header**: `Authorization`
* **Formato**: `Bearer <seu_jwt_token>`

O middleware de segurança ([security.py](file:///c:/Users/motam/Github/rrm-backend/app/core/security.py)) decodifica e valida o token diretamente com o endpoint `/auth/v1/user` do Supabase para obter o ID do usuário correspondente.

### Controle de Membros de Co-living (`RequiresResident`)
Para rotas específicas de uma residência (como tarefas, recados e moradores), existe um controle de autorização baseado no papel do morador:
* **Função**: `RequiresResident(allowed_roles=[...])`
* **Exemplo**: Apenas moradores com papel `MASTER` ou `ADMIN` podem alterar as configurações da residência ou remover membros.

---

## 🔄 3. Webhook de Sincronização do Supabase

Para manter o banco local sincronizado com a autenticação do Supabase, o endpoint `/api/v1/auth/webhooks/supabase` deve ser configurado como Webhook no Supabase (escutando a tabela `auth.users`).

* **Método**: `POST`
* **Payload Esperado**: Eventos do Supabase Auth contendo `type` (`INSERT`, `UPDATE`, `DELETE`) e `record`/`old_record`.
* **Segurança**: Se a variável `SUPABASE_WEBHOOK_SECRET` estiver configurada no `.env`, o cabeçalho `x-supabase-signature` será validado para garantir a integridade da chamada.
* **Ações Automáticas**:
  * `INSERT`: Cria automaticamente o registro correspondente em `users`, `profiles` e `user_preferences`.
  * `UPDATE`: Atualiza o e-mail e os metadados do perfil.
  * `DELETE`: Executa soft delete local do usuário para preservar logs e histórico.

---

## 📂 4. Estrutura dos Endpoints (Fase 1)

### 👤 Usuários e Perfis (`/api/v1`)
* `GET /users/me`: Retorna os dados cadastrais da conta do usuário logado.
* `DELETE /users/me`: Executa o soft delete da conta do usuário.
* `GET /profile`: Retorna o perfil público do usuário logado (nome, apelido, telefone).
* `PATCH /profile`: Atualiza dados parciais do perfil.
* `GET /preferences`: Retorna as preferências do usuário (idioma, tema).
* `PATCH /preferences`: Atualiza preferências.

### 🏠 Residências e Membros (`/api/v1/residences`)
* `GET /residences`: Lista todas as residências de que o usuário logado participa.
* `POST /residences`: Cria uma nova residência (quem cria assume o papel `MASTER` e cria-se as configurações padrão automaticamente).
* `GET /residences/{id}`: Retorna os detalhes de uma residência específica.
* `PATCH /residences/{id}`: Atualiza os dados da residência.
* `DELETE /residences/{id}`: Exclui a residência (apenas para usuários `MASTER`).
* `GET /residences/{id}/settings`: Retorna as preferências internas da residência (limites de moradores, rateio financeiro).
* `PATCH /residences/{id}/settings`: Atualiza configurações da residência (apenas `MASTER`/`ADMIN`).
* `GET /residences/{id}/residents`: Lista todos os moradores e seus papéis na residência.
* `POST /residences/{id}/residents`: Convida/Adiciona um novo morador (apenas `MASTER`/`ADMIN`).
* `PATCH /residents/{resident_id}`: Atualiza o papel (`role`) ou peso de renda de um residente.
* `DELETE /residents/{resident_id}`: Remove um residente (apenas `MASTER`/`ADMIN`).

### 🧹 Tarefas, Recorrências e Execuções (`/api/v1/residences/{residence_id}/tasks` & `/api/v1/tasks`)
* `GET /residences/{residence_id}/tasks`: Lista todas as tarefas da residência.
* `POST /residences/{residence_id}/tasks`: Cria uma nova tarefa (com suporte a configuração de `recurrence`).
* `GET /tasks/{id}`: Detalha uma tarefa específica.
* `PATCH /tasks/{id}`: Atualiza título, status, prazo ou morador designado.
* `DELETE /tasks/{id}`: Remove la tarefa.
* `GET /tasks/{id}/executions`: Lista o histórico de realizações daquela tarefa.
* `POST /tasks/{id}/executions`: Registra que uma tarefa foi realizada (com anotações opcionais).
* `POST /tasks/{id}/attachments`: Faz upload de arquivos de suporte para a tarefa no Storage.
* `DELETE /tasks/{id}/attachments/{attachment_id}`: Remove o anexo.

### 📅 Eventos e Calendário (`/api/v1/residences/{residence_id}/events` & `/api/v1/events`)
* `GET /residences/{residence_id}/events`: Lista eventos agendados na residência.
* `POST /residences/{residence_id}/events`: Cria um evento (ex: reuniões, faxinas coletivas, visitas).
* `GET /events/{id}`: Detalha um evento.
* `PATCH /events/{id}`: Modifica horários ou descrições do evento.
* `DELETE /events/{id}`: Remove o evento.

### 📌 Mural de Recados (`/api/v1/residences/{residence_id}/messages` & `/api/v1/messages`)
* `GET /residences/{residence_id}/messages`: Lista as mensagens ativas no mural (recados pinados aparecem primeiro).
* `POST /residences/{residence_id}/messages`: Publica um novo recado.
* `GET /messages/{id}`: Detalha uma mensagem.
* `PATCH /messages/{id}`: Atualiza o recado.
* `DELETE /messages/{id}`: Exclui a mensagem.
* `POST /messages/{id}/read`: Marca a mensagem como visualizada pelo usuário atual (rastreamento de visualização de avisos importantes).
* `POST /messages/{id}/attachments`: Faz upload de imagens ou arquivos anexados ao recado.
* `DELETE /messages/{id}/attachments/{attachment_id}`: Remove o anexo.

### 📊 Dashboard Consolidado e Notificações (`/api/v1`)
* `GET /dashboard`: Retorna o resumo das atividades de todas as residências do usuário para o dia de hoje (tarefas pendentes hoje, recados recentes e notificações não lidas).
* `GET /dashboard/residences/{residence_id}`: Retorna o painel detalhado de uma residência específica.
* `GET /notifications`: Lista as notificações do usuário logado.
* `POST /notifications/{id}/read`: Marca uma notificação específica como lida.
* `POST /notifications/read-all`: Marca todas as notificações do usuário como lidas de uma só vez.
* `DELETE /notifications/{id}`: Exclui a notificação.

---

## 🗃️ 5. Serviço de Storage Desacoplado

O `BaseStorageService` gerencia a interface de arquivos da aplicação de forma agnóstica.
A implementação atual de produção (`SupabaseStorageService`) utiliza o bucket de Storage do Supabase de forma assíncrona com `httpx`.

Ao fazer upload de um arquivo nos endpoints de anexo (Tarefas e Mural):
1. O arquivo é validado e enviado ao Supabase Storage.
2. Um registro é gerado na tabela `attachments`.
3. É retornada a URL assinada pública temporária para o front-end exibir o recurso (imagem/documento).

---

## 📮 6. Testando com o Postman

Use a coleção fornecida no Workspace do Postman para testar os fluxos completos. As variáveis de ambiente da coleção facilitam o encadeamento das requisições:

1. Acesse o Postman no Workspace **Person** na coleção **RRM Backend API**.
2. Defina o valor da variável de coleção `baseUrl` como `http://localhost:8000`.
3. Insira o token JWT de teste na variável `token`.
4. Ao criar uma residência, capture o ID de retorno e configure a variável `residence_id`. Isso fará com que as requisições subsequentes de moradores, tarefas e eventos funcionem automaticamente.
