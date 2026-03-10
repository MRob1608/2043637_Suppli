import time
import json
import threading
import requests
import pika
from sseclient import SSEClient

from sensor_normalizer import normalize_sensor_reading

# --- Configurazione ---
GET_TOPICS = [
    "http://mars-simulator:8080/api/sensors/greenhouse_temperature",
    "http://mars-simulator:8080/api/sensors/entrance_humidity",
    "http://mars-simulator:8080/api/sensors/co2_hall",
    "http://mars-simulator:8080/api/sensors/hydroponic_ph",
    "http://mars-simulator:8080/api/sensors/water_tank_level",
    "http://mars-simulator:8080/api/sensors/corridor_pressure",
    "http://mars-simulator:8080/api/sensors/air_quality_pm25",
    "http://mars-simulator:8080/api/sensors/air_quality_voc"
]

SSE_TOPICS = [
    "http://mars-simulator:8080/api/telemetry/stream/mars/telemetry/solar_array",
    "http://mars-simulator:8080/api/telemetry/stream/mars/telemetry/radiation",
    "http://mars-simulator:8080/api/telemetry/stream/mars/telemetry/life_support",
    "http://mars-simulator:8080/api/telemetry/stream/mars/telemetry/thermal_loop",
    "http://mars-simulator:8080/api/telemetry/stream/mars/telemetry/power_bus",
    "http://mars-simulator:8080/api/telemetry/stream/mars/telemetry/power_consumption",
    "http://mars-simulator:8080/api/telemetry/stream/mars/telemetry/airlock"
]

RABBITMQ_HOST = "message-broker"
RABBITMQ_QUEUE = "telemetry_queue"
EXCHANGE_NAME = 'exchange_data'

# Lock per pubblicare su RabbitMQ (channel non è thread-safe)
_publish_lock = threading.Lock()

# --- Funzione di normalizzazione allo schema unificato ---
def normalize_message(msg):
    """
    Normalizza il payload (REST o telemetria) nello schema unificato.
    La source viene inferita: se c'è "topic" è telemetry, altrimenti rest.
    Aggiunge "topic" per il routing_key RabbitMQ (uguale a "id").
    """
    source = "telemetry" if "topic" in msg and "sensor_id" not in msg else "rest"
    try:
        normalized = normalize_sensor_reading(msg, source)
        normalized["topic"] = normalized["id"]
        return normalized
    except ValueError as e:
        print(f"Normalizzazione fallita, messaggio inalterato: {e}")
        return msg

# --- Funzione per creare una connessione persistente con RabbitMQ
def create_connection():
    while True:
        try:
            connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600)
            )
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
            return connection, channel
        except pika.exceptions.AMQPConnectionError:
            print("cannot create connection with broker")
            time.sleep(5)

# --- Funzione per inviare messaggi a RabbitMQ ---
def send_to_rabbitmq(message, connection, channel):
    try:
        with _publish_lock:
            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=message["topic"],
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2  # rende il messaggio persistente
                )
            )
        # Non chiudere la connessione: è condivisa tra i thread
        print(f"Messaggio inviato a RabbitMQ: {message.get('topic', message.get('id', ''))}")
    except Exception as e:
        print(f"Errore RabbitMQ: {e}")

# --- Thread per i topic SSE ---
def listen_sse(url, connection, channel):
    while True:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            client = SSEClient(response)
            for msg in client.events():
                if msg.data:
                    try:
                        data = json.loads(msg.data)
                        normalized = normalize_message(data)
                        print(normalized)
                        send_to_rabbitmq(normalized, connection, channel)
                    except json.JSONDecodeError:
                        print(f"Dati SSE non validi: {msg.data}")
        except Exception as e:
            print(f"Errore SSE {url}: {e}")
            time.sleep(5)  # ritenta dopo 5 secondi

# --- Thread per chiamate GET periodiche ---
def poll_get(url, connection, channel, interval=5):
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            normalized = normalize_message(data)
            print(normalized)
            send_to_rabbitmq(normalized, connection, channel)
        except requests.RequestException as e:
            print(f"Errore GET {url}: {e}")
        time.sleep(interval)

# --- Main ---
if __name__ == "__main__":
    connection, channel = create_connection()
    threads = []

    # Avvia thread SSE
    for sse_url in SSE_TOPICS:
        t = threading.Thread(target=listen_sse, args=(sse_url, connection, channel), daemon=True)
        t.start()
        threads.append(t)

    # Avvia thread GET periodiche
    for get_url in GET_TOPICS:
        t = threading.Thread(target=poll_get, args=(get_url, connection, channel), daemon=True)
        t.start()
        threads.append(t)

    # Loop principale per tenere vivo il processo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrotto manualmente.")
