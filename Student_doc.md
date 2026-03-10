# SYSTEM DESCRIPTION:

This project is a multi-container IoT monitoring and control system for a Mars habitat simulation. It ingests sensor and telemetry data from an external simulator (`mars-simulator`), routes data via RabbitMQ (`message-broker`), persists and applies automation rules using a PostgreSQL rules database (`rule-database`) and an automation engine (`automation-engine`), presents a real‑time dashboard and rule management UI via a Flask-based presentation service (`presentation-service`), maintains streaming state and forwards data to the frontend via a state service (`state`), and generates PDF reports for selected sensors via a report service (`report-service`).

# USER STORIES:

#### US-01 – View sensors
* **As a** habitat operator
* **I want to** see the list of available sensors
* **So that** I can monitor the habitat systems.

#### US-02 – View sensors values
* **As a** habitat operator
* **I want to** see the current values of sensors
* **So that** I can monitor environmental conditions.

#### US-03 – View sensors measure units
* **As a** habitat operator
* **I want to** see the unit of measurement of each sensor
* **So that** I can correctly interpret the values.

#### US-04 – View actuators
* **As a** habitat operator
* **I want to** see the list of actuators
* **So that** I know which devices can be controlled.

#### US-05 – View actuator state
* **As a** habitat operator
* **I want to** see the current state of an actuator
* **So that** I know whether it is ON or OFF.

#### US-06 – View system rules
* **As a** habitat operator
* **I want to** see the list of automation rules
* **So that** I can review system automation.

### ---- RULE MANAGEMENT ----

#### US-07 – Create new rule
* **As a** habitat operator
* **I want to** create new automation rules
* **So that** the system can automatically react to sensor values and interact with the environment.

#### US-08 – Update rule
* **As a** habitat operator
* **I want to** update already existing automation rules
* **So that** the system can respond to new conditions.

#### US-09 – Delete rule
* **As a** habitat operator
* **I want to** delete an automation rule
* **So that** I can remove outdated automation.

#### US-10 – Disable and/or enable rule
* **As a** habitat operator
* **I want to** disable and/or enable an automation rule
* **So that** I can handle in real time automation.

### ---- ACTUATOR MANAGEMENT ----

#### US-11 - Automated Actuator control
* **As a** habitat operator
* **I want** the system to automatically activate actuators when rule conditions are met
* **So that** environmental conditions are maintained.

#### US-12 – Manual Actuator control
* **As a** habitat operator
* **I want to** manually activate or deactivate an actuator
* **So that** I can override automation when necessary.

### ---- SYSTEM ALERTS, LOGS AND TELEMETRY ----

#### US-13 – View sensor warnings
* **As a** habitat operator
* **I want to** see visual warnings or alerts for REST sensors when they exceed critical thresholds or become unreachable
* **So that** I can quickly identify and react to life-support anomalies.

#### US-14 – View actuator activation history
* **As a** habitat operator
* **I want to** view a terminal or log showing the history of actuator state changes (both manual and rule-triggered)
* **So that** I can trace system actions and audit the automation behavior.

#### US-15 – Persist automation rules
* **As a** system operator
* **I want** the automation rules to be persisted in a database
* **So that** the habitat automation logic is preserved and restored automatically after a system reboot or failure.

#### US-16 – View real-time telemetry trends
* **As a** system operator
* **I want to** see live line charts for telemetry data (e.g., power_bus, radiation)
* **So that** I can analyze immediate trends.
* **NFR:** Real-time updates must be handled with low latency via WebSocket or SSE.

# CONTAINERS:

## CONTAINER_NAME: mars-simulator

### DESCRIPTION:

External IoT simulator container providing sensor, telemetry, and actuator HTTP APIs, used as the data source and target for commands. Defined in `src/docker-compose.yml` as `mars-simulator` using image `mars-iot-simulator:multiarch_v1`.

### USER STORIES:

