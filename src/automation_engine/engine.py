import pika
import json
import threading
import requests
from flask import Flask, request
import time

app = Flask(__name__)

# --- Configurazione ---
RABBIT_HOST = 'message-broker'
EXCHANGE_NAME = 'exchange_data'
BACKEND_URL = "http://backend-service:5000/api/actuators"

# Variabili globali per RabbitMQ
connection = None
channel = None
queue_name = None

def connect_rabbitmq():
    global channel, queue_name,connection
    while True:
        try:
            connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=RABBIT_HOST, heartbeat=600)
            )
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue
            return channel
        except pika.exceptions.AMQPConnectionError:
            print("cannot create connection with broker")
            time.sleep(2)
    


def sync_rules_on_startup():
    global connection, channel, queue_name
    """
    Recupera tutte le regole attive dal backend e iscrive 
    l'engine ai rispettivi topic su RabbitMQ.
    """
    print(" [*] Sincronizzazione regole in corso...")
    try:
        # Chiamata al backend per ottenere l'elenco completo dei topic
        # Supponiamo che il backend esponga un endpoint GET /api/rules/topics
        response = requests.get(f"{BACKEND_URL}/topics", timeout=10)
        response.raise_for_status()
        
        topics = response.json()  # Ci aspettiamo una lista di stringhe: ["topic1", "topic2", ...]
        
        count = 0
        for topic in topics:
            if topic:
                # Esegue il binding dinamico per ogni topic trovato
                channel.queue_bind(
                    exchange=EXCHANGE_NAME, 
                    queue=queue_name, 
                    routing_key=topic
                )
                count += 1
        
        print(f" [V] Sincronizzazione completata: {count} topic registrati.")
        
    except Exception as e:
        print(f" [!] Errore durante la sincronizzazione iniziale: {e}")
        # In un sistema reale, qui potresti decidere di far fallire l'avvio 
        # o riprovare dopo qualche secondo.

# --- Logica di Automazione ---
def process_message(ch, method, properties, body):
    data = json.loads(body)
    topic = data.get("topic")
    print(data)
    
    # 1. Cerca regole nel DB per questo topic (Esempio semplificato)
    # rule = db.query("SELECT * FROM rules WHERE sensor_id = %s", (topic,))
    rule = {"metric": "temperature", "threshold": 30, "actuator": "fan_01"} # Dummy
    
    # 2. Applica la regola
    for measure in data.get("measurements", []):
        if measure["metric"] == rule["metric"] and measure["value"] > rule["threshold"]:
            # 3. Notifica il Backend
            print(f"!!! REGOLA ATTIVATA per {topic} - Attivazione {rule['actuator']}")
            # requests.post(BACKEND_URL, json={"id": rule["actuator"], "status": "ON"})


# --- Endpoint per il Backend (Aggiornamento Regole) ---
@app.route('/update-rules', methods=['POST'])
def update_rules():
    global connection, channel, queue_name # Usa la connessione globale
    
    update_info = request.json
    action = update_info.get("action")
    topic = update_info.get("topic")

    # Creiamo due piccole funzioni che RabbitMQ eseguirà nel suo thread
    def esegui_bind():
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=topic)
        print(f" [+] Iscritto al nuovo topic: {topic}")

    def esegui_unbind():
        channel.queue_unbind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=topic)
        print(f" [-] Disiscritto dal topic: {topic}")

    try:
        if action == "add":
            # Diciamo alla connessione di eseguire il bind in modo sicuro
            connection.add_callback_threadsafe(esegui_bind)
        elif action == "remove":
            # Diciamo alla connessione di eseguire l'unbind in modo sicuro
            connection.add_callback_threadsafe(esegui_unbind)
            
        return {"status": "updated"}, 200
        
    except Exception as e:
        print(f" [!] Errore: {e}")
        return {"status": "error", "message": str(e)}, 500

def start_rabbitmq():
    channel.basic_consume(queue=queue_name, on_message_callback=process_message, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    channel = connect_rabbitmq()

    #sync_rules_on_startup()
    
    # Avvia RabbitMQ in un thread separato
    threading.Thread(target=start_rabbitmq, daemon=True).start()
    
    # Avvia il server Flask per ricevere aggiornamenti dal Backend
    app.run(host='0.0.0.0', port=6000)