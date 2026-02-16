from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import asyncio

app = FastAPI(title="API de Livros - Async FastAPI")

# ---------------------------
# MODELO DE DADOS (Pydantic)
# ---------------------------

class Livro(BaseModel):
    id: int
    titulo: str
    autor: str
    ano: int

class LivroCreate(BaseModel):
    titulo: str
    autor: str
    ano: int

# ---------------------------
# "BANCO DE DADOS" EM MEMÓRIA
# ---------------------------

livros_db: List[Livro] = []
contador_id = 1

# ---------------------------
# ENDPOINT GET - LISTAR LIVROS
# ---------------------------

@app.get("/livros", response_model=List[Livro])
async def listar_livros():
    """
    Retorna a lista de livros.
    Simula uma operação assíncrona (ex: consulta ao banco).
    """
    await asyncio.sleep(0.1)  # simula I/O não-bloqueante
    return livros_db

# ---------------------------
# ENDPOINT POST - CRIAR LIVRO
# ---------------------------

@app.post("/livros", response_model=Livro)
async def criar_livro(livro: LivroCreate):
    """
    Cria um novo livro e adiciona na lista em memória.
    """
    global contador_id

    await asyncio.sleep(0.1)  # simula operação assíncrona

    novo_livro = Livro(
        id=contador_id,
        titulo=livro.titulo,
        autor=livro.autor,
        ano=livro.ano
    )

    livros_db.append(novo_livro)
    contador_id += 1

    return novo_livro

# ---------------------------
# ENDPOINT PUT - ATUALIZAR LIVRO
# ---------------------------

@app.put("/livros/{id}", response_model=Livro)
async def atualizar_livro(id: int, livro_atualizado: LivroCreate):
    """
    Atualiza os dados de um livro existente.
    """
    await asyncio.sleep(0.1)  # simula operação I/O

    for index, livro in enumerate(livros_db):
        if livro.id == id:
            livro_editado = Livro(
                id=id,
                titulo=livro_atualizado.titulo,
                autor=livro_atualizado.autor,
                ano=livro_atualizado.ano
            )
            livros_db[index] = livro_editado
            return livro_editado

    raise HTTPException(status_code=404, detail="Livro não encontrado")

# ---------------------------
# ENDPOINT DELETE - REMOVER LIVRO
# ---------------------------

@app.delete("/livros/{id}")
async def deletar_livro(id: int):
    """
    Remove um livro da lista.
    """
    await asyncio.sleep(0.1)  # simula operação assíncrona

    for index, livro in enumerate(livros_db):
        if livro.id == id:
            livros_db.pop(index)
            return {"mensagem": "Livro removido com sucesso"}

    raise HTTPException(status_code=404, detail="Livro não encontrado")
