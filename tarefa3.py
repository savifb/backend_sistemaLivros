from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional, Dict, List
import secrets

app = FastAPI()

# =========================
# AUTENTICAÇÃO
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

@app.get('/tarefas', dependencies=[Depends(autentica_usuario)])
def get_tarefas(
    page: int,
    size: int,
    ordenar_por: Optional[str] = None
):
    if page < 1 or size < 1:
        raise HTTPException(400, "Página e tamanho devem ser maiores que zero.")

    tarefas_lista = list(minhas_tarefas.values())

    if not tarefas_lista:
        raise HTTPException(404, "Nenhuma tarefa cadastrada.")

    if ordenar_por:
        if ordenar_por not in ["nome", "descricao", "concluida"]:
            raise HTTPException(400, "Parâmetro de ordenação inválido.")
        tarefas_lista.sort(key=lambda t: getattr(t, ordenar_por))

    inicio = (page - 1) * size
    fim = inicio + size
    tarefas_paginadas = tarefas_lista[inicio:fim]

    if not tarefas_paginadas:
        raise HTTPException(404, "Nenhuma tarefa encontrada para esta página.")

    return {
        "pagina": page,
        "tamanho": size,
        "total": len(tarefas_lista),
        "tarefas": tarefas_paginadas
    }


# =========================
# CRIAR
# =========================

@app.post('/adiciona/{id}', response_model=Tarefa, status_code=201)
def adiciona_tarefa(
    id : int,
    tarefa: Tarefa,
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    if id in minhas_tarefas:
        raise HTTPException(400, "Tarefa já existe.")

    minhas_tarefas[id] = tarefa
    return tarefa


# =========================
# ATUALIZAR
# =========================

@app.put('/atualiza/{id}', response_model=Tarefa)
def atualiza_tarefa(
    id: int,
    tarefa: Tarefa,
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    if id not in minhas_tarefas:
        raise HTTPException(404, "Tarefa não encontrada.")

    minhas_tarefas[id] = tarefa
    return tarefa


# =========================
# DELETAR
# =========================

@app.delete('/delete/{nome}')
def deleta_tarefa(
    nome: str,
    credentials: HTTPBasicCredentials = Depends(autentica_usuario)
):
    if nome not in minhas_tarefas:
        raise HTTPException(404, "Tarefa não localizada.")

    del minhas_tarefas[nome]
    return {"message": "Tarefa deletada com sucesso"}
