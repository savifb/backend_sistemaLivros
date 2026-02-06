# SISTEMA LIVROS 

# IMPORTAÇÕES FASTAPI E OUTRAS BIBLIOTECAS
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os
import secrets 

load_dotenv()
# IMPORTAÇÕES PARA O BANCO DE DADOS 
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# CONFIGURAÇÕES DO BANCO DE DADOS 

DATABASE_URL = os.getenv('DATABASE_URL')

engine= create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

base = declarative_base()

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


# CODIGO BACKEND PARA GERENCIAR LIVROS


### Estrutura do Livro 
class Livro(BaseModel):
    titulo: str
    autor: str
    ano_publicacao: int

meus_livros = {}


@app.get('/')
def hello_word():
    return {'message': 'Bem Vindo ao Sistema de Livros!'}

@app.get('/livros')
def get_livros(page: int = 1, limit: int = 10, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autentica_usuario)):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail='A pagina e o limite de livros por página devem ser maiores que zero.')
    livros = db.query(LivroDB).offset(page - 1).limit(limit).all()  # quero todos os registros do bd livros // e que sejam apresentados conforme a page e o limit 
    
    total_livros = db.query(LivroDB).count()
    
    if not livros:
        raise HTTPException(status_code=404, detail="Nenhum livro encontrado.")
    
 
    return {
        "page": page,
        "limit": limit,
        "total_livros": total_livros,
        "livros": [{'id' : livro.id, 'titulo': livro.titulo, 'autor': livro.autor, 'ano_publicacao': livro.ano_publicacao} for livro in livros] 
    }
    

# ADICIONA O LIVRO NO BANCO DE DADOS
    
@app.post('/adiciona')
def adiciona_livro(livro: Livro, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autentica_usuario)):
    
    db_livro = db.query(LivroDB).filter(LivroDB.titulo == livro.titulo, LivroDB.autor == livro.autor).first() # variável que só verifica se livro existe em LivroDB
    if db_livro:
        raise HTTPException(status_code=400, detail="Livro já existe.")
    
    # CRIA UM NOVO LIVRO NO LIVRODB DO BACK
    novo_livro = LivroDB(titulo= livro.titulo, autor=livro.autor, ano_publicacao=livro.ano_publicacao)
    
    # ADICIONA O LIVRO
    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)
    return {'message': 'Livro Criado Com Sucesso!'}



@app.put('/atualiza/{id_livro}')
def atualiza_livro(id_livro: int, livro: Livro, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autentica_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail='livro não encontrado')
    db_livro.titulo = livro.titulo
    db_livro.autor = livro.autor
    db_livro.ano_publicacao = livro.ano_publicacao 
    db.commit()
    db.refresh(db_livro)
    
    return {'message': 'Livro atualizado com sucesso!'}
    
    
    
    
    
@app.delete('/delete/{id_livro}')
def deleta_livro(id_livro: int, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autentica_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail='Livro não localizado')
    
    db.delete(db_livro)
    db.commit()
    return {'message': 'Livro deletado com sucesso!'}