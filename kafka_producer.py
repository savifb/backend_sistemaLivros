from kafka import KafkaProducer
import json
import os 

KAFKA_SERVER = os.getenv('KAFKA_SERVER', 'localhost:9092')

producer = None

def get_producer():
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_SERVER],  # ✅ typo corrigido
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    return producer

def enviar_evento(topico: str, evento: dict):
    try:
        prod = get_producer()
        prod.send(topico, evento)
        prod.flush()
    except Exception as e:
        print(f"⚠️ Erro ao enviar evento Kafka: {e}")
        raise  # re-lança para o chamador tratar