- Supports all user stories that depend on simulated sensors, telemetry, and actuators (monitoring, manual control, automation), by exposing:
  - Sensor endpoints such as `/api/sensors`, `/api/sensors/<sensor_id>` (referenced in ingestion and state services).
  - Telemetry endpoints such as `/api/telemetry/topics` and `/api/telemetry/stream/...`.
  - Actuator endpoints `/api/actuators` and `/api/actuators/<actuator>` (referenced in `automation_engine/engine.py` and `presentation_service/server/app.py`).

### PORTS:

- Host `8080` mapped to container port `8080` (`"8080:8080"` in `docker-compose.yml`).

### PERSISTENCE EVALUATION

- No explicit volumes defined for this container in `docker-compose.yml`; its data is not configured as persistent within this project definition.

### EXTERNAL SERVICES CONNECTIONS

- Acts as an external service for other containers:
  - `ingestion-service` polls and subscribes via HTTP and SSE (e.g., `http://mars-simulator:8080/api/sensors/...`, `.../api/telemetry/stream/...`).
  - `state` service calls `http://mars-simulator:8080/api/sensors`, `/api/telemetry/topics`, `/api/actuators`.
  - `automation-engine` calls `http://mars-simulator:8080/api/actuators`.
  - `presentation-service` calls `http://mars-simulator:8080/api/actuators/<actuator>` via `/switch_actuator`.

### MICROSERVICES:

#### MICROSERVICE: mars-simulator

* TYPE: backend

* DESCRIPTION: HTTP API simulator that exposes sensor, telemetry, and actuator endpoints used by the ingestion, state, automation, and presentation services. The actual implementation is external to this repo.

* PORTS: 8080 (inside container; exposed as `8080:8080`).

* SERVICE ARCHITECTURE:

  Acts as an upstream REST/SSE provider. Other microservices perform:
  - Periodic GET requests to sensor endpoints (`/api/sensors/<id>`) and telemetry SSE streams (`/api/telemetry/stream/...`).
  - Reads of aggregated lists (`/api/sensors`, `/api/telemetry/topics`, `/api/actuators`).
  - POST commands to `/api/actuators/<actuator>` to change actuator state.


* PAGES:

  N/A (backend service).

* DB STRUCTURE:

  N/A (database not defined in this repository for this container).

---

## CONTAINER_NAME: message-broker

### DESCRIPTION:

RabbitMQ message broker providing AMQP messaging for telemetry and sensor data distribution across services. Defined in `src/docker-compose.yml` as `message-broker` using image `rabbitmq:3-management`.

### USER STORIES:

- Enables real-time distribution of ingested sensor and telemetry data so that:
  - The automation engine can apply rules.
  - The state service can forward updates to the frontend.
  - The report service can generate historical reports for selected sensors.

### PORTS:

- `5672:5672` (AMQP).
- `15672:15672` (RabbitMQ management UI).

### PERSISTENCE EVALUATION

- No `volumes` defined specifically for this service in `docker-compose.yml`; broker data (queues/messages) are not explicitly persisted across container restarts within this project configuration.

### EXTERNAL SERVICES CONNECTIONS

- No outgoing connections to other external systems defined here.
- Internal AMQP connections from:
  - `ingestion-service` (producer).
  - `automation-engine` (consumer).
  - `state` (consumer).
  - `report-service` (consumer).

### MICROSERVICES:

#### MICROSERVICE: message-broker (RabbitMQ)

* TYPE: backend

* DESCRIPTION: Provides topic-based messaging (`exchange_data` topic exchange) for normalized sensor and telemetry messages.

* PORTS: 5672, 15672.

* TECHNOLOGICAL SPECIFICATION:
  - RabbitMQ 3 with management plugin (`rabbitmq:3-management`).

* SERVICE ARCHITECTURE:

  - Topic exchange `exchange_data` declared by all connected services (`ingestion_service/app.py`, `automation_engine/engine.py`, `state/state.py`, `report_service/report-generator.py`).
  - Producers publish messages with routing key equal to the normalized sensor topic (e.g., `message["topic"]`).
  - Consumers bind queues to the exchange using:
    - Specific topics from automation rules (`automation-engine`).
    - Wildcard `#` for all topics (`state`).
    - Specific topics registered via `/change_sensor_tracking` (`report-service`).

