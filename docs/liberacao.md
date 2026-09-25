# Liberacao e gate final

Este documento define o gate obrigatorio antes de publicar uma nova versao do GAW Finance.

## 1. Gate automatizado

Rode:

```bash
bash scripts/release_gate.sh
```

O gate executa:

- analise de vulnerabilidades em dependencias Python;
- `flake8`;
- `python manage.py check`;
- `python manage.py check --deploy`;
- verificacao de migrations pendentes;
- sintaxe dos scripts de operacao;
- suíte completa de testes.

O job de CI `lint-and-test` executa o mesmo gate antes do build e do deploy.

## 2. Requisitos antes do deploy

Confirme que:

- o gate passou no commit a ser publicado;
- a imagem sera publicada por commit SHA, nunca por `latest`;
- `SECRET_KEY`, senha do banco, senha do RabbitMQ e token do Cloudflare estao como Docker secrets;
- `DJANGO_ENV=prd`;
- `DEBUG=False`;
- `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` nao usam wildcard;
- `DOMAIN` e `ACME_EMAIL` estao corretos;
- `SSH_HOST`, `SSH_USER` e `SSH_PRIVATE_KEY` estao configurados no CI;
- o servidor tem acesso ao GHCR.

## 3. Deploy

O pipeline publica a imagem com o SHA do commit e executa o deploy automaticamente.

O job de deploy:

1. sincroniza os arquivos de deploy para a VPS;
2. exporta `GAW_IMAGE_TAG`;
3. cria backup do banco e media;
4. roda migrations e `collectstatic` em job isolado;
5. publica a stack;
6. agrega app, Celery worker e Celery beat;
7. testa `/ready/` e `/login/`;
8. faz rollback do app se o smoke test falhar.

## 4. Smoke test manual

Depois do deploy:

```bash
curl -fsS https://gawfinance.gawsystems.com.br/ready/
curl -fsSI https://gawfinance.gawsystems.com.br/login/
```

Verifique tambem:

- login por email;
- MFA;
- dashboard;
- criacao de uma saida de teste;
- consulta no banco se necessario.

## 5. Restore

Para validar o ultimo backup:

```bash
bash scripts/restore.sh backups/<timestamp>
```

Para restaurar em database temporaria:

```bash
bash scripts/restore.sh backups/<timestamp> --apply
```

O script nao substitui producao automaticamente. Apos validar a database temporaria, promova os dados manualmente.

## 6. Rollback

Em caso de falha:

1. verifique `docker service ps gaw_finance_app`;
2. verifique `docker service logs gaw_finance_app`;
3. se o problema for de imagem, faca rollback do app:

```bash
docker service rollback gaw_finance_app
```

4. se o problema for de schema, trate como rollback de release separado. Nao faca rollback automatico de migrations sem plano de reversao.

## 7. Criterios de liberacao

A versao pode ser liberada apenas se:

- o gate final passou;
- o backup pre-deploy foi criado;
- migrations aplicaram sem erro;
- `/ready/` retornou `200`;
- `/login/` respondeu;
- Celery worker e beat estao saudaveis;
- nao ha vulnerabilidades conhecidas em dependencias Python;
- rollback foi testado ou o plano de rollback foi revisado.
