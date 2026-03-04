import sys
import os
import pytest

    # Adiciona a raiz do projeto ao path para que celery_app seja encontrado
    # independente de onde o pytest é executado (ex: dentro da pasta test/)
    #estava dando erro de módulo não encontrado, então adicionei isso para corrigir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from celery_app import calcular_soma, calcular_fatorial


def test_soma_dois_numeros():
    """Verifica se a soma de dois números é calculada corretamente."""
    resultado = calcular_soma(3, 4)
    assert resultado == 7


def test_fatorial_numero():
    """Verifica o cálculo correto do fatorial para um número dado."""
    resultado = calcular_fatorial(5)
    assert resultado == 120


def test_fatorial_zero():
    """Caso de borda: garante que o fatorial de 0 é igual a 1."""
    resultado = calcular_fatorial(0)
    assert resultado == 1