* ENDPOINTS:

  N/A (AMQP service, not HTTP).

---

## CONTAINER_NAME: rule-database

### DESCRIPTION:

PostgreSQL database storing automation rules, built from `src/database` directory. It holds the `rules` table which is queried and updated by the `presentation-service` and used indirectly by `automation-engine`.

### USER STORIES:

* **As a** system operator
* **I want** the automation rules to be persisted in a database
* **So that** the habitat automation logic is preserved and restored automatically after a system reboot or failure.

### PORTS:

- `5432:5432` (PostgreSQL default port).

### PERSISTENCE EVALUATION

- Uses volume `postgres_data:/var/lib/postgresql/data` mapped in `docker-compose.yml`, providing persistent storage for rules across container restarts.

### EXTERNAL SERVICES CONNECTIONS

- Receives connections from `presentation-service` via `psycopg2-binary` (`db.py` in `presentation_service/server`).
- No outgoing connections defined.

### MICROSERVICES:

#### MICROSERVICE: rules-db (PostgreSQL)

* TYPE: backend

* DESCRIPTION: Stores automation rules in a single `rules` table, populated initially from `schema.sql`.

* PORTS: 5432.

* TECHNOLOGICAL SPECIFICATION:
  - PostgreSQL (version implied by official image, not pinned in `docker-compose.yml`).
  - SQL schema defined in `src/database/schema.sql`.

* SERVICE ARCHITECTURE:

  - Single database `rules_db` (from environment `POSTGRES_DB`).
  - Single table `rules` used for automation rules.
  - `presentation-service` performs CRUD on `rules` via SQL (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).
  - `automation-engine` queries rules indirectly by calling `presentation-service:/get_rule` rather than connecting directly to the DB.

* DB STRUCTURE:

  ***rules*** : | ***id*** | name, sensor_name, operator, threshold_value, unit, actuator_name, actuator_state, enabled, created_at

  - From `schema.sql`:

    - `id SERIAL PRIMARY KEY`
    - `name TEXT`
    - `sensor_name TEXT NOT NULL`
    - `operator TEXT NOT NULL`
    - `threshold_value DOUBLE PRECISION NOT NULL`
    - `unit TEXT`
    - `actuator_name TEXT NOT NULL`
    - `actuator_state TEXT CHECK (actuator_state IN ('ON','OFF')) NOT NULL`
    - `enabled BOOLEAN DEFAULT TRUE`
    - `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

---

## CONTAINER_NAME: ingestion-service

### DESCRIPTION:

Python service that ingests sensor and telemetry data from the `mars-simulator` via REST and SSE, normalizes messages, and publishes them to RabbitMQ (`message-broker`) on exchange `exchange_data`. Built from `src/ingestion_service`.

### USER STORIES:

- Supports real-time monitoring and automation by ensuring sensor and telemetry data flows continuously into the messaging backbone and downstream services.

### PORTS:

- No ports exposed in `docker-compose.yml` (runs as an internal worker).

### PERSISTENCE EVALUATION

- No volumes defined; service is stateless, with no on-disk persistence in this container.

### EXTERNAL SERVICES CONNECTIONS

- Connects to:
  - `mars-simulator` over HTTP/SSE for:
    - REST sensor endpoints `GET_TOPICS` (e.g., `http://mars-simulator:8080/api/sensors/<id>`).
    - Telemetry SSE endpoints `SSE_TOPICS` (e.g., `http://mars-simulator:8080/api/telemetry/stream/mars/telemetry/solar_array`).
  - `message-broker` (RabbitMQ) using `pika`.

### MICROSERVICES:

#### MICROSERVICE: ingestion-service

* TYPE: backend

* DESCRIPTION: Headless ingestion microservice that periodically polls REST endpoints and subscribes to SSE streams from the simulator, normalizes all messages into a unified schema, and publishes them to RabbitMQ.

* PORTS: None exposed.

