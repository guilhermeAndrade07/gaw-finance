# Desenvolvimento

## Ambiente Local

### Prerequisitos

- Python 3.13
- pip
- (opcional) Docker + Docker Compose

### Setup sem Docker

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crie `.env` (use `.env.example` como template):

```env
DJANGO_ENV=dev
SECRET_KEY=sua-chave-local
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

Execute:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Setup com Docker

```bash
docker compose up -d --build
```

Acesse `http://localhost:8000/`.

## Dados de Demonstracao

Para carregar dados fake para demonstracao:

```bash
python manage.py load_fake_data
```

Opcoes:

```bash
python manage.py load_fake_data --username=meuuser --password=minhasenha --email=meu@email.com --reset
```

Isso cria:

- 1 usuario demo (username: `demo`, senha: `demo12345`)
- 3 bancos com saldos iniciais
- 8 categorias (Moradia, Alimentacao, Transporte, etc.)
- Entradas (salarios + freelance) dos ultimos 9 meses
- Saidas (aluguel, supermercado, transporte, etc.) dos ultimos 9 meses
- 2 cartoes de credito com compras parceladas
- 5 assinaturas recorrentes (Netflix, Spotify, etc.)
- 6 investimentos (Renda Fixa, Variavel, Cripto, Fundos)

## Lint e Testes

```bash
# Lint
flake8 .

# Testes
python manage.py test

# System check
python manage.py check
```

## Management Commands

| Command | Funcao |
|---|---|
| `wait_for_db` | Aguarda o banco de dados com retry |
| `migrate_safe` | Migrations com advisory lock (multi-replica) |
| `load_fake_data` | Carga de dados de demonstracao |

## Celery Local (opcional)

Para testar Celery localmente, e necessario RabbitMQ e Redis rodando.

```bash
# Terminal 1 - RabbitMQ
docker run -d --name rabbitmq -p 5672:5672 rabbitmq:4-management

# Terminal 2 - Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Terminal 3 - Celery Worker
celery -A app worker --loglevel=info

# Terminal 4 - Celery Beat
celery -A app beat --loglevel=info
```

Adicione ao `.env`:

```env
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/1
REDIS_URL=redis://localhost:6379/0
```

## Painel do Celery

Acesse `http://localhost:8000/dj-celery-panel/` para visualizar tasks, workers e filas.

## Estrutura de Diretorios

```
gaw-finance/
├── app/              # Configuracoes globais, Celery, dashboard
├── accounts/         # Contas de usuario
├── authentication/   # JWT endpoints
├── banks/            # Bancos
├── categories/       # Categorias
├── inflows/          # Entradas
├── outflows/         # Saidas
├── payment/          # Cartao de credito
├── signatures/       # Assinaturas recorrentes
├── investments/      # Investimentos
├── reports/          # Relatorios PDF
├── traefik/          # Config do Traefik
├── scripts/          # deploy.sh, backup.sh
├── docs/             # Documentacao MKDocs
├── Dockerfile
├── docker-compose.yml
├── stack.yml         # Docker Swarm
├── entrypoint.sh     # App entrypoint
├── entrypoint-celery.sh  # Celery entrypoint
├── gunicorn.conf.py
├── mkdocs.yml
└── requirements.txt
```
