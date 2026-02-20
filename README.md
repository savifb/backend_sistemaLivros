# Sistema Livros — FastAPI + Celery + Redis

## Visão Geral

API REST para gerenciamento de livros com:
- **Celery** para execução assíncrona de tarefas (`calcular_soma` e `calcular_fatorial`)
- **Redis** como broker do Celery, backend de resultados e cache de leituras
- **SQLite** como banco de dados
- **Kafka** para eventos de domínio
- **Autenticação HTTP Basic**

---

## Pré-requisitos

- Docker e Docker Compose instalados

---

## Como Executar

### Passo 1: Criar o arquivo `.env`

```env
DATABASE_URL=sqlite:///./livros.db
MEU_USUARIO=admin
MINHA_SENHA=admin
PYTHONUNBUFFERED=1
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
```

### Passo 2: Subir todos os containers

```bash
docker-compose up --build -d
```

Isso sobe automaticamente:
- **FastAPI** → http://localhost:8001
- **Celery Worker** → processa tarefas em background
- **Redis** → broker + backend + cache
- **Kafka + Zookeeper + Kafka UI** → http://localhost:8080

### Passo 3: Verificar se tudo está rodando

```bash
docker-compose ps
```

Todos os containers devem estar com status `Up`.

---

## Executar o Celery Worker manualmente (fora do Docker)

```bash
# Instalar dependências
pip install celery redis fastapi uvicorn python-dotenv sqlalchemy

# Na raiz do projeto, iniciar o worker
celery -A celery_app:app worker --loglevel=info

# Monitorar tarefas em tempo real
celery -A celery_app:app events
```

---

## Endpoints

### Tarefas Assíncronas (Celery)

| Método | Rota | Parâmetros | Descrição |
|--------|------|------------|-----------|
| POST | `/calcular/soma` | `numero1`, `numero2` (query) | Dispara tarefa `calcular_soma` |
| POST | `/calcular/fatorial` | `n` (query) | Dispara tarefa `calcular_fatorial` |
| GET | `/tarefas/recentes` | — | Lista últimas 50 tarefas com status e resultado |

### Livros (autenticação: admin/admin)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/livros` | Lista livros com paginação (usa cache Redis) |
| POST | `/adiciona` | Adiciona novo livro |
| PUT | `/atualiza/{id}` | Atualiza livro |
| DELETE | `/delete/{id}` | Remove livro |

### Debug

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/debug/redis-status` | Status da conexão Redis |
| GET | `/debug/redis` | Visualiza todo o cache |
| DELETE | `/debug/limpar-cache` | Limpa todo o cache |

---

## Testando com curl

### 1. Disparar tarefa de soma

```bash
curl -X POST "http://localhost:8001/calcular/soma?numero1=15&numero2=25"
```

Resposta imediata (não bloqueia):
```json
{
  "task_id": "3bc4e742-6d5d-4190-a513-c62719afa799",
  "message": "Tarefa de soma enviada para execução em background."
}
```

### 2. Disparar tarefa de fatorial

```bash
curl -X POST "http://localhost:8001/calcular/fatorial?n=10"
```

Resposta imediata (não bloqueia):
```json
{
  "task_id": "bcb2fa15-5ce0-4a5a-905d-7e001715e15f",
  "message": "Tarefa de fatorial enviada para execução em background."
}
```

### 3. Verificar resultados (aguardar ~5 segundos)

```bash
curl http://localhost:8001/tarefas/recentes
```

Resposta após conclusão:
```json
{
  "tarefas": [
    {
      "task_id": "bcb2fa15-5ce0-4a5a-905d-7e001715e15f",
      "status": "SUCCESS",
      "resultado": 3628800
    },
    {
      "task_id": "3bc4e742-6d5d-4190-a513-c62719afa799",
      "status": "SUCCESS",
      "resultado": 40
    }
  ]
}
```

### 4. Livros

```bash
# Adicionar livro
curl -u admin:admin -X POST http://localhost:8001/adiciona \
  -H "Content-Type: application/json" \
  -d '{"titulo": "1984", "autor": "George Orwell", "ano_publicacao": 1949}'

# Listar livros
curl -u admin:admin "http://localhost:8001/livros?page=1&limit=10"
```

---

## Fluxo das Tarefas Celery

```
Cliente HTTP
    │
    ▼
FastAPI POST /calcular/soma
    │  ← retorna task_id IMEDIATAMENTE (sem bloquear)
    ▼
Redis Broker ──── enfileira tarefa ────► Celery Worker
                                              │
                                              │ executa calcular_soma()
                                              │ time.sleep(5) — simula workload
                                              ▼
                                         Redis Backend
                                              │ armazena resultado
                                              ▼
                              GET /tarefas/recentes
                              status: SUCCESS | resultado: 40
```

---

## Implementação das Tarefas

### calcular_soma
Recebe `numero1` e `numero2`, aguarda 5 segundos (simulação de workload) e retorna a soma.

### calcular_fatorial
Recebe `n` e calcula o fatorial usando **implementação iterativa**, sem recursão:

```python
resultado = 1
for i in range(2, n + 1):
    resultado *= i
```

Vantagens desta abordagem:
- **Sem risco de RecursionError** — Python tem limite de recursão (~1000 chamadas por padrão)
- **Sem risco de overflow** — Python suporta inteiros de precisão arbitrária
- Calcula corretamente valores grandes como `1000!` ou `10000!`

---

## Verificar Redis manualmente

```bash
# Acessar Redis CLI
docker exec -it livro_redis redis-cli

# Comandos úteis
PING                          # Testar conexão
KEYS *                        # Listar todas as chaves
LRANGE tarefas_ids 0 -1       # Ver IDs das tarefas
GET livros                    # Ver cache de livros
TTL livros                    # Ver tempo de expiração
FLUSHDB                       # Limpar tudo
exit
```

---

## Monitorar logs do worker

```bash
docker-compose logs -f celery
```