* TECHNOLOGICAL SPECIFICATION:
  - Language: Python 3.11 (from Dockerfile).
  - Libraries: `requests`, `pika`, `sseclient-py` (from `requirements.txt`).
  - Custom module: `sensor_normalizer.py`.

* SERVICE ARCHITECTURE:

  - On startup (`if __name__ == "__main__":` in `app.py`):
    - Creates a persistent RabbitMQ connection and channel via `create_connection()`, declares `exchange_data` (topic exchange).
    - Starts multiple threads:
      - SSE listener threads (`listen_sse`) per `SSE_TOPICS`.
      - Periodic polling threads (`poll_get`) per `GET_TOPICS`.
  - Each received message is normalized via:
    - `normalize_message(msg)` which infers source type and calls `normalize_sensor_reading`.
    - Attaches `topic` equal to normalized `id`.
  - Publishes normalized messages with routing key `message["topic"]` to exchange `exchange_data` using `send_to_rabbitmq`.

* ENDPOINTS:

  N/A (no HTTP server defined).


---

## CONTAINER_NAME: automation-engine

### DESCRIPTION:

Automation engine that consumes normalized sensor/telemetry messages from RabbitMQ, applies automation rules from the rules database (via `presentation-service`), and issues actuator commands back to the simulator via the presentation backend. Exposes an HTTP API for dynamic rule-topic subscription updates. Built from `src/automation_engine`.

### USER STORIES:

* **As a** habitat operator
* **I want** the system to automatically activate actuators when rule conditions are met
* **So that** environmental conditions are maintained.

### PORTS:

- `6000:6000` (HTTP API endpoint for rule updates).

### PERSISTENCE EVALUATION

- No volumes defined; this service is stateless. Rule and sensor configuration are persisted externally in the `rule-database` and managed through the `presentation-service`.

### EXTERNAL SERVICES CONNECTIONS

- Connects to:
  - `message-broker` (RabbitMQ) via `pika` on host `message-broker`, exchange `exchange_data`.
  - `presentation-service` HTTP API (`http://presentation-service:5050/rules` and `/get_rule`, `/switch_actuator`).
  - `mars-simulator` indirectly via `presentation-service` `/switch_actuator` which posts to simulator.

### MICROSERVICES:

#### MICROSERVICE: automation-engine

* TYPE: backend

* DESCRIPTION: Flask-based automation engine that subscribes to selected RabbitMQ topics, evaluates rules for incoming sensor data, and triggers actuator changes via the presentation backend. It also exposes an HTTP endpoint for updating RabbitMQ bindings when rules change.

* PORTS: 6000.

* TECHNOLOGICAL SPECIFICATION:
  - Language: Python 3.11 (`Dockerfile`).
  - Frameworks/Libraries: `Flask`, `pika`, `requests`, `operator` (standard lib).
  - Queue: RabbitMQ (via `pika`).

* SERVICE ARCHITECTURE:

  - Global configuration: `RABBIT_HOST`, `EXCHANGE_NAME`, `RULES_API_URL`.
  - On startup (`if __name__ == "__main__":` in `engine.py`):
    - Calls `connect_rabbitmq()` to connect to the broker, declare `exchange_data`, declare an exclusive queue, and store `channel`, `connection`, `queue_name`.
    - Calls `sync_rules_on_startup()`:
      - Fetches all rules via `GET http://presentation-service:5050/rules`.
      - Extracts unique `sensor_name` values and binds its queue to `exchange_data` for each topic.
    - Starts RabbitMQ consumer in a background thread (`start_rabbitmq` with `basic_consume` and callback `process_message`).
    - Runs the Flask app on `0.0.0.0:6000`.
  - `process_message`:
    - Parses messages from RabbitMQ, obtains `topic`, logs, then calls `RULES_API_URL` (`/get_rule`) with `{ "sensor_name": topic }`.
    - Iterates over returned rule rows, checks `enabled`, operator, threshold, and compares with each measurement value.
    - Fetches current actuator states from `mars-simulator:/api/actuators` to avoid redundant commands.
    - For triggered rules, posts to `http://presentation-service:5050/switch_actuator` with `{ "actuator": actuator_name, "state": actuator_state, "sender": "engine" }`.
  - The Flask endpoint `/update-rules` is used by the backend to dynamically add/remove queue bindings based on new or removed rules.

