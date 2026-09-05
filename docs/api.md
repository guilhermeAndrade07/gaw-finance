# API REST

## Autenticacao

A API usa JWT (SimpleJWT).

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/api/v1/authentication/token/` | POST | Obtem access + refresh token |
| `/api/v1/authentication/token/refresh/` | POST | Renova access token |
| `/api/v1/authentication/token/verify/` | POST | Verifica token |

### Exemplo

```bash
curl -X POST http://localhost:8000/api/v1/authentication/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo12345"}'
```

## Endpoints

Todos os endpoints exigem autenticacao JWT (`Authorization: Bearer <token>`).

### Banks

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/api/v1/banks/` | GET | Lista bancos do usuario |
| `/api/v1/banks/` | POST | Cria banco |
| `/api/v1/banks/<id>/` | GET | Detalhe do banco |
| `/api/v1/banks/<id>/` | PUT/PATCH | Atualiza banco |
| `/api/v1/banks/<id>/` | DELETE | Remove banco |

### Categories

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/api/v1/categories/` | GET, POST | Lista / Cria |
| `/api/v1/categories/<id>/` | GET, PUT, PATCH, DELETE | CRUD |

### Inflows

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/api/v1/inflows/` | GET, POST | Lista / Cria |
| `/api/v1/inflows/<id>/` | GET | Detalhe |

### Outflows

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/api/v1/outflows/` | GET, POST | Lista / Cria |
| `/api/v1/outflows/<id>/` | GET | Detalhe |

### Transfers

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/api/v1/transfers/` | GET, POST | Lista / Cria transferencia interna |
| `/api/v1/transfers/<id>/` | GET | Detalhe da transferencia |

### Payments

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/api/v1/payment/` | GET, POST | Lista / Cria |
| `/api/v1/payment/<id>/` | GET, PUT, PATCH, DELETE | CRUD |

### Signatures

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/api/v1/signatures/` | GET, POST | Lista / Cria |
| `/api/v1/signatures/<id>/` | GET, PUT, PATCH, DELETE | CRUD |

### Investments

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/api/v1/investments/` | GET, POST | Lista / Cria ativo |
| `/api/v1/investments/<id>/` | GET, PUT, PATCH, DELETE | CRUD ativo |
| `/api/v1/investment-movements/` | GET | Lista movimentacoes |
| `/api/v1/investment-movements/<id>/` | GET | Detalhe movimentacao |

## Filtros por Usuario

Todos os endpoints filtram automaticamente pelo usuario autenticado. Nao e possivel acessar dados de outros usuarios.
