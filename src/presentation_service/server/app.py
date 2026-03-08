from flask import *
from flask_socketio import SocketIO
from db import *

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
    sensor_name = data["sensor_name"]
    operator = data["operator"]
    threshold_value = data["threshold_value"]
    unit = data["unit"]
    actuator_name = data["actuator_name"]
    actuator_state = data["actuator_state"]
    enabled = data["enabled"]
    tuple = f"""'{sensor_name}', '{operator}', {threshold_value}, '{unit}', '{actuator_name}', '{actuator_state}', {enabled}"""

    cur.execute(f"""insert into rules (sensor_name, operator, threshold_value, unit, actuator_name, actuator_state, enabled) values ({tuple});""")
    conn.commit()

    cur.close()
    conn.close()

    automation_data = {
        "action": "add",
        "topic": sensor_name
    }
    response = request.post("http://automation-engine/update-rules", json=automation_data)

    if response.ok:
        return {'ok': True}

@app.route("/update_rule", methods=["POST"])
def update_rule():
    conn = get_connection()
    cur = conn.cursor()

    data = request.json
    id = data["id"]
    sensor_name = data["sensor_name"]
    operator = data["operator"]
    threshold_value = data["threshold_value"]
    unit = data["unit"]
    actuator_name = data["actuator_name"]
    actuator_state = data["actuator_state"]
    enabled = data["enabled"]
    update_query = f"""sensor_name='{sensor_name}', 
                       operator='{operator}', 
                       threshold_value={threshold_value}, 
                       unit='{unit}', 
                       actuator_name='{actuator_name}', 
                       actuator_state='{actuator_state}', 
                       enabled={enabled}"""

    cur.execute(f"""update rules set {update_query} where id={id};""")
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

    cur.execute(f"""select * from rules where sensor_name='{sensor_name}';""")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(rows)


if __name__ == "__main__":
    socketio.run(host="0.0.0.0", port=5050)