* ENDPOINTS:

| HTTP METHOD | URL             | Description                                                                 | User Stories                                       |
| ----------- | --------------- | --------------------------------------------------------------------------- | -------------------------------------------------- |
| POST        | /update-rules   | Updates RabbitMQ topic subscriptions based on `action` (`add`/`remove`) and `topic`. Uses thread-safe callbacks to bind/unbind queue to `exchange_data`. | Dynamic reaction to new/removed rules/topics.      |


* DB STRUCTURE:

  N/A (no direct DB access; uses HTTP API of `presentation-service` instead).

---

## CONTAINER_NAME: presentation-service

### DESCRIPTION:

Flask + Flask-SocketIO backend with a single-page HTML/JS frontend (`index.html`, `static/js/app.js`, `static/css/styles.css`). Provides the Mars Mission Dashboard UI, handles rule management, forwards sensor updates to the browser via WebSockets, proxies actuator commands to the simulator, and coordinates sensor tracking toggles with the report service.

### USER STORIES:

* **As a** habitat operator
* **I want to** see the list of available sensors
* **So that** I can monitor the habitat systems.

* **As a** habitat operator
* **I want to** see the current values of sensors
* **So that** I can monitor environmental conditions.

* **As a** habitat operator
* **I want to** see the unit of measurement of each sensor
* **So that** I can correctly interpret the values.

* **As a** habitat operator
* **I want to** see the list of actuators
* **So that** I know which devices can be controlled.

* **As a** habitat operator
* **I want to** see the current state of an actuator
* **So that** I know whether it is ON or OFF.

* **As a** habitat operator
* **I want to** see the list of automation rules
* **So that** I can review system automation.

* **As a** habitat operator
* **I want to** create new automation rules
* **So that** the system can automatically react to sensor values and interact with the environment.

* **As a** habitat operator
* **I want to** update already existing automation rules
* **So that** the system can respond to new conditions.

* **As a** habitat operator
* **I want to** delete an automation rule
* **So that** I can remove outdated automation.

* **As a** habitat operator
* **I want to** disable and/or enable an automation rule
* **So that** I can handle in real time automation.

* **As a** habitat operator
* **I want to** manually activate or deactivate an actuator
* **So that** I can override automation when necessary.

* **As a** habitat operator
* **I want to** see visual warnings or alerts for REST sensors when they exceed critical thresholds or become unreachable
* **So that** I can quickly identify and react to life-support anomalies.

* **As a** habitat operator
* **I want to** view a terminal or log showing the history of actuator state changes (both manual and rule-triggered)
* **So that** I can trace system actions and audit the automation behavior.

* **As a** system operator
* **I want** the automation rules to be persisted in a database
* **So that** the habitat automation logic is preserved and restored automatically after a system reboot or failure.

* **As a** system operator
* **I want to** see live line charts for telemetry data (e.g., power_bus, radiation)
* **So that** I can analyze immediate trends.

### PORTS:

- `5050:5050`.

### PERSISTENCE EVALUATION

- The service itself is stateless; rule persistence is delegated to `rule-database` (PostgreSQL), and reports are stored by `report-service`. Frontend state is in-browser.

### EXTERNAL SERVICES CONNECTIONS

- PostgreSQL `rule-database` via `psycopg2-binary` (`db.py`).
- `automation-engine` via HTTP POST to `http://automation-engine:6000/update-rules` when rules are added.
- `mars-simulator` via:
  - POST `http://mars-simulator:8080/api/actuators/<actuator>` to change actuator state.
- `report-service` via:
  - POST `http://report-service:3030/change_sensor_tracking` to bind/unbind report-service’s RabbitMQ subscriptions.
- `state` service sends data to `/update_sensor`.
- The browser connects via Socket.IO to receive `sensor_update` and `actuator_switch` events.

### MICROSERVICES:

#### MICROSERVICE: presentation-backend

* TYPE: backend

