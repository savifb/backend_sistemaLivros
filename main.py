# SISTEMA LIVROS

# IMPORTAÇÕES FASTAPI E OUTRAS BIBLIOTECAS
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
import os
import secrets
import json
import redis
import asyncio
import time
from celery_app import app as celery_app, calcular_soma, calcular_fatorial
from celery.result import AsyncResult
from kafka_producer import enviar_evento

load_dotenv()

# IMPORTAÇÕES PARA O BANCO DE DADOS
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# CONFIGURAÇÕES DO BANCO DE DADOS
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
base = declarative_base()

# CONFIGURAÇÃO DO REDIS
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
TTL_1_HORA = 3600
TTL_5_MIN = 300

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    print(f"✅ Redis conectado em {REDIS_HOST}:{REDIS_PORT}")
    REDIS_DISPONIVEL = True
except Exception as e:
    print(f"⚠️ Redis não disponível: {e}")
    redis_client = None
    REDIS_DISPONIVEL = False


### CRIANDO TABELA DO BANCO DE DADOS - LIVROS
class LivroDB(base):
    __tablename__ = 'Livros'
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    autor = Column(String, index=True)
    ano_publicacao = Column(Integer)

base.metadata.create_all(bind=engine)


### UMA SESSAO NO BANCO DE DADOS
def sessao_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


# Inicializações do FastAPI
app = FastAPI()

MEU_USUARIO = os.getenv('MEU_USUARIO')
MINHA_SENHA = os.getenv('MINHA_SENHA')

security = HTTPBasic()


def autentica_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    username_correct = secrets.compare_digest(credentials.username, MEU_USUARIO)
    password_correct = secrets.compare_digest(credentials.password, MINHA_SENHA)
    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=401,
            detail='Usuário ou senha incorretos',
            headers={'WWW-Authenticate': 'Basic'},
        )


### Estrutura do Livro
class Livro(BaseModel):
    titulo: str
    autor: str
    ano_publicacao: int


# ==================== FUNÇÕES DE CACHE REDIS ====================

async def salvar_livro_cache(livro_id: int, livro: Livro, ttl: int = TTL_1_HORA):
    if not REDIS_DISPONIVEL:
        return
    try:
        await asyncio.to_thread(
            redis_client.setex,
            f'livro:{livro_id}',
            ttl,
            json.dumps(livro.model_dump())
        )
        print(f"✅ Livro {livro_id} salvo no cache (expira em {ttl}s)")
    except Exception as e:
        print(f"❌ Erro ao salvar livro no cache: {e}")


async def salvar_livros_redis(livros: List[dict], ttl: int = TTL_5_MIN):
    if not REDIS_DISPONIVEL:
        return False
    try:
        livros_json = json.dumps(livros)
        await asyncio.to_thread(redis_client.setex, 'livros', ttl, livros_json)
        print(f"✅ {len(livros)} livros salvos no cache (expira em {ttl}s)")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar livros no cache: {e}")
        return False


async def obter_livros_redis() -> Optional[List[dict]]:
    if not REDIS_DISPONIVEL:
        return None
    try:
        livros_json = await asyncio.to_thread(redis_client.get, 'livros')
        if livros_json:
            livros = json.loads(livros_json)
            print(f"✅ {len(livros)} livros encontrados no cache")
            return livros
        print("❌ Livros NÃO encontrados no cache")
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar livros do cache: {e}")
        return None


async def deletar_livros_redis():
    if not REDIS_DISPONIVEL:
        return False
    try:
        result = await asyncio.to_thread(redis_client.delete, 'livros')
        if result:
            print("✅ Cache de livros invalidado com sucesso")
            return True
        print("⚠️ Cache de livros não existia")
        return False
    except Exception as e:
        print(f"❌ Erro ao deletar livros do cache: {e}")
        return False


async def obter_livro_cache(livro_id: int) -> Optional[dict]:
    if not REDIS_DISPONIVEL:
        return None
    try:
        valor = await asyncio.to_thread(redis_client.get, f'livro:{livro_id}')
        if valor:
            print(f"✅ Livro {livro_id} encontrado no cache")
            return json.loads(valor)
        print(f"❌ Livro {livro_id} NÃO está no cache")
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar livro do cache: {e}")
        return None


async def deletar_livro_cache(livro_id: int):
    if not REDIS_DISPONIVEL:
        return
    try:
        await asyncio.to_thread(redis_client.delete, f'livro:{livro_id}')
        print(f"✅ Livro {livro_id} removido do cache")
    except Exception as e:
        print(f"❌ Erro ao deletar livro do cache: {e}")


# ==================== ENDPOINTS CELERY ====================

@app.post('/calcular/soma')
def endpoint_calcular_soma(numero1: int, numero2: int):
    """
    Dispara a tarefa calcular_soma em background via Celery.
    Retorna imediatamente com o task_id, sem bloquear a API.
    """
    tarefa = calcular_soma.delay(numero1, numero2)
    redis_client.lpush("tarefas_ids", tarefa.id)
    redis_client.ltrim("tarefas_ids", 0, 49)
    return {
        "task_id": tarefa.id,
        "message": "Tarefa de soma enviada para execução em background."
    }


@app.post('/calcular/fatorial')
def endpoint_calcular_fatorial(n: int):
    """
    Dispara a tarefa calcular_fatorial em background via Celery.
    Retorna imediatamente com o task_id, sem bloquear a API.
    """
    tarefa = calcular_fatorial.delay(n)
    redis_client.lpush("tarefas_ids", tarefa.id)
    redis_client.ltrim("tarefas_ids", 0, 49)
    return {
        "task_id": tarefa.id,
        "message": "Tarefa de fatorial enviada para execução em background."
    }


@app.get('/tarefas/recentes')
def listar_tarefas():
    """Lista as últimas 50 tarefas com status e resultado."""
    ids = redis_client.lrange('tarefas_ids', 0, -1)
    tarefas = []
    for task_id in ids:
        resultado = AsyncResult(task_id, app=celery_app)
        tarefas.append({
            "task_id": task_id,
            "status": resultado.status,
            "resultado": resultado.result if resultado.successful() else None
        })
    return {"tarefas": tarefas}


# ==================== ENDPOINTS LIVROS ====================

@app.get('/livros')
async def get_livros(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    if page < 1 or limit < 1:
        raise HTTPException(
            status_code=400,
            detail='A página e o limite devem ser maiores que zero.'
        )

    inicio = time.time()
    livros_cache = await obter_livros_redis()

    if livros_cache:
        offset = (page - 1) * limit
        livros_pagina = livros_cache[offset:offset + limit]
        return {
            "source": "cache",
            "tempo_resposta_ms": round((time.time() - inicio) * 1000, 2),
            "page": page,
            "limit": limit,
            "total_livros": len(livros_cache),
            "livros": livros_pagina
        }

    todos_livros = db.query(LivroDB).all()
    if not todos_livros:
        raise HTTPException(status_code=404, detail="Nenhum livro encontrado.")

    livros_list = [
        {'id': l.id, 'titulo': l.titulo, 'autor': l.autor, 'ano_publicacao': l.ano_publicacao}
        for l in todos_livros
    ]

    await salvar_livros_redis(livros_list, ttl=TTL_5_MIN)

    offset = (page - 1) * limit
    return {
        "source": "database",
        "tempo_resposta_ms": round((time.time() - inicio) * 1000, 2),
        "page": page,
        "limit": limit,
        "total_livros": len(livros_list),
        "livros": livros_list[offset:offset + limit]
    }


@app.post('/adiciona')
async def adiciona_livro(
    livro: Livro,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    db_livro = db.query(LivroDB).filter(
        LivroDB.titulo == livro.titulo,
        LivroDB.autor == livro.autor
    ).first()

    if db_livro:
        raise HTTPException(status_code=400, detail="Livro já existe.")

    novo_livro = LivroDB(
        titulo=livro.titulo,
        autor=livro.autor,
        ano_publicacao=livro.ano_publicacao
    )
    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)

    await deletar_livros_redis()
    await salvar_livro_cache(novo_livro.id, livro, ttl=TTL_1_HORA)

    enviar_evento('livros_eventos', {
        'ação': 'criação',
        'livro': livro.model_dump()
    })

    return {
        'message': 'Livro criado com sucesso!',
        'livro_id': novo_livro.id,
        'cache_invalidado': True
    }


@app.put('/atualiza/{id_livro}')
async def atualiza_livro(
    id_livro: int,
    livro: Livro,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail='Livro não encontrado')

    db_livro.titulo = livro.titulo
    db_livro.autor = livro.autor
    db_livro.ano_publicacao = livro.ano_publicacao
    db.commit()
    db.refresh(db_livro)

    await deletar_livros_redis()
    await deletar_livro_cache(id_livro)
    await salvar_livro_cache(id_livro, livro, ttl=TTL_1_HORA)

    return {'message': 'Livro atualizado com sucesso!', 'cache_invalidado': True}


@app.delete('/delete/{id_livro}')
async def deleta_livro(
    id_livro: int,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail='Livro não localizado')

    db.delete(db_livro)
    db.commit()

    await deletar_livros_redis()
    await deletar_livro_cache(id_livro)

    return {'message': 'Livro deletado com sucesso!', 'cache_invalidado': True}


# ==================== ENDPOINTS DE DEBUG ====================

@app.get('/debug/redis-status')
async def redis_status():
    if not REDIS_DISPONIVEL:
        return {"status": "Redis não disponível", "cache": "desabilitado"}
    try:
        await asyncio.to_thread(redis_client.ping)
        return {"status": "Redis conectado!", "cache": "habilitado", "host": REDIS_HOST, "port": REDIS_PORT}
    except Exception as e:
        return {"status": "Redis com erro", "erro": str(e)}


@app.get('/debug/redis')
async def ver_cache_redis():
    if not REDIS_DISPONIVEL:
        raise HTTPException(status_code=503, detail="Redis não está disponível")
    try:
        chaves = await asyncio.to_thread(redis_client.keys, '*')
        resultado = []
        for chave in chaves:
            valor = await asyncio.to_thread(redis_client.get, chave)
            ttl = await asyncio.to_thread(redis_client.ttl, chave)
            resultado.append({
                "chave": chave,
                "valor": json.loads(valor) if valor else None,
                "ttl_segundos": ttl,
                "expira_em": f"{ttl // 60} minutos e {ttl % 60} segundos" if ttl > 0 else "Sem expiração"
            })
        return {"total_chaves": len(resultado), "dados": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao acessar Redis: {str(e)}")


@app.delete('/debug/limpar-cache')
async def limpar_cache():
    if not REDIS_DISPONIVEL:
        return {"message": "Redis não disponível"}
    try:
        await asyncio.to_thread(redis_client.flushdb)
        return {"message": "✅ Cache limpo com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")