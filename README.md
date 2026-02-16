```markdown
# README.md

## Como Executar o Código

### Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.13+ (apenas para execução local)
- Poetry (apenas para execução local)

---

## Opção 1: Executar com Docker Compose

### Passo 1: Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=sqlite:///./livros.db
REDIS_HOST=redis
MEU_USUARIO=admin
MINHA_SENHA=senha123
```

### Passo 2: Iniciar os containers

```bash
docker-compose up -d
```

### Passo 3: Acessar a API

A API estará disponível em: **http://localhost:8001**

Documentação interativa: **http://localhost:8001/docs**

### Comandos úteis

```bash
# Ver logs
docker-compose logs -f

# Parar os containers
docker-compose down

# Reconstruir as imagens
docker-compose up --build -d
```

---

## Opção 2: Executar Localmente

### Passo 1: Configurar Redis

Inicie o Redis usando Docker:

```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

Ou instale o Redis localmente:

**Linux/Ubuntu:**
```bash
sudo apt update
sudo apt install redis-server
redis-server
```

**Mac:**
```bash
brew install redis
redis-server
```

### Passo 2: Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=sqlite:///./livros.db
REDIS_HOST=localhost
MEU_USUARIO=admin
MINHA_SENHA=senha123
```

### Passo 3: Instalar dependências

```bash
poetry install
```

### Passo 4: Executar a aplicação

```bash
fastapi dev main.py
```

A API estará disponível em: **http://localhost:8000**

---

## Testando a Aplicação

### Usando curl

```bash
# Adicionar um livro
curl -u admin:senha123 -X POST http://localhost:8001/adiciona \
  -H "Content-Type: application/json" \
  -d '{"titulo": "1984", "autor": "George Orwell", "ano_publicacao": 1949}'

# Listar livros
curl -u admin:senha123 http://localhost:8001/livros

# Ver status do Redis
curl -u admin:senha123 http://localhost:8001/debug/redis-status

# Ver conteúdo do cache
curl -u admin:senha123 http://localhost:8001/debug/redis
```

### Usando Python

```python
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8001"
auth = HTTPBasicAuth("admin", "senha123")

# Adicionar livro
novo_livro = {"titulo": "1984", "autor": "George Orwell", "ano_publicacao": 1949}
response = requests.post(f"{BASE_URL}/adiciona", json=novo_livro, auth=auth)
print(response.json())

# Listar livros
response = requests.get(f"{BASE_URL}/livros", auth=auth)
print(response.json())
```

---

## Verificar o Redis Manualmente

```bash
# Acessar o Redis CLI
docker exec -it redis_cache redis-cli

# Comandos úteis dentro do Redis
PING              # Testar conexão
KEYS *            # Listar todas as chaves
GET livros        # Ver conteúdo da chave 'livros'
TTL livros        # Ver tempo de expiração
FLUSHDB           # Limpar todo o cache
exit              # Sair
```
```