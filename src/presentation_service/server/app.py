from flask import *
from flask_socketio import SocketIO
from db import *
import requests

app = Flask(__name__)
socketio = SocketIO(app)

@app.route("/") 
def dashboard():
    return render_template("index.html")

@app.route("/rules", methods=["GET"])
def get_rules():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rules")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(rows)

@app.route("/add_rule", methods=["POST"])
def add_rule():
    conn = get_connection()
    cur = conn.cursor()

    data = request.json
    name = data.get("name", "")
    sensor_name = data["sensor_name"]
    operator = data["operator"]
    threshold_value = data["threshold_value"]
    unit = data["unit"]
    actuator_name = data["actuator_name"]
    actuator_state = data["actuator_state"]
    enabled = data["enabled"]
    tuple = f"""'{name}', '{sensor_name}', '{operator}', {threshold_value}, '{unit}', '{actuator_name}', '{actuator_state}', {enabled}"""

    cur.execute(
        """INSERT INTO rules (name, sensor_name, operator, threshold_value, unit, actuator_name, actuator_state, enabled) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
        (name, sensor_name, operator, threshold_value, unit, actuator_name, actuator_state, enabled),
    )
    conn.commit()

    cur.close()
    conn.close()

    automation_data = {
        "action": "add",
        "topic": sensor_name
    }
    response = requests.post("http://automation-engine:6000/update-rules", json=automation_data)

    if response.ok:
        return {'ok': True}
    else:
        # Se l'engine fallisce, avvisa il frontend
        return {'ok': False, 'error': 'Errore aggiornamento engine'}, 500

@app.route("/update_rule", methods=["POST"])
def update_rule():
    conn = get_connection()
    cur = conn.cursor()

    data = request.json
    id = data["id"]
    name = data.get("name", "")
    sensor_name = data["sensor_name"]
    operator = data["operator"]
    threshold_value = data["threshold_value"]
    unit = data["unit"]
    actuator_name = data["actuator_name"]
    actuator_state = data["actuator_state"]
    enabled = data["enabled"]

    cur.execute(
        """UPDATE rules 
           SET name=%s,
               sensor_name=%s,
               operator=%s,
               threshold_value=%s,
               unit=%s,
               actuator_name=%s,
               actuator_state=%s,
               enabled=%s
           WHERE id=%s;""",
        (name, sensor_name, operator, threshold_value, unit, actuator_name, actuator_state, enabled, id),
    )
    conn.commit()

    cur.close()
    conn.close()

    return {'ok': True}

@app.route("/delete_rule", methods=["POST"])
def delete_rule():
    conn = get_connection()
    cur = conn.cursor()

    data = request.json
    id = data["id"]

    cur.execute(f"""delete from rules where id={id};""")
    conn.commit()

    cur.close()
    conn.close()

    return {'ok': True}

@app.route("/get_rule", methods=["POST"])
def get_rule():
    conn = get_connection()
    cur = conn.cursor()

    data = request.json

    sensor_name = data["sensor_name"]

    sensor_name = data.get("sensor_name") if data else None


    cur.execute(f"""select * from rules where sensor_name='{sensor_name}';""")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(rows)

from flask import jsonify # Assicurati che sia importato in alto

from flask import jsonify, request

@app.route("/switch_actuator", methods=["POST"])
def switch_actuator():
    data = request.json
    actuator = data.get("actuator")
    state = data.get("state") # "ON" o "OFF"

    if not actuator or not state:
        return jsonify({"error": "Parametri 'actuator' o 'state' mancanti"}), 400

    try:
        # LA MODIFICA È QUI: passiamo un dizionario {"state": state}
        payload = {"state": state}
        response = requests.post(
            f"http://mars-simulator:8080/api/actuators/{actuator}", 
            json=payload, 
            timeout=5
        )

        if response.ok:
            # Notifichiamo il frontend, includendo quale attuatore è cambiato
            socketio.emit("actuator_switch", {"actuator": actuator, "state": state})
            return jsonify({'ok': True})
        else:
            print(f"Errore dal simulatore: {response.text}", flush=True)
            return jsonify({'ok': False, 'error': f"Errore {response.status_code}"}), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({'ok': False, 'error': f"Connessione fallita: {e}"}), 503

@app.route("/update_sensor", methods=["POST"])
def update_sensor():
    data = request.json
    sensor = data.get("topic")
    measurements = data.get("measurements")

    if not sensor or not measurements:
        return jsonify({"error": "Parametri 'sensor' o 'measurements' mancanti"}), 400

    socketio.emit("sensor_update", {"sensor": sensor, "measurements": measurements})
    return jsonify({'ok': True})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5050)

