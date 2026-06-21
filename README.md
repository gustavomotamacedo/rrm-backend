# RRM Backend 🚀

O **RRM Backend** é uma API RESTful de alta performance projetada para centralizar o gerenciamento e governança de residências compartilhadas (tarefas, eventos, comunicação, finanças, estoque e integrações inteligentes).

Construído sobre uma arquitetura assíncrona moderna em Python, o projeto segue práticas estritas de tipagem estática e desenvolvimento guiado por especificações.

---

## 🛠️ Stack Tecnológica

- **Linguagem**: [Python 3.10+](https://www.python.org/)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (assíncrono, documentação interativa automática com OpenAPI/Swagger)
- **Banco de Dados**: [Supabase](https://supabase.com/) / [PostgreSQL](https://www.postgresql.org/)
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (driver assíncrono `asyncpg`)
- **Versionamento de Banco**: [Alembic](https://alembic.sqlalchemy.org/)
- **Autenticação & RLS**: Supabase Auth & Row Level Security (RLS)
- **Qualidade & Estilo**: [Ruff](https://github.com/astral-sh/ruff) (linter e formatter) e [Mypy](https://mypy-lang.org/) (verificação de tipos estrita)

---

## 📁 Estrutura do Repositório

O projeto segue uma arquitetura modular dividida em camadas de responsabilidade clara:

```text
/app
  ├── api/              # Endpoints HTTP do FastAPI (divididos por recursos/versões)
  ├── core/             # Configurações globais, segurança e variáveis de ambiente
  ├── db/               # Conexão com banco, sessões assíncronas e dependências
  ├── models/           # Modelos ORM do SQLAlchemy (conforme MODELO_FISICO.md)
  ├── schemas/          # Schemas Pydantic para validação e serialização de dados
  ├── services/         # Regras de negócio e lógica de aplicação principal
  └── main.py           # Ponto de entrada da aplicação FastAPI
/tests                  # Testes automatizados
  ├── unit/             # Testes unitários (mockando dependências externas)
  └── integration/      # Testes de integração (fluxos completos de banco/API)
/migrations             # Scripts de migração de banco de dados do Alembic
/scripts                # Scripts auxiliares (seeds de banco, automações)
/docs                   # Documentação arquitetural e de modelagem física
/.specs                 # Especificações de features (Feature Spec first)
```

---

## 🤖 Uso de Inteligência Artificial (Agente Guiado)

Este repositório foi estruturado para ser altamente compatível com o desenvolvimento assistido por agentes de IA:

- **[CLAUDE.md](file:///c:/Users/motam/Github/rrm-backend/CLAUDE.md)**: Guia de desenvolvimento consolidado que atua como a "fonte da verdade" sobre a arquitetura do projeto, comandos úteis, regras de segurança e checklist pré-commit para agentes.
- **Desenvolvimento Orientado a Especificações**: Novas features sempre começam com a escrita de uma especificação no diretório `/.specs/` antes da escrita de qualquer linha de código produtivo.

---

## 🚀 Como Rodar Localmente

### 1. Pré-requisitos
- Python 3.10 ou superior.
- Banco de dados PostgreSQL rodando localmente ou conexão ativa com o Supabase.

### 2. Clonar e Acessar o Projeto
```bash
git clone <url-do-repositorio>
cd rrm-backend
```

### 3. Configurar o Ambiente Virtual
```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual (Windows)
.venv\Scripts\activate

# Ativar ambiente virtual (Linux/macOS)
source .venv/bin/activate
```

### 4. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 5. Variáveis de Ambiente
Copie o template `.env.example` para `.env` e ajuste com suas credenciais:
```bash
cp .env.example .env
```
Preencha a variável `DATABASE_URL` (com protocolo `postgresql+asyncpg://`) e as credenciais do Supabase.

### 6. Executar Migrações do Banco
```bash
alembic upgrade head
```

### 7. Iniciar o Servidor de Desenvolvimento
```bash
python -m uvicorn app.main:app --reload
```
Acesse a aplicação em [http://127.0.0.1:8000](http://127.0.0.1:8000) e a documentação interativa da API em [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 🧪 Rodando Testes e Qualidade

Antes de submeter alterações, execute a validação local do código:

```bash
# Executar a suíte de testes (pytest)
pytest

# Executar o linter e o formatador de código (Ruff)
ruff check .
ruff format .

# Validar anotações de tipo estritas (Mypy)
mypy --strict .
```

---

## 🤝 Como Contribuir

1. **Desenvolvimento Spec-First**: Para qualquer alteração arquitetural ou nova feature, crie/edite o arquivo na pasta `.specs/` usando o template definido em `.specs/README.md` e obtenha alinhamento técnico.
2. **Padrão de Código**:
   - Utilize tipagem estática completa do Python (compatível com `mypy --strict`).
   - Use docstrings no padrão **Google Style Docstrings** para classes e métodos públicos.
   - Siga a convenção de commits [Conventional Commits](https://www.conventionalcommits.org/).