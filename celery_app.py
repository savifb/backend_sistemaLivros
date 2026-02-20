from celery import Celery
import os
import time

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')

app = Celery(
    'tarefa_livros',
    broker=REDIS_URL,
    backend=REDIS_URL,
)

app.conf.update(
    task_track_started=True,
    result_expires=3600,
    result_persistent=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json']
)


@app.task(name='calcular_soma')
def calcular_soma(numero1: int, numero2: int) -> int:
    """
    Tarefa Celery: soma dois números.
    time.sleep() simula uma operação demorada (workload).
    """
    time.sleep(5)
    resultado = numero1 + numero2
    print(f"✅ Soma concluída: {numero1} + {numero2} = {resultado}")
    return resultado


@app.task(name='calcular_fatorial')
def calcular_fatorial(n: int) -> int:
    """
    Tarefa Celery: calcula o fatorial de n.
    - Implementação iterativa: evita RecursionError para valores grandes de n.
    - Python suporta inteiros de precisão arbitrária, sem risco de overflow.
    - time.sleep() simula uma operação demorada (workload).
    """
    if n < 0:
        raise ValueError("Fatorial não é definido para números negativos.")

    time.sleep(5)

    resultado = 1
    for i in range(2, n + 1):
        resultado *= i

    print(f"✅ Fatorial concluído: {n}! = {resultado}")
    return resultado