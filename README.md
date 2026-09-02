# GAW Finance

GAW Finance e um sistema de gestao financeira pessoal desenvolvido com Django. A aplicacao ajuda a organizar bancos, categorias, entradas, saidas, pagamentos, assinaturas recorrentes e investimentos, com dashboard para acompanhamento do saldo e do fluxo financeiro.

## Funcionalidades

- Home autenticada com saldo total, entradas do mes, saidas do mes, saldo mensal, total de assinaturas, total investido e ultimas transacoes.
- Dashboard com indicadores financeiros, fluxo de caixa mensal e grafico de despesas por categoria.
- Cadastro e gerenciamento de contas de usuario.
- Cadastro de bancos com tipo de conta, agencia, conta e saldo.
- Cadastro de categorias para organizar despesas.
- Registro de entradas de dinheiro vinculadas a bancos.
- Registro de saidas de dinheiro vinculadas a bancos e categorias.
- Controle de cartao de credito, incluindo cadastro de cartoes, limite, compras parceladas e status de pago/nao pago.
- Controle de assinaturas recorrentes, com banco, categoria, dia de cobranca, cancelamento e geracao de cobrancas.
- Controle de investimentos, ativos, tipos de investimento, liquidez, valor atual, aportes e resgates.
- API REST com autenticacao JWT para bancos, categorias, entradas, saidas, pagamentos, assinaturas e investimentos.

## Tecnologias utilizadas

- Python 3.13
- Django 6.0.1
- Django REST Framework
- Simple JWT
- django-environ
- Bootstrap
- SQLite em desenvolvimento
- PostgreSQL em producao
- Gunicorn
- WhiteNoise
- Docker e Docker Compose (dev)
- Docker Swarm + Traefik (producao)

## Estrutura do projeto

- `app`: configuracoes globais, rotas principais, views da home/dashboard e metricas financeiras.
- `accounts`: contas de usuario da aplicacao.
- `authentication`: endpoints JWT.
- `banks`: bancos e contas bancarias.
- `categories`: categorias financeiras.
- `inflows`: entradas financeiras.
- `outflows`: saidas financeiras.
- `payment`: cartoes de credito e compras parceladas.
- `signatures`: assinaturas recorrentes.
- `investments`: ativos de investimento e movimentacoes.
- `traefik/`: configuracao do Traefik (static config).
- `scripts/`: scripts de deploy e backup.

## Configuracao local

Crie e ative um ambiente virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto (use `.env.example` como template):

```env
DJANGO_ENV=dev
SECRET_KEY=sua-chave-local
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

Execute as migracoes:

```powershell
python manage.py migrate
```

Crie um usuario administrador:

```powershell
python manage.py createsuperuser
```

Inicie o servidor local:

```powershell
python manage.py runserver
```

Acesse:

- Aplicacao: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- Healthcheck: `http://127.0.0.1:8000/health/`

## Docker (desenvolvimento local)

```bash
docker compose up -d --build
```

A aplicacao estara disponivel em `http://localhost:8000/`.

## Deploy em producao (Docker Swarm + Traefik)

### Pre-requisitos na VPS

1. **Docker Swarm ativo:**
   ```bash
   docker swarm init
   ```

2. **Rede overlay publica do Traefik:**
   ```bash
   docker network create --driver overlay traefik_public
   ```

3. **Docker Secrets:**
   ```bash
    echo -n 'sua-secret-key' | docker secret create gaw_secret_key -
    echo -n 'senha-postgres' | docker secret create gaw_db_password -
    echo -n 'senha-rabbitmq' | docker secret create gaw_rabbitmq_password -
    echo -n 'token-cloudflare' | docker secret create CLOUDFLARE_DNS_API_TOKEN -
   ```

4. **Arquivo `.env.prod`** na raiz do projeto com dominio, email ACME, credenciais do GHCR, etc. (ver `.env.example`).

### Deploy

```bash
bash scripts/deploy.sh
```

Redeploy sem rebuild (apenas configuracao):

```bash
bash scripts/deploy.sh --skip-build
```

### Backup

```bash
bash scripts/backup.sh
```

Os backups sao salvos em `backups/` com rotacao automatica (7 dias por padrao).

## CI/CD

O workflow do GitHub Actions (`.github/workflows/deploy.yml`) faz:

1. **Lint & Test** — flake8 + testes em todo PR/push para `main`.
2. **Build & Push** — constroi a imagem Docker e publica no GHCR (`ghcr.io/guilhermeandrade07/gaw-finance:latest`).
3. **Deploy** — SSH para a VPS e executa `scripts/deploy.sh --skip-build`.

### Secrets necessarias no GitHub

- `SSH_HOST` — IP da VPS.
- `SSH_USER` — usuario SSH.
- `SSH_PRIVATE_KEY` — chave privada SSH.
