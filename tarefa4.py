from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional, Dict, List
import secrets

app = FastAPI()

# IMPORTAÇÕES BANCO

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


# CONFIGURAÇÕES BANCO

DATABASE_URL = 'sqlite:///./tarefas.db'
# a engine serve para fazer a comunicação com o banco de dados e é criada com a função create_engine no caso é o banco sqlite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# sessionLocal cria as sessões de comunicação com o banco de dados
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# base é a classe base para a criação das tabelas no banco de dados - servindo como o backend comunicando com o banco
base = declarative_base()

class TarefaDB(base):
    __tablename__ = 'Tarefas'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    descricao = Column(String, index=True)
    concluida = Column(String, index=True)

# o base.metadata.create_all cria as tabelas no banco de dados com base na classe definida acima
base.metadata.create_all(bind=engine)

# criando a função para quando eu quiser acessar o banco de dados - através de um sessao no banco de dados 

def sessao_db():
    db = sessionLocal() # conectando com o local
    try:
        yield db
    finally:
        db.close()

# =========================

security = HTTPBasic()

meu_login = 'admin'
minha_senha = 'admin'

def autentica_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    if not (
        secrets.compare_digest(credentials.username, meu_login) and
        secrets.compare_digest(credentials.password, minha_senha)
    ):
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# =========================
# MODELO
# =========================

class Tarefa(BaseModel):
    nome: str
    descricao: str
    concluida: bool = False
    




minhas_tarefas: Dict[str, Tarefa] = {}


# =========================
# LISTAR TAREFAS
# =========================

@app.get('/tarefas')
def get_tarefas(
    page: int,
    size: int,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    if page < 1 or size < 1:
        raise HTTPException(400, "Página e tamanho devem ser maiores que zero.")

    tarefas = db.query(TarefaDB).offset(page - 1).limit(size).all()
    
    total_tarefas = db.query(TarefaDB).count()
    
    if not tarefas:
        raise HTTPException(404, "Nenhuma tarefa cadastrada.")


    return {
        "pagina": page,
        "tamanho": size,
        "total": total_tarefas,
        "tarefas": [{'id': tarefa.id, 'nome': tarefa.nome, 'descricao': tarefa.descricao, 'concluida': tarefa.concluida} for tarefa in tarefas]
    }


# =========================
# CRIAR
# =========================

@app.post('/adiciona')
def adiciona_tarefa(tarefa: Tarefa, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autentica_usuario)):
    tarefa_existe = db.query(TarefaDB).filter(TarefaDB.nome == tarefa.nome).first()
    if tarefa_existe:
        raise HTTPException(400, "Tarefa já existe.")

    nova_tarefa = TarefaDB(
        nome=tarefa.nome,
        descricao=tarefa.descricao,
        concluida=tarefa.concluida
    )

    db.add(nova_tarefa)
    db.commit()
    db.refresh(nova_tarefa)
    return {'message': 'Tarefa criada com sucesso!'}

# =========================
# ATUALIZAR
# =========================

@app.put('/atualiza/{id}', response_model=Tarefa)
def atualiza_tarefa(
    id: int,
    tarefa: Tarefa,
    db : Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    tarefa_db = db.query(TarefaDB).filter(TarefaDB.id == id).first()
    if not tarefa_db:
        raise HTTPException(404, "Tarefa não encontrada.")
    
    tarefa_db.nome = tarefa.nome
    tarefa_db.descricao = tarefa.descricao
    tarefa_db.concluida = tarefa.concluida

    db.commit()
    db.refresh(tarefa_db)
    return tarefa_db
# =========================
# DELETAR
# =========================

@app.delete('/delete/{id}')
def deleta_tarefa(
    id: int,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    tarefa_db = db.query(TarefaDB).filter(TarefaDB.id == id).first()
    if not tarefa_db:
        raise HTTPException(404, "Tarefa não localizada.")

    db.delete(tarefa_db)
    db.commit()
    return {"message": "Tarefa deletada com sucesso"}
