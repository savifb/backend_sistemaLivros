from celery_app import app 
import time

import celery_app

@celery_app.task(name='somar', bind=True)
def somar(self, a, b):
    return a+b

@celery_app.task(name='fatorial', bind=True)
def fatorial(self, n):
    if n < 0:
        raise ValueError("Fatorial não é definido para números negativos.")
    
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado

