from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

class Tarefa(BaseModel):
    nome: str 
    descricao: str  
    concluida: bool = False 

app = FastAPI()

minhas_tarefas: List[Tarefa] = []

class Tarefa(BaseModel):
    nome: str   
    descricao: str   
    concluida: bool = False  

@app.get('/tarefas', response_model=List[Tarefa])  
def get_tarefas():
    if not minhas_tarefas:
        raise HTTPException(status_code=404, detail="Nenhuma tarefa encontrada.")
    return minhas_tarefas

@app.post('/adiciona', response_model=Tarefa, status_code=201)
def adiciona_tarefa(tarefa: Tarefa):
    for t in minhas_tarefas:
        if t.nome == tarefa.nome: 
            raise HTTPException(status_code=400, detail="Tarefa já existe.")
    
   
    minhas_tarefas.append(tarefa)
    return tarefa

@app.put('/atualiza/{nome}', response_model=Tarefa)  
def atualiza_tarefa(nome: str, tarefa: Tarefa):
    for i, t in enumerate(minhas_tarefas): 
        if t.nome == nome:  
            minhas_tarefas[i] = tarefa 
            return tarefa
    raise HTTPException(status_code=404, detail='Tarefa Não Encontrada.')

@app.delete('/delete/{nome}') 
def deleta_tarefa(nome: str):
    for index, tarefa in enumerate(minhas_tarefas):
        if tarefa.nome == nome:  
            tarefa_deletada = minhas_tarefas.pop(index)
            return {
                'message': 'Tarefa Deletada Com Sucesso!',
                'tarefa': tarefa_deletada
            }
    raise HTTPException(status_code=404, detail='Tarefa não localizada')