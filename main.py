# SISTEMA LIVROS 

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

meus_livros = {}

class Livro(BaseModel):
    titulo: str
    autor: str
    ano_publicacao: int

@app.get('/livros')
def get_livros():
    if not meus_livros:
        raise HTTPException(status_code=404, detail="Nenhum livro encontrado.")
    else:
        return meus_livros
@app.post('/adiciona')
def adiciona_livro(id_livro: int, livro: Livro):
    if id_livro in meus_livros:
        raise HTTPException(status_code=400, detail="Livro já existe.")
    else:
        meus_livros[id_livro] = livro.model_dump()
        return {'message' : 'Livro Criado Com Sucesso!'}

@app.put('/atualiza/{id_livro}')
def atualiza_livro(id_livro: int, livro: Livro):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404, detail='Livro Não Encontrado.')
    else:
        meus_livros[id_livro] = livro.model_dump()
        return {'message' : 'Livro Atualizado Com Sucesso!'}
    
@app.delete('/delete/{id_livro}')
def deleta_livro(id_livro: int):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404, detail='Livro não localizado')
    else:
        del meus_livros[id_livro]
        return {'message' : 'Livro Deletado Com Sucesso!'}
    
