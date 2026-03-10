import pika
import json
import threading
import requests
from flask import Flask, request
import time
import operator
import sys

app = Flask(__name__)

# --- Configuration ---
RABBIT_HOST = 'message-broker'
EXCHANGE_NAME = 'exchange_data'
RULES_API_URL = "http://presentation-service:5050/get_rule"

# Mapping of supported comparison operators
OPERATORI_MAP = {
    '>': operator.gt,   # Greater than
    '<': operator.lt,   # Less than
    '>=': operator.ge,  # Greater or equal
    '<=': operator.le,  # Less or equal
    '=': operator.eq,   # Equal
    '==': operator.eq,
    '!=': operator.ne   # Not equal
}

# Global variables for RabbitMQ
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
    Fetch all active rules from the backend and subscribe
    the engine to the corresponding topics on RabbitMQ.
    """
    print("[AUTOMATION][INFO] Synchronizing rules from backend...")
    try:
        # Call the backend to obtain the full list of topics
        # We assume the backend exposes a GET /api/rules/topics endpoint
        response = requests.get("http://presentation-service:5050/rules", timeout=10)
        response.raise_for_status()
        
        raw_data = response.json()
        
        # Extract topics (sensor_name column) from the database (index 2).
        # The set() removes duplicates before converting back to a list.
        topics = list(set([row[2] for row in raw_data if len(row) > 2]))

        print(f"[AUTOMATION][DEBUG] Initial topics list | topics={topics}", file=sys.stderr, flush=True)
        
        count = 0
        for topic in topics:
            if topic:
                # Performs dynamic binding for each topic found
                channel.queue_bind(
                    exchange=EXCHANGE_NAME, 
                    queue=queue_name, 
                    routing_key=topic
                )
                count += 1
        
        print(f"[AUTOMATION][INFO] Rule synchronization completed | topics_registered={count}")
        
    except Exception as e:
        print(f"[AUTOMATION][ERROR] Initial rule synchronization failed | error={e}")
        # In a real system, you might abort startup or retry after some delay.

# --- Automation logic ---
def process_message(ch, method, properties, body):
    data = json.loads(body)
    topic = data.get("topic")
    
    measurements = data.get("measurements", [])
    print(f"[AUTOMATION][DEBUG] Message received | topic={topic} | measurements={measurements}", file=sys.stderr, flush=True)
    
    try:
        response = requests.post(RULES_API_URL, json={"sensor_name": topic}, timeout=5)
        
        if response.status_code == 200:
            rules = response.json()
            
            if not rules:
                print(f"[AUTOMATION][INFO] No rules configured for topic | topic={topic}", file=sys.stderr, flush=True)
                return

            # --- New block: retrieve current actuator states ---
            # Note: verify=False is used in case the container does not have valid HTTPS certificates
            current_actuators = {}
            try:
                actuators_resp = requests.get("http://mars-simulator:8080/api/actuators", timeout=5, verify=False)
                if actuators_resp.status_code == 200:
                    # Extract actuator dictionary from JSON payload {"actuators": {...}}
                    current_actuators = actuators_resp.json().get("actuators", {})
                else:
                    print(f"[AUTOMATION][WARN] Actuator API returned non-200 status | status={actuators_resp.status_code}", file=sys.stderr, flush=True)
            except requests.exceptions.RequestException as e:
                print(f"[AUTOMATION][ERROR] Actuator API unreachable | error={e}", file=sys.stderr, flush=True)
            # -----------------------------------------------------------------

            for rule_row in rules:
                # Exact mapping to the SQL rules table:
                # 0:id, 1:name, 2:sensor_name, 3:operator, 4:threshold, 5:unit,
                # 6:actuator_name, 7:actuator_state, 8:enabled, 9:created_at

                rule_enabled = rule_row[8]
                if not rule_enabled:
                    continue  # Skip disabled rules immediately

                rule_op_str = rule_row[3]            # Example: ">"
                rule_threshold = float(rule_row[4])  # Example: 30.0
                actuator_name = rule_row[6]          # Example: "fan_01"
                actuator_state = rule_row[7]         # Example: "ON"
                
                # --- New block: skip rule if actuator is already in the desired state ---
                if current_actuators.get(actuator_name) == actuator_state:
                    print(f"[AUTOMATION][DEBUG] Skipping rule because actuator already in desired state | actuator={actuator_name} | state={actuator_state}", file=sys.stderr, flush=True)
                    continue
                # ---------------------------------------------------------------------------------

                # Get the mathematical function corresponding to the operator
                op_func = OPERATORI_MAP.get(rule_op_str)
                if not op_func:
                    print(f"[AUTOMATION][WARN] Operator not supported, rule ignored | operator={rule_op_str}", file=sys.stderr, flush=True)
                    continue
                
                # Apply the rule to the received data
                dispatched_for_rule = False
                for measure in data.get("measurements", []):
                    misurazione = float(measure.get("value", 0))
                    
                    # Evaluate if (measurement OP threshold) is true.
                    # This is equivalent to writing for example "if value > rule_threshold:".
                    if op_func(misurazione, rule_threshold):
                        
                        # --- Alarm triggered ---
                        print(f"[AUTOMATION][INFO] Rule triggered | topic={topic}", file=sys.stderr, flush=True)
                        print(f"[AUTOMATION][DEBUG] Condition satisfied | value={misurazione} | operator={rule_op_str} | threshold={rule_threshold}", file=sys.stderr, flush=True)
                        print(f"[AUTOMATION][DEBUG] Action dispatched | actuator={actuator_name} | target_state={actuator_state}", file=sys.stderr, flush=True)
                        
                        # When an API for real actuators is available, this will trigger it:
                        rule_name = rule_row[1] if len(rule_row) > 1 else ""
                        sender = f"engine:{rule_name}" if rule_name else "engine"
                        requests.post(
                            "http://presentation-service:5050/switch_actuator",
                            json={"actuator": actuator_name, "state": actuator_state, "sender": sender},
                        )
                        dispatched_for_rule = True
                        break

        else:
            print(f"[AUTOMATION][ERROR] Rules API returned non-200 status | status={response.status_code}", file=sys.stderr, flush=True)
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTOMATION][ERROR] Rules API unreachable | error={e}", file=sys.stderr, flush=True)



# --- Backend endpoint (rules update) ---
@app.route('/update-rules', methods=['POST'])
def update_rules():
    global connection, channel, queue_name  # Use the shared global connection
    
    update_info = request.json
    action = update_info.get("action")
    topic = update_info.get("topic")

    # Small helper functions that RabbitMQ will run in its own thread
    def esegui_bind():
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=topic)
        print(f"[AUTOMATION][INFO] Subscribed to topic | topic={topic}")

    def esegui_unbind():
        channel.queue_unbind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=topic)
        print(f"[AUTOMATION][INFO] Unsubscribed from topic | topic={topic}")

    try:
        if action == "add":
            # Ask the connection to safely schedule a bind operation
            connection.add_callback_threadsafe(esegui_bind)
        elif action == "remove":
            # Ask the connection to safely schedule an unbind operation
            connection.add_callback_threadsafe(esegui_unbind)
            
        return {"status": "updated"}, 200
        
    except Exception as e:
        print(f"[AUTOMATION][ERROR] Failed to update routing rules | error={e}")
        return {"status": "error", "message": str(e)}, 500

def start_rabbitmq():
    channel.basic_consume(queue=queue_name, on_message_callback=process_message, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    channel = connect_rabbitmq()

    sync_rules_on_startup()
    
    # Start RabbitMQ in a dedicated thread
    threading.Thread(target=start_rabbitmq, daemon=True).start()
    
    # Start the Flask server to receive updates from the backend
    app.run(host='0.0.0.0', port=6000)