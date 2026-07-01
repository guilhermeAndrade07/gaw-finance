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

- Python 3.12
- Django 6.0.1
- Django REST Framework
- Simple JWT
- Bootstrap
- SQLite em desenvolvimento
- PostgreSQL em producao
- Gunicorn
- WhiteNoise
- Docker e Docker Compose
- Nginx Proxy Manager

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

Crie um arquivo `.env` na raiz do projeto. Para desenvolvimento local, as variaveis principais sao:

```env
SECRET_KEY=sua-chave-local
DEBUG=True
DJANGO_ENV=dev
ALLOWED_HOSTS=localhost,127.0.0.1
```

Quando `DJANGO_ENV=dev`, o projeto usa SQLite em `db.sqlite3`.

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
