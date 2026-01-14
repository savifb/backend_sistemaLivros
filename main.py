# SISTEMA LIVROS 

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import os 
import secrets 

app = FastAPI()

security = HTTPBasic()

MEU_USUARIO = 'admin'
MINHA_SENHA = 'admin'

meus_livros = {}


def autentica_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    username_correct = secrets.compare_digest(credentials.username, MEU_USUARIO)
    password_correct = secrets.compare_digest(credentials.password, MINHA_SENHA)
    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=401,
            detail='Usuário ou senha incorretos',
            headers={'WWW-Authenticate': 'Basic'},
        )



class Livro(BaseModel):
    titulo: str
    autor: str
    ano_publicacao: int

@app.get('/livros')
def get_livros(page: int = 1, limit: int = 10, credentials: HTTPBasicCredentials = Depends(autentica_usuario)):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail='A pagina e o limite de livros por página devem ser maiores que zero.')
    if not meus_livros:
        raise HTTPException(status_code=404, detail="Nenhum livro encontrado.")
    
    livros_ordenados = sorted(meus_livros.items(), key= lambda x: x[0])
    
    start = (page - 1) * limit
    end = start + limit
    livros_paginados = [
        {"id": id_livro, "titulo": livro_data['titulo'], "autor": livro_data["autor"], "ano_publicacao": livro_data['ano_publicacao']}
        for id_livro, livro_data in livros_ordenados[start:end]
    ]
    
    
    return {
        "page" : page,
        "limit": limit,
        "total_livros" : len(meus_livros),
        "livros": livros_paginados
    }
    
    
@app.post('/adiciona/{id_livro}')
def adiciona_livro(id_livro: int, livro: Livro, credentials: HTTPBasicCredentials = Depends(autentica_usuario)):
    if id_livro in meus_livros:
        raise HTTPException(status_code=400, detail="Livro já existe.")
    else:
        meus_livros[id_livro] = livro.model_dump()
        return {'message' : 'Livro Criado Com Sucesso!'}

@app.put('/atualiza/{id_livro}')
def atualiza_livro(id_livro: int, livro: Livro, credentials: HTTPBasicCredentials = Depends(autentica_usuario)):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404, detail='Livro Não Encontrado.')
    else:
        meus_livros[id_livro] = livro.model_dump()
        return {'message' : 'Livro Atualizado Com Sucesso!'}
    
@app.delete('/delete/{id_livro}')
def deleta_livro(id_livro: int, credentials: HTTPBasicCredentials = Depends(autentica_usuario)):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404, detail='Livro não localizado')
    else:
        del meus_livros[id_livro]
        return {'message' : 'Livro Deletado Com Sucesso!'}