* DESCRIPTION: Flask + Flask-SocketIO API providing rules CRUD endpoints, sensor/actuator update endpoints, and coordination with automation and reporting services.

* PORTS: 5050.

* TECHNOLOGICAL SPECIFICATION:
  - Language: Python 3.11.
  - Frameworks/Libraries: `Flask`, `Flask-SocketIO`, `eventlet`, `psycopg2-binary`, `pika`, `requests`.
  - Database: PostgreSQL (rules DB via `db.py`).
  - WebSockets: Socket.IO.

* SERVICE ARCHITECTURE:

  - `app = Flask(__name__)`, `socketio = SocketIO(app)`.
  - Database access via `get_connection()` in `db.py`.
  - Endpoints for:
    - Rendering dashboard page.
    - Exposing rules as list.
    - CRUD for rules.
  - Automation integration:
    - On rule add, posts `{ "action": "add", "topic": sensor_name }` to `automation-engine:/update-rules`.
  - Actuator integration:
    - `/switch_actuator` proxies actuator commands to `mars-simulator` and emits Socket.IO `actuator_switch` events for UI updates.
  - Sensor streaming:
    - `/update_sensor` receives `{ "topic": sensor, "measurements": [...] }` and emits `sensor_update` to all connected clients.
  - Reporting integration:
    - `/switch_sensor_state` proxies actions to `report-service:/change_sensor_tracking` with `{ "action": state, "topic": sensor }`.

* ENDPOINTS:

| HTTP METHOD | URL                 | Description                                                                                                                     | User Stories                                                                                     |
| ----------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| GET         | /                   | Renders `index.html`, the main Mars Mission Dashboard UI.                                                                      | US-1 US-2 US-3 US-4 US-5                                                                         |
| GET         | /rules              | Returns all rules from `rules` table via JSON.                                                                                 | US-6                                                                                             |
| POST        | /add_rule           | Inserts a new rule into the `rules` table and posts to `automation-engine:/update-rules` with `action="add"`, `topic=sensor`. | US-7                                                                                             |
| POST        | /update_rule        | Updates an existing rule in the `rules` table.                                                                                 | US-8                                                                                             |
| POST        | /delete_rule        | Deletes a rule by `id` from the `rules` table.                                                                                 | US-9                                                                                             |
| POST        | /get_rule           | Returns all rules for a given `sensor_name` (used by automation engine).                                                       | US-11                                                                                            |
| POST        | /switch_actuator    | Validates `actuator` and `state`, posts JSON `{"state": state}` to `mars-simulator:/api/actuators/<actuator>`, emits Socket.IO event. | US-12                                                                                   |
| POST        | /update_sensor      | Receives new sensor/telemetry measurements and broadcasts them to connected clients via Socket.IO `sensor_update`.             | US-1                                                                                             |
| POST        | /switch_sensor_state| Receives `topic` and `state` (`add`/`remove`), validates, and calls `report-service:/change_sensor_tracking`.                  | US-17       |


* DB STRUCTURE:

Uses the `rules` table defined under `rule-database` (see that container).

---

#### MICROSERVICE: presentation-frontend

* TYPE: frontend

* DESCRIPTION: Browser-based dashboard implemented as static HTML/CSS/JS (`index.html`, `styles.css`, `app.js`) served by the presentation backend. It shows monitoring views, actuator controls, sensor tracking toggles, and automation rule management UI.

* PORTS: Served via `presentation-backend` on port 5050.

* TECHNOLOGICAL SPECIFICATION:
  - Technologies: HTML5, CSS, vanilla JavaScript.
  - Real-time: Socket.IO client from CDN (`https://cdn.socket.io/4.7.2/socket.io.min.js`).
  - No frontend framework (no React/Vue/etc. detected).

