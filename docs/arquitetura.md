# Arquitetura

## Diagrama de Arquitetura

```mermaid
graph TB
    Internet[Internet / Cloudflare]
    Internet --> Traefik

    subgraph "Docker Swarm Stack"
        subgraph "traefik_public (external)"
            Traefik[Traefik v3<br/>TLS Termination<br/>Let's Encrypt DNS-01]
        end

        subgraph "gaw_finance_internal (internal: true)"
            App[Django App<br/>Gunicorn x2 replicas]
            DB[(PostgreSQL 16)]
            Redis[(Redis 7)]
            RabbitMQ[(RabbitMQ 4)]
            CeleryWorker[Celery Worker]
            CeleryBeat[Celery Beat]
        end

        subgraph "gaw_finance_egress (overlay)"
            CeleryWorker2[Celery Worker<br/>acesso a APIs externas]
            CeleryBeat2[Celery Beat<br/>acesso a APIs externas]
        end

        Traefik -->|HTTP interno| App
        App --> DB
        App --> Redis
        App --> RabbitMQ
        CeleryWorker --> DB
        CeleryWorker --> Redis
        CeleryWorker --> RabbitMQ
        CeleryBeat --> DB
        CeleryBeat --> Redis
        CeleryBeat --> RabbitMQ
    end
```

## Topologia de Redes

O stack usa tres redes overlay com isolamento granular:

| Rede | Tipo | Servicos | Proposito |
|---|---|---|---|
| `traefik_public` | external | traefik, app | Trafego HTTP externo |
| `gaw_finance_internal` | internal: true | app, db, redis, rabbitmq, celery_worker, celery_beat | Comunicacao entre servicos backend, sem acesso a internet |
| `gaw_finance_egress` | overlay (sem internal) | celery_worker, celery_beat | Acesso a internet para APIs externas, sem exposicao HTTP |

## Fluxo de Uma Requisicao

```mermaid
sequenceDiagram
    participant U as Usuario
    participant CF as Cloudflare
    participant T as Traefik
    participant A as Django App
    participant DB as PostgreSQL
    participant R as Redis

    U->>CF: HTTPS Request
    CF->>T: HTTP com X-Forwarded-Proto: https
    T->>A: HTTP interno (load balance)
    A->>DB: Query
    A->>R: Cache lookup
    A->>T: Response
    T->>CF: HTTP Response
    CF->>U: HTTPS Response
```

## Celery Task Flow

```mermaid
sequenceDiagram
    participant A as Django App
    participant R as RabbitMQ
    participant W as Celery Worker
    participant RD as Redis
    participant DB as PostgreSQL

    A->>R: Envia task
    R->>W: Entrega task
    W->>DB: Processa (le/escrita)
    W->>RD: Salva resultado
    A->>RD: Consulta resultado
```

## Volumes e Persistencia

| Volume | Conteudo |
|---|---|
| `postgres_data` | Dados do PostgreSQL |
| `redis_data` | Persistencia do Redis |
| `rabbitmq_data` | Filas e mensagens do RabbitMQ |
| `media_data` | Arquivos de media do Django |
| `static_data` | Arquivos estaticos coletados |
| `letsencrypt_data` | Certificados TLS do Let's Encrypt |

## Docker Secrets

| Secret | Uso |
|---|---|
| `gaw_secret_key` | Django SECRET_KEY |
| `gaw_db_password` | Senha do PostgreSQL |
| `CLOUDFLARE_DNS_API_TOKEN` | Token da API do Cloudflare para DNS-01 challenge |
