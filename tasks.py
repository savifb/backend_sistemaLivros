# tasks.py
# Importa as tarefas do celery_app para manter compatibilidade com os imports do main.py
from celery_app import somar, fatorial

__all__ = ['somar', 'fatorial']