* SERVICE ARCHITECTURE:

  - Single HTML entry point `index.html`:
    - Sidebar navigation with buttons:
      - `Monitoring` → `monitoring-section`.
      - `Control` → `control-section`.
      - `Sensors` → `sensors-section`.
      - `Automation` → `automation-section`.
    - Main content sections for monitoring, control, sensors tracking, and automation rules.
  - `static/js/app.js`:
    - Data models for scalar sensors, telemetry streams, actuators.
    - Rendering functions:
      - `renderScalarSensors`, `updateScalarSensorsUI`.
      - `renderTelemetryCards`, `drawTelemetryStream`.
      - `renderActuators`, `updateActuatorsUI`.
      - `renderRules`, `loadRules`.
      - `renderSensorTracking`, `updateSensorTrackingUI`.
    - Socket.IO integration for:
      - `sensor_update` (updates scalar/telemetry UI and radiation pill).
      - `actuator_switch` (updates actuator status and log).
    - Navigation setup via `setupNav()` toggling section visibility based on `.nav-item` buttons.
    - Actuator toggling via `toggleActuator` which POSTs to `/switch_actuator`.
    - Sensor report tracking toggling via `toggleSensorTracking`, which POSTs to `/switch_sensor_state` with `state: "add"` or `"remove"`.
    - Rule modal and table management (`openRuleModal`, `handleRuleFormSubmit`, `handleRuleUpdateClick`, `deleteRule`, `toggleRuleEnabled`).
    - A periodic `mainLoop` calling `applyAutomation()` for local visualization, though core automation is handled by the backend engine.

* ENDPOINTS:

  N/A (frontend client in the browser).

* PAGES:

| Name                | Description                                                                                           | Related Microservice | User Stories                                                                                  |
| ------------------- | ----------------------------------------------------------------------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------- |
| Monitoring section  | Displays scalar environment sensors and telemetry stream cards with live values and charts.          | presentation-backend | US-1                                                     |
| Control section     | Shows actuator cards with ON/OFF status, toggle controls, and an actuator event log terminal.        | presentation-backend | US-12                                |
| Sensors section     | Displays cards for all scalar and telemetry sensors with toggles to enable/disable reporting.        | presentation-backend | US-17                                       |
| Automation section  | Shows automation rule table and modal for creating/editing rules, including enable/disable toggles.  | presentation-backend | US-8 US-9 US-10                    |


---

## CONTAINER_NAME: state

### DESCRIPTION:

Python service that builds a snapshot of available sensors, telemetry topics, and actuators from the simulator, then subscribes to all RabbitMQ topics and forwards messages to the presentation service’s `/update_sensor` endpoint. Built from `src/state`.

### USER STORIES:

- Enables the frontend to display real-time data by ensuring all messages on `exchange_data` are forwarded to the presentation service, which in turn broadcasts via WebSockets.

### PORTS:

- `6001:6001` in `docker-compose.yml`, but the `state.py` main block does not start an HTTP server; this port mapping is unused in the current code.

### PERSISTENCE EVALUATION

- No volumes defined; the state is in-memory (dictionary `STATE`) and lost on restart.

### EXTERNAL SERVICES CONNECTIONS

- Connects to:
  - `mars-simulator` over HTTP for initial discovery of `sensors`, `telemetry` topics, and `actuators`.
  - `message-broker` (RabbitMQ) for consuming all topics.
  - `presentation-service` via HTTP POST to `/update_sensor` for forwarding measurements.

### MICROSERVICES:

#### MICROSERVICE: state-service

* TYPE: backend

* DESCRIPTION: Headless consumer that subscribes to all telemetry/sensor topics from RabbitMQ and forwards them to the presentation backend for frontend WebSocket broadcasting.

* PORTS: None used (though `6001` is mapped in docker-compose, it is not utilized in `state.py`).

* TECHNOLOGICAL SPECIFICATION:
  - Language: Python 3.11.
  - Libraries: `pika`, `requests`, `json`, `time`.

