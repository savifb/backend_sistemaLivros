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
from functools import wraps
import time

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
TTL_1_HORA = 3600
TTL_5_MIN = 300

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=6379,
        db=0,
        socket_connect_timeout=2,
        decode_responses=True  # Retorna strings ao invés de bytes
    )
    redis_client.ping()
    print(f"✅ Redis conectado em {REDIS_HOST}:6379")
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


### UMA SESSAO NO BANCO DE DADOS - sessao_db 
def sessao_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

    
# inicializações do FastAPI
app = FastAPI()

MEU_USUARIO = os.getenv('MEU_USUARIO')
MINHA_SENHA = os.getenv('MINHA_SENHA')

# autentificação básica
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

def sync_to_async(func):
    """Decorator para transformar funções síncronas em assíncronas"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper


async def salvar_livro_cache(livro_id: int, livro: Livro, ttl: int = TTL_1_HORA):
    """
    Salva um livro individual no cache
    
    Args:
        livro_id: ID do livro
        livro: Objeto Livro
        ttl: Tempo de vida em segundos (padrão: 1 hora)
    """
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
    """
    Salva uma lista completa de livros no cache Redis
    
    Args:
        livros: Lista de dicionários com dados dos livros
        ttl: Tempo de vida em segundos (padrão: 5 minutos)
    
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    if not REDIS_DISPONIVEL:
        print("⚠️ Redis não disponível - pulando cache")
        return False
    
    try:
        # Serializa a lista de livros para JSON
        livros_json = json.dumps(livros)
        
        # Salva no Redis com TTL usando thread separada (assíncrono)
        await asyncio.to_thread(
            redis_client.setex,
            'livros',  # Chave única para lista completa
            ttl,
            livros_json
        )
        
        print(f"✅ {len(livros)} livros salvos no cache (expira em {ttl}s)")
        return True
    
    except Exception as e:
        print(f"❌ Erro ao salvar livros no cache: {e}")
        return False


async def obter_livros_redis() -> Optional[List[dict]]:
    """
    Busca a lista de livros do cache Redis
    
    Returns:
        List[dict] ou None: Lista de livros se encontrado, None caso contrário
    """
    if not REDIS_DISPONIVEL:
        return None
    
    try:
        # Busca do Redis usando thread separada (assíncrono)
        livros_json = await asyncio.to_thread(
            redis_client.get,
            'livros'
        )
        
        if livros_json:
            livros = json.loads(livros_json)
            print(f"✅ {len(livros)} livros encontrados no cache")
            return livros
        else:
            print("❌ Livros NÃO encontrados no cache")
            return None
    
    except Exception as e:
        print(f"❌ Erro ao buscar livros do cache: {e}")
        return None


async def deletar_livros_redis():
    """
    Remove a lista de livros do cache Redis
    Deve ser chamado após qualquer operação que altere os dados (CREATE, UPDATE, DELETE)
    
    Returns:
        bool: True se deletou com sucesso, False caso contrário
    """
    if not REDIS_DISPONIVEL:
        return False
    
    try:
        # Deleta a chave do Redis usando thread separada (assíncrono)
        result = await asyncio.to_thread(
            redis_client.delete,
            'livros'
        )
        
        if result:
            print("✅ Cache de livros invalidado com sucesso")
            return True
        else:
            print("⚠️ Cache de livros não existia")
            return False
    
    except Exception as e:
        print(f"❌ Erro ao deletar livros do cache: {e}")
        return False


async def obter_livro_cache(livro_id: int) -> Optional[dict]:
    """Busca um livro individual no cache"""
    if not REDIS_DISPONIVEL:
        return None
    
    try:
        valor = await asyncio.to_thread(
            redis_client.get,
            f'livro:{livro_id}'
        )
        
        if valor:
            print(f"✅ Livro {livro_id} encontrado no cache")
            return json.loads(valor)
        else:
            print(f"❌ Livro {livro_id} NÃO está no cache")
            return None
    except Exception as e:
        print(f"❌ Erro ao buscar livro do cache: {e}")
        return None


async def deletar_livro_cache(livro_id: int):
    """Deleta um livro individual do cache"""
    if not REDIS_DISPONIVEL:
        return
    
    try:
        await asyncio.to_thread(
            redis_client.delete,
            f'livro:{livro_id}'
        )
        print(f"✅ Livro {livro_id} removido do cache")
    except Exception as e:
        print(f"❌ Erro ao deletar livro do cache: {e}")


# ==================== ENDPOINTS ====================

@app.get('/livros')
async def get_livros(
    page: int = 1, 
    limit: int = 10, 
    db: Session = Depends(sessao_db), 
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    """
    Lista livros com paginação
    
    Fluxo:
    1. Tenta buscar do cache Redis
    2. Se não encontrar, busca do banco de dados
    3. Salva no cache para próximas requisições
    4. Retorna os dados com informações de origem
    """
    if page < 1 or limit < 1:
        raise HTTPException(
            status_code=400, 
            detail='A página e o limite de livros por página devem ser maiores que zero.'
        )
    
    # Medir tempo de resposta
    inicio = time.time()
    
    # 1️⃣ Tentar buscar do CACHE primeiro
    livros_cache = await obter_livros_redis()
    
    if livros_cache:
        # Cache HIT - dados encontrados no Redis
        # Aplicar paginação nos dados do cache
        offset = (page - 1) * limit
        livros_pagina = livros_cache[offset:offset + limit]
        
        tempo_resposta = round((time.time() - inicio) * 1000, 2)  # em ms
        
        return {
            "source": "cache",  # Indica que veio do cache
            "tempo_resposta_ms": tempo_resposta,
            "page": page,
            "limit": limit,
            "total_livros": len(livros_cache),
            "livros": livros_pagina
        }
    
    # 2️⃣ Cache MISS - buscar do BANCO DE DADOS
    print("⚠️ Cache miss - buscando do banco de dados...")
    
    # Buscar todos os livros do banco
    todos_livros = db.query(LivroDB).all()
    
    if not todos_livros:
        raise HTTPException(status_code=404, detail="Nenhum livro encontrado.")
    
    # Converter para lista de dicionários
    livros_list = [
        {
            'id': livro.id,
            'titulo': livro.titulo,
            'autor': livro.autor,
            'ano_publicacao': livro.ano_publicacao
        } 
        for livro in todos_livros
    ]
    
    # 3️⃣ Salvar no CACHE para próximas requisições
    await salvar_livros_redis(livros_list, ttl=TTL_5_MIN)
    
    # Aplicar paginação
    offset = (page - 1) * limit
    livros_pagina = livros_list[offset:offset + limit]
    
    tempo_resposta = round((time.time() - inicio) * 1000, 2)  # em ms
    
    return {
        "source": "database",  # Indica que veio do banco
        "tempo_resposta_ms": tempo_resposta,
        "page": page,
        "limit": limit,
        "total_livros": len(livros_list),
        "livros": livros_pagina
    }


@app.post('/adiciona')
async def adiciona_livro(
    livro: Livro, 
    db: Session = Depends(sessao_db), 
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    """Adiciona um novo livro e invalida o cache"""
    
    # Verifica se já existe
    db_livro = db.query(LivroDB).filter(
        LivroDB.titulo == livro.titulo, 
        LivroDB.autor == livro.autor
    ).first()
    
    if db_livro:
        raise HTTPException(status_code=400, detail="Livro já existe.")
    
    # Cria novo livro
    novo_livro = LivroDB(
        titulo=livro.titulo, 
        autor=livro.autor, 
        ano_publicacao=livro.ano_publicacao
    )
    
    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)
    
    # ⚠️ IMPORTANTE: Invalidar cache da lista de livros
    await deletar_livros_redis()
    
    # Salvar livro individual no cache (opcional)
    await salvar_livro_cache(novo_livro.id, livro, ttl=TTL_1_HORA)
    
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
    """Atualiza um livro e invalida o cache"""
    
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail='Livro não encontrado')
    
    db_livro.titulo = livro.titulo
    db_livro.autor = livro.autor
    db_livro.ano_publicacao = livro.ano_publicacao
    
    db.commit()
    db.refresh(db_livro)
    
    # ⚠️ IMPORTANTE: Invalidar cache da lista de livros
    await deletar_livros_redis()
    
    # Deletar cache individual antigo e salvar novo
    await deletar_livro_cache(id_livro)
    await salvar_livro_cache(id_livro, livro, ttl=TTL_1_HORA)
    
    return {
        'message': 'Livro atualizado com sucesso!',
        'cache_invalidado': True
    }


@app.delete('/delete/{id_livro}')
async def deleta_livro(
    id_livro: int, 
    db: Session = Depends(sessao_db), 
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    """Deleta um livro e invalida o cache"""
    
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail='Livro não localizado')
    
    db.delete(db_livro)
    db.commit()
    
    # ⚠️ IMPORTANTE: Invalidar cache da lista de livros
    await deletar_livros_redis()
    
    # Deletar cache individual
    await deletar_livro_cache(id_livro)
    
    return {
        'message': 'Livro deletado com sucesso!',
        'cache_invalidado': True
    }


# ==================== ENDPOINTS DE DEBUG ====================

@app.get('/debug/redis-status')
async def redis_status():
    """Verifica status da conexão Redis"""
    if not REDIS_DISPONIVEL:
        return {
            "status": "Redis não disponível",
            "cache": "desabilitado"
        }
    
    try:
        await asyncio.to_thread(redis_client.ping)
        return {
            "status": "Redis conectado!",
            "cache": "habilitado",
            "host": REDIS_HOST,
            "port": 6379
        }
    except Exception as e:
        return {
            "status": "Redis com erro",
            "erro": str(e)
        }


@app.get('/debug/redis')
async def ver_cache_redis():
    """Visualiza todos os dados do cache"""
    if not REDIS_DISPONIVEL:
        raise HTTPException(
            status_code=503, 
            detail="Redis não está disponível"
        )
    
    try:
        # Buscar todas as chaves
        chaves = await asyncio.to_thread(
            redis_client.keys,
            '*'
        )
        
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
        
        return {
            "total_chaves": len(resultado),
            "dados": resultado
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao acessar Redis: {str(e)}"
        )


@app.delete('/debug/limpar-cache')
async def limpar_cache():
    """Limpa TODO o cache Redis"""
    if not REDIS_DISPONIVEL:
        return {"message": "Redis não disponível"}
    
    try:
        await asyncio.to_thread(redis_client.flushdb)
        return {"message": "✅ Cache limpo com sucesso!"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao limpar cache: {str(e)}"
        )