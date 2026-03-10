import pika
import json
import time
import requests

STATE= None

# 1. CONNECTION PIPELINE (same retry mechanism)
def connect_to_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('message-broker'))
            print("[STATE][INFO] Connected to RabbitMQ")
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("[STATE][WARN] RabbitMQ not ready yet, retrying in 3 seconds...")
            time.sleep(3)


# 3. CONSUMPTION PIPELINE (callback)
def callback(ch, method, properties, body):
    try:
        # Decode the incoming message payload
        data = json.loads(body)
        print(f"[STATE][DEBUG] Message received | topic={data.get('topic')} | measurements={data.get('measurements', [])}")
        
        response = requests.post(
            "http://presentation-service:5050/update_sensor", 
            json={"topic": data['topic'], "measurements": data['measurements']}
        )
        
        # Optional: helpful print to know that forwarding succeeded
        print(f"[STATE][INFO] Forwarded message to presentation-service | status_code={response.status_code}")

    except Exception as e:
        # Catch any processing error and log it
        print(f"[STATE][ERROR] Error while processing message | error={e}")


def create_state():
    print("[STATE][INFO] Waiting for mars-simulator to become available...", flush=True)
    
    # 1. Retry loop until the simulator responds
    while True:
        try:
            print("[STATE][DEBUG] Probing mars-simulator endpoints...", flush=True)
            sensors_req = requests.get("http://mars-simulator:8080/api/sensors", timeout=5)
            telemetry_req = requests.get("http://mars-simulator:8080/api/telemetry/topics", timeout=5)
            actuators_req = requests.get("http://mars-simulator:8080/api/actuators", timeout=5)
            
            # Ensure all responses are 200 OK before proceeding
            # sensors_req.raise_for_status()
            # telemetry_req.raise_for_status()
            # actuators_req.raise_for_status()
            
            # If we reach this point, all calls finished successfully
            sensors = sensors_req.json().get('sensors', [])
            
            telemetry = [
                t.split('/')[-1] 
                for t in telemetry_req.json().get('topics', [])
            ]
            
            actuators = list(actuators_req.json().get('actuators', {}).keys())
            
            print("[STATE][INFO] mars-simulator is ready, data retrieved successfully")
            break  # Exit the infinite loop
            
        except requests.exceptions.RequestException as e:
            # Catch connection errors, timeouts, or HTTP errors (e.g. 500/404)
            print("[STATE][WARN] mars-simulator not ready yet, retrying in 3 seconds...")
            time.sleep(3)

    # 2. Create the STATE dictionary
    STATE = {
        **{sensor: 0 for sensor in sensors},
        **{tel: 0 for tel in telemetry},
        **{actuator: "OFF" for actuator in actuators}
    }
    print(f"[STATE][DEBUG] Initial state created | sensors={len(sensors)} | telemetry={len(telemetry)} | actuators={len(actuators)}")

    return STATE



if __name__ == "__main__":
    print("[STATE][INFO] Starting state service", flush=True)
    time.sleep(5)
    create_state()
    print("[STATE][INFO] Initial state created successfully")

    connection = connect_to_rabbitmq()
    channel = connection.channel()

    # 2. DECLARATION AND BINDING PIPELINE
    exchange_name = 'exchange_data'
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

    # Create a unique queue for this subscriber
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(
    exchange=exchange_name, 
    queue=queue_name, 
    routing_key='#'
    )

    print("[STATE][INFO] Waiting for messages on all topics")

    # Start continuous consuming
    channel.basic_consume(
        queue=queue_name, 
        on_message_callback=callback, 
        auto_ack=True
    )

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[STATE][INFO] Shutting down subscriber due to keyboard interrupt")
    finally:
        connection.close()