* SERVICE ARCHITECTURE:

  - On startup (`if __name__ == "__main__":` in `state.py`):
    - Waits for simulator readiness and calls:
      - `GET http://mars-simulator:8080/api/sensors`.
      - `GET http://mars-simulator:8080/api/telemetry/topics`.
      - `GET http://mars-simulator:8080/api/actuators`.
    - Builds an initial `STATE` dict with keys for all sensors, telemetry topics, and actuators.
    - Connects to RabbitMQ (`connect_to_rabbitmq`), declares `exchange_data`, declares an exclusive queue, and binds it with routing key `#` (all topics).
    - Starts consuming with `basic_consume` and callback `callback`.
  - `callback`:
    - Parses each message, logs, and POSTs `{ "topic": data['topic'], "measurements": data['measurements'] }` to `http://presentation-service:5050/update_sensor`.

* ENDPOINTS:

  N/A (no HTTP server defined).

---

## CONTAINER_NAME: report-service

### DESCRIPTION:

Python + Flask service that consumes selected sensor messages from RabbitMQ, maintains short in-memory histories, and generates PDF reports with plots and basic statistics when sufficient data is collected. It exposes an HTTP endpoint for changing which topics are tracked and subscribed. Built from `src/report_service`.

### USER STORIES:

* **As a** system operator
* **I want to** export and store the sensor telemetry charts as a PDF file
* **So that** I can archive, share, and review historical telemetry reports outside the system.
* **NFR:** The generated PDF must include clearly labeled charts and timestamps for the selected time range.

### PORTS:

- `3030:3030`.

### PERSISTENCE EVALUATION

- Uses a `reports` volume mapped to `/app/reports` (`./reports:/app/reports` in docker-compose), so generated PDFs are persisted and shared with the host.

### EXTERNAL SERVICES CONNECTIONS

- Connects to:
  - `message-broker` (RabbitMQ) via `pika`, exchange `exchange_data`.
- Receives connections from:
  - `presentation-service` via `/change_sensor_tracking` endpoint URL (`http://report-service:3030/change_sensor_tracking`).

### MICROSERVICES:

#### MICROSERVICE: report-service

* TYPE: backend

* DESCRIPTION: Flask microservice that subscribes to specific sensor topics on RabbitMQ, accumulates recent measurements, and generates PDF reports using Matplotlib when a configurable history length is reached. It exposes an HTTP endpoint for the presentation service to add/remove topics for tracking.

* PORTS: 3030.

* TECHNOLOGICAL SPECIFICATION:
  - Language: Python 3.11.
  - Frameworks/Libraries: `Flask`, `pika`, `matplotlib`, `statistics`, `datetime`, `collections.deque`.
  - Output format: PDF files stored under `/app/reports/<topic>/`.

* SERVICE ARCHITECTURE:

  - On startup (`if __name__ == "__main__":` in `report-generator.py`):
    - Connects to RabbitMQ (`connect_rabbitmq`), declares `exchange_data`, declares an exclusive queue, and stores `channel`, `connection`, `queue_name`.
    - Starts `start_rabbitmq()` in a background thread to `basic_consume` with callback `process_message`.
    - Runs the Flask app on `0.0.0.0:3030`.
  - `sensor_data_history`: dict mapping topics to bounded `deque` (`MAX_HISTORY` elements).
  - `process_message`:
    - Parses payload, looks up `topic` in `sensor_data_history`; if not tracked, returns.
    - Extracts first measurement’s `metric`, `value`, and `captured_at` timestamp.
    - Appends a record to the deque and, if history length reaches `MAX_HISTORY`, spawns a thread (`pdf_worker`) to call `generate_pdf_report` and resets the deque.
  - `generate_pdf_report`:
    - Builds time-series plots and calculates mean/variance, then saves PDF per `topic` into `PDF_OUTPUT_DIR` under a timestamped filename.
  - Flask endpoint `/change_sensor_tracking` allows external services to add/remove topics from tracking and to bind/unbind the RabbitMQ queue for those topics.

* ENDPOINTS:

| HTTP METHOD | URL                  | Description                                                                                                     | User Stories                                                   |
| ----------- | -------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| POST        | /change_sensor_tracking | Accepts JSON `{ "action": "add" or "remove", "topic": "<topic>" }`. On `add`, creates history deque and binds queue to topic; on `remove`, clears history and unbinds. | US-17 |

* DB STRUCTURE:

  N/A (uses file system and in-memory structures, not a DB).

---

