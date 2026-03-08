import time
import json
import threading
import requests
import pika
from sseclient import SSEClient

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
    "http://mars-simulator:8080/api/telemetry/stream/mars/telemetry/airlock",
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

# --- Funzione placeholder per la normalizzazione ---
def normalize_message(msg):
    """
    Per ora ritorna direttamente il messaggio così com'è.
    Poi possiamo implementare regole di normalizzazione.
    """

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
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("cannot create connection with broker")

# --- Funzione per inviare messaggi a RabbitMQ ---
def send_to_rabbitmq(message, connection):
    try:
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=message["topic"],
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # rende il messaggio persistente
            )
        )
        connection.close()
        print(f"Messaggio inviato a RabbitMQ: {message}")
    except Exception as e:
        print(f"Errore RabbitMQ: {e}")

# --- Thread per i topic SSE ---
def listen_sse(url, connection):
    while True:
        try:
            messages = SSEClient(url)
            for msg in messages:
                if msg.data:
                    try:
                        data = json.loads(msg.data)
                        normalized = normalize_message(data)
                        send_to_rabbitmq(normalized, connection)
                    except json.JSONDecodeError:
                        print(f"Dati SSE non validi: {msg.data}")
        except Exception as e:
            print(f"Errore SSE {url}: {e}")
            time.sleep(5)  # ritenta dopo 5 secondi

# --- Thread per chiamate GET periodiche ---
def poll_get(url, interval=5, connection):
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            normalized = normalize_message(data)
            send_to_rabbitmq(normalized, connection)
        except requests.RequestException as e:
            print(f"Errore GET {url}: {e}")
        time.sleep(interval)

# --- Main ---
if __name__ == "__main__":
    connection = create_connection()
    threads = []

    # Avvia thread SSE
    for sse_url in SSE_TOPICS:
        t = threading.Thread(target=listen_sse, args=(sse_url,connection, ), daemon=True)
        t.start()
        threads.append(t)

    # Avvia thread GET periodiche
    for get_url in GET_TOPICS:
        t = threading.Thread(target=poll_get, args=(get_url,connection, ), daemon=True)
        t.start()
        threads.append(t)

    # Loop principale per tenere vivo il processo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrotto manualmente.")
