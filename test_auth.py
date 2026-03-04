import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

USUARIO_CORRETO = os.getenv("MEU_USUARIO", "admin")
SENHA_CORRETA   = os.getenv("MINHA_SENHA",  "secret")


def test_login_credenciais_corretas():
    """HTTP 200 ao enviar credenciais válidas no endpoint /livros."""
    response = client.get("/livros", auth=(USUARIO_CORRETO, SENHA_CORRETA))

    assert response.status_code == 200


def test_login_senha_incorreta():
    """HTTP 401 ao enviar senha errada."""
    response = client.get("/livros", auth=(USUARIO_CORRETO, "senha_errada"))
    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Usuário ou senha incorretos"


def test_login_usuario_incorreto():
    """HTTP 401 ao enviar usuário errado."""
    response = client.get("/livros", auth=("outro@email.com", SENHA_CORRETA))
    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Usuário ou senha incorretos"


def test_login_ambas_credenciais_incorretas():
    """HTTP 401 quando usuário e senha são inválidos."""
    response = client.get("/livros", auth=("falso@email.com", "senhaerrada"))
    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Usuário ou senha incorretos"