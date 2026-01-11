from fastapi import FastAPI, HTTPException

# CRUD 
# Create, Read, Update, Delete 
# POST (ADICIONA), GET (LÊ), PUT (ATUALIZA), DELETE (DELETA)
# SISTEMA DE LIVROS 

app = FastAPI()

tarefas = {} 

@app.get('/tarefas')
def chamar_tarefas():
    if not tarefas:
        return{'message': 'Nenhuma tarefa cadastrada'}
    else:
        return tarefas
@app.post('/adicionar')
def adicionar_tarefa(nome_tarefa: str, descricao_tarefa: str, concluida: bool = False):
    if nome_tarefa in tarefas:
        raise HTTPException(status_code=400, detail='tarefa com esse nome já existe')
    else:
        tarefas[nome_tarefa] = {
            'descricao_tarefa': descricao_tarefa,
            'concluida': concluida
        }
        return {'message': 'Tarefa Adicionada com Sucesso'}
    

from fastapi import HTTPException

@app.put('/atualizar/{nome_tarefa}')
def atualizar_tarefa(nome_tarefa: str, concluida: bool = False):
    if nome_tarefa not in tarefas:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    tarefas[nome_tarefa]['concluida'] = concluida

    return {'message': 'Tarefa Atualizada com Sucesso'}


@app.delete('/deletar/{nome_tarefa}')
def deletar_tarefa(nome_tarefa:str):
    minha_tarefa = tarefas.get(nome_tarefa)
    if minha_tarefa not in tarefas: 
        raise HTTPException(status_code=404, detail= 'tarefa não encontrada!')
    else:
        del tarefas[nome_tarefa]
        return {'message': 'Tarefa Mandada Embora'}