import pika
import json
import threading
import time
import os
import statistics
import matplotlib
import matplotlib.dates as mdates
from datetime import datetime
from collections import deque  
from flask import Flask, request
import socket
import stat

matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

# --- Configurazione ---
RABBIT_HOST = 'message-broker' # Assicurati che coincida con il nome servizio su docker-compose
EXCHANGE_NAME = 'exchange_data'
MAX_HISTORY = 20
sensor_data_history = {}
PDF_OUTPUT_DIR = "/app/reports"

# Variabili globali per RabbitMQ
connection = None
channel = None
queue_name = None

def generate_pdf_report(topic, data_list):
    timestamps = [datetime.fromisoformat(d['timestamp']) for d in data_list]
    values = [d['value'] for d in data_list]
    metric_name = data_list[0]['metric']

    mean_val = statistics.mean(values)
    var_val = statistics.variance(values) if len(values) > 1 else 0.0

    # --- Creazione isolata per Thread ---
    fig, ax = plt.subplots(figsize=(10, 6))
    
    label_text = f"Mean: {mean_val:.2f}\nVariance: {var_val:.2f}"
    ax.plot(timestamps, values, marker='o', linestyle='-', color='#1f77b4', label=label_text)

    ax.set_title(f"Sensor Report: {topic} ({metric_name})")
    ax.set_xlabel("Tempo")
    ax.set_ylabel(f"Value ({metric_name})")
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc="best")
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate() 

    topic_dir = os.path.join(PDF_OUTPUT_DIR, topic)
    os.makedirs(topic_dir, exist_ok=True) 
    
    try:
        os.chmod(topic_dir, 0o777)
    except Exception:
        pass
    
    timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{topic}_report_{timestamp_file}.pdf"
    filepath = os.path.join(topic_dir, filename)
    
    # Salva usando l'oggetto 'fig' specifico
    fig.savefig(filepath, format='pdf', bbox_inches='tight')
    plt.close(fig) # Chiude solo questa specifica figura

    try:
        os.chmod(filepath, 0o777)
    except Exception:
        pass
    
    print(f" [📄] PDF generated: {filepath} with {len(data_list)} real values.")

def connect_rabbitmq():
    global channel, queue_name, connection
    while True:
        try:
            connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=RABBIT_HOST, heartbeat=600)
            )
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue
            print(" [x] Connesso a RabbitMQ con successo.")
            return channel
        except (pika.exceptions.AMQPConnectionError, socket.gaierror) as e:
            print(" [!] Impossibile connettersi al broker. Riprovo in 2 secondi...")
            time.sleep(2)

# --- Logica di Automazione ---
def process_message(ch, method, properties, body):
    global sensor_data_history
    try:
        payload = json.loads(body.decode('utf-8'))
        topic = payload.get("topic")
        
        if topic not in sensor_data_history:
            return

        measurements = payload.get("measurements", [])
        if not measurements:
            return
            
        first_measurement = measurements[0]
        metric_name = first_measurement.get("metric")
        value = first_measurement.get("value")
        timestamp = payload.get("captured_at")
        
        record = {
            "timestamp": timestamp,
            "metric": metric_name,
            "value": value
        }
        
        sensor_data_history[topic].append(record)
        
        # --- LOGICA DI THREADING ---
        if len(sensor_data_history[topic]) >= MAX_HISTORY:
            print(f" [*] Raggiunti {MAX_HISTORY} elementi per {topic}. Avvio worker in background...")
            
            data_to_plot = list(sensor_data_history[topic])
            sensor_data_history[topic].clear()
            
            pdf_worker = threading.Thread(
                target=generate_pdf_report, 
                args=(topic, data_to_plot)
            )
            pdf_worker.daemon = True 
            pdf_worker.start()

    except json.JSONDecodeError:
        print(" [!] Errore: il messaggio ricevuto non è un JSON valido.")
    except Exception as e:
        print(f" [!] Errore nel processamento del messaggio: {e}")

# --- Endpoint per il Backend ---
@app.route('/change_sensor_tracking', methods=['POST'])
def update_rules():
    global connection, channel, queue_name, sensor_data_history 
    
    update_info = request.json
    action = update_info.get("action")
    topic = update_info.get("topic")

    if not action or not topic:
        return {"status": "error", "message": "Mancano action o topic"}, 400

    def esegui_bind():
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=topic)
        print(f" [+] Iscritto al nuovo topic: {topic}")

    def esegui_unbind():
        channel.queue_unbind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=topic)
        print(f" [-] Disiscritto dal topic: {topic}")

    try:
        if action == "add":
            if topic not in sensor_data_history:
                sensor_data_history[topic] = deque(maxlen=MAX_HISTORY)
            connection.add_callback_threadsafe(esegui_bind)
            
        elif action == "remove":
            sensor_data_history.pop(topic, None)
            connection.add_callback_threadsafe(esegui_unbind)
            
        else:
            return {"status": "error", "message": "Azione non valida."}, 400
            
        return {"status": "updated"}, 200
        
    except Exception as e:
        print(f" [!] Errore: {e}")
        return {"status": "error", "message": str(e)}, 500

def start_rabbitmq():
    channel.basic_consume(queue=queue_name, on_message_callback=process_message, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    channel = connect_rabbitmq()
    
    # Avvia RabbitMQ in un thread separato
    threading.Thread(target=start_rabbitmq, daemon=True).start()
    
    # Avvia il server Flask
    app.run(host='0.0.0.0', port=3030)