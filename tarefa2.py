from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional


app = FastAPI()

minhas_tarefas = []

class Tarefa(BaseModel):
    nome_tarefa: str
    descricao: Optional[str] = None
    concluida : bool = False

@app.get('/tarefas')
def get_tarefas():
    if not minhas_tarefas:
        raise HTTPException(status_code=404, detail="Nenhuma tarefa encontrada.")
    else:
        return minhas_tarefas

@app.post('/adiciona')
def adiciona_tarefa(tarefa:Tarefa):
    for i in minhas_tarefas:
        if i['nome_tarefa'] == tarefa.nome_tarefa:
            raise HTTPException(status_code=400, detail="Tarefa já existe.")
       
    minhas_tarefas.append(tarefa.model_dump())
    return {'message' : 'Tarefa Criada Com Sucesso!'}

@app.put('/atualiza/{nome_tarefa}')
def atualiza_tarefa(nome_tarefa: str, tarefa: Tarefa):
    for i in minhas_tarefas:
        if i['nome_tarefa'] == nome_tarefa:
            i.update(tarefa.model_dump())
            return {'message' : 'Tarefa Atualizada Com Sucesso!'}
    raise HTTPException(status_code=404, detail='Tarefa Não Encontrada.')

@app.delete('/delete/{nome_tarefa}')
def detela_tarefa(nome_tarefa: str):
    for i in minhas_tarefas:
        if i['nome_tarefa'] == nome_tarefa:
            minhas_tarefas.remove(i)
            return {'message' : 'Tarefa Deletada Com Sucesso!'}
    raise HTTPException(status_code=404, detail='Tarefa não localizada')