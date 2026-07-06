# GAW Finance

Sistema de gestao financeira pessoal desenvolvido com Django.

## Visao Geral

O GAW Finance ajuda a organizar:

- **Bancos** - contas bancarias com saldo inicial e atual
- **Categorias** - organizacao de despesas
- **Entradas** - registro de dinheiro recebido
- **Saidas** - registro de gastos vinculados a categorias
- **Cartao de Credito** - compras parceladas e controle de limite
- **Assinaturas** - cobrancas recorrentes mensais
- **Investimentos** - ativos, aportes e resgates
- **Relatorios** - exportacao em PDF (fluxo de caixa, despesas por categoria, investimentos)

## Stack Tecnologica

| Componente | Tecnologia |
|---|---|
| Backend | Django 6.0.1, Python 3.13 |
| API | Django REST Framework + SimpleJWT |
| Banco de Dados | PostgreSQL (prod) / SQLite (dev) |
| Cache/Result Backend | Redis |
| Mensageria | RabbitMQ |
| Tasks Assincronas | Celery (worker + beat) |
| Reverse Proxy | Traefik v3 |
| Static Files | WhiteNoise |
| PDF | ReportLab + PyPDF |
| Deploy | Docker Swarm |
| CI/CD | GitHub Actions |
| Documentacao | MKDocs + Mermaid |
