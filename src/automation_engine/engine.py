import pika
import json
import threading
import requests
from flask import Flask, request
import time
import operator
import sys

app = Flask(__name__)

# --- Configurazione ---
RABBIT_HOST = 'message-broker'
EXCHANGE_NAME = 'exchange_data'
RULES_API_URL = "http://presentation-service:5050/get_rule"

OPERATORI_MAP = {
    '>': operator.gt,   # Greater Than
    '<': operator.lt,   # Less Than
    '>=': operator.ge,  # Greater or Equal
    '<=': operator.le,  # Less or Equal
    '=': operator.eq,   # Equal
    '==': operator.eq,
    '!=': operator.ne   # Not Equal
}

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
        response = requests.get("http://presentation-service:5050/rules", timeout=10)
        response.raise_for_status()
        
        raw_data = response.json()  
        
        # Estrae i topic (colonna 1) dal database. 
        # Il set() serve a rimuovere i duplicati prima di convertirli di nuovo in una lista.
        topics = list(set([row[1] for row in raw_data if len(row) > 1]))

        print(f"initial topics: {topics}", file=sys.stderr, flush=True)
        
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
    
    print(f"\n---> [RICEVUTO] Topic: {topic} | Dati: {data}", file=sys.stderr, flush=True)
    
    try:
        response = requests.post(RULES_API_URL, json={"sensor_name": topic}, timeout=5)
        
        if response.status_code == 200:
            rules = response.json()
            
            if not rules:
                print(f"---> [INFO] Nessuna regola per {topic}", file=sys.stderr, flush=True)
                return

            for rule_row in rules:
                # 🎯 Mappatura esatta sulla tua tabella SQL:
                # 0:id, 1:sensor_name, 2:operator, 3:threshold, 4:unit, 
                # 5:actuator_name, 6:actuator_state, 7:enabled, 8:created_at
                
                rule_enabled = rule_row[7]
                if not rule_enabled:
                    continue # Salta subito le regole disattivate (geniale averlo nel DB!)

                rule_op_str = rule_row[2]            # es: ">"
                rule_threshold = float(rule_row[3])  # es: 30.0
                actuator_name = rule_row[5]          # es: "fan_01"
                actuator_state = rule_row[6]         # es: "ON"
                
                # Prende la funzione matematica corrispondente all'operatore
                op_func = OPERATORI_MAP.get(rule_op_str)
                if not op_func:
                    print(f"Operatore ignorato: {rule_op_str}", file=sys.stderr, flush=True)
                    continue
                
                # Applica la regola ai dati ricevuti
                for measure in data.get("measurements", []):
                    misurazione = float(measure.get("value", 0))
                    
                    # MAGIA: valuta se (misurazione OPERATORE soglia) è vero.
                    # Equivale a scrivere "if misurazione > rule_threshold:"
                    if op_func(misurazione, rule_threshold):
                        
                        # --- ALLARME SCATTATO ---
                        print(f"!!! REGOLA ATTIVATA per {topic} !!!", file=sys.stderr, flush=True)
                        print(f"    Condizione verificata: {misurazione} {rule_op_str} {rule_threshold}", file=sys.stderr, flush=True)
                        print(f"    -> AZIONE: Imposta {actuator_name} su {actuator_state}", file=sys.stderr, flush=True)
                        
                        # Se/quando avrai l'API per comandare gli attuatori reali:
                        requests.post("http://presentation-service:5050/switch_actuator", json={"actuator": actuator_name, "state": actuator_state})

        else:
            print(f"---> [ERRORE API] Codice: {response.status_code}", file=sys.stderr, flush=True)
            
    except requests.exceptions.RequestException as e:
        print(f"---> [ERRORE RETE] API irraggiungibile: {e}", file=sys.stderr, flush=True)



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

    sync_rules_on_startup()
    
    # Avvia RabbitMQ in un thread separato
    threading.Thread(target=start_rabbitmq, daemon=True).start()
    
    # Avvia il server Flask per ricevere aggiornamenti dal Backend
    app.run(host='0.0.0.0', port=6000)