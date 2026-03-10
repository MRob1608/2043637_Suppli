# Mars Habitat - Automation Platform
**Project Acronym:** Supplì
**Group Members:** Gandolfi Alessia, Iacomi Gabriel, Robotti Marcello

## 1. System Overview
The system is a distributed automation platform designed for a Mars habitat. 
It is capable of ingesting heterogeneous sensor data from both REST-based devices (polling) and publish-based devices (asynchronous telemetry streams). The architecture utilizes an event-driven approach via a message broker to normalize incoming payloads into a unified internal format. 

The platform features an automation engine that evaluates simple, dynamically triggered event rules to control actuators, alongside a real-time web dashboard for system monitoring and manual control.

## 2. Standard Event Schema
To handle the incompatible dialects of the habitat's devices, all incoming data is normalized into a standard internal event format before being published to the internal message broker.

**JSON Schema Example:**
```json
{
  "id": "string",
  "source": "rest | telemetry",
  "captured_at": "ISO_8601_timestamp",
  "status": "ok | warning",
  "measurements": [
    {
      "metric": "string",
      "value": "number",
      "unit": "string"
    }
  ],
  "metadata": {},
  "topic": "string"
}
```
## 3. Rule Model
The automation engine supports simple IF-THEN rules that are dynamically evaluated upon the arrival of new normalized events. Rules are persisted in a database to survive service restarts.

**Logical Structure:**

IF <sensor_name> <operator> <value> THEN set <actuator_name> to <ON|OFF>

## 4. User Stories

### ---- DASHBOARD AND MONITORING ----

#### US-01 – View sensors
* **As a** habitat operator
* **I want to** see the list of available sensors
* **So that** I can monitor the habitat systems.
* **Mockup:** ![Mockup US-01](/booklets/dashboard.png)

#### US-02 – View sensors values
* **As a** habitat operator
* **I want to** see the current values of sensors
* **So that** I can monitor environmental conditions.
* **Mockup:** ![Mockup US-02](/booklets/dashboard.png)

#### US-03 – View sensors measure units
* **As a** habitat operator
* **I want to** see the unit of measurement of each sensor
* **So that** I can correctly interpret the values.
* **Mockup:** ![Mockup US-03](/booklets/dashboard.png)

#### US-04 – View actuators
* **As a** habitat operator
* **I want to** see the list of actuators
* **So that** I know which devices can be controlled.
* **Mockup:** ![Mockup US-04](/booklets/actuators.png)

#### US-05 – View actuator state
* **As a** habitat operator
* **I want to** see the current state of an actuator
* **So that** I know whether it is ON or OFF.
* **Mockup:** ![Mockup US-05](/booklets/actuators.png)

#### US-06 – View system rules
* **As a** habitat operator
* **I want to** see the list of automation rules
* **So that** I can review system automation.
* **Mockup:** ![Mockup US-06](/booklets/rules.png)

### ---- RULE MANAGEMENT ----

#### US-07 – Create new rule
* **As a** habitat operator
* **I want to** create new automation rules
* **So that** the system can automatically react to sensor values and interact with the environment.
* **Mockup:** ![Mockup US-07](/booklets/rules.png)

#### US-08 – Update rule
* **As a** habitat operator
* **I want to** update already existing automation rules
* **So that** the system can respond to new conditions.
* **Mockup:** ![Mockup US-08](/booklets/rules.png)

#### US-09 – Delete rule
* **As a** habitat operator
* **I want to** delete an automation rule
* **So that** I can remove outdated automation.
* **Mockup:** ![Mockup US-09](/booklets/rules.png)

#### US-10 – Disable and/or enable rule
* **As a** habitat operator
* **I want to** disable and/or enable an automation rule
* **So that** I can handle in real time automation.
* **Mockup:** ![Mockup US-10](/booklets/rules.png)

### ---- ACTUATOR MANAGEMENT ----

#### US-11 - Automated Actuator control
* **As a** habitat operator
* **I want** the system to automatically activate actuators when rule conditions are met
* **So that** environmental conditions are maintained.
* **NFR - Reliability** The automation engine must verify the current state of an actuator before sending a command to prevent redundant messages
* **Mockup:** ![Mockup US-11](/booklets/actuators.png)

#### US-12 – Manual Actuator control
* **As a** habitat operator
* **I want to** manually activate or deactivate an actuator
* **So that** I can override automation when necessary.
* **Mockup:** ![Mockup US-12](/booklets/actuators.png)

### ---- SYSTEM ALERTS, LOGS AND TELEMETRY ----

#### US-13 – View sensor warnings
* **As a** habitat operator
* **I want to** see visual warnings or alerts for REST sensors when they exceed critical thresholds or become unreachable
* **So that** I can quickly identify and react to life-support anomalies.
* **Mockup:** ![Mockup US-13](/booklets/dashboard.png)

#### US-14 – View actuator activation history
* **As a** habitat operator
* **I want to** view a terminal or log showing the history of actuator state changes (both manual and rule-triggered)
* **So that** I can trace system actions and audit the automation behavior.
* **Mockup:** ![Mockup US-14](/booklets/actuators.png)

#### US-15 – Persist automation rules
* **As a** system operator
* **I want** the automation rules to be persisted in a database
* **So that** the habitat automation logic is preserved and restored automatically after a system reboot.

#### US-16 – View real-time telemetry trends
* **As a** system operator
* **I want to** see live line charts for telemetry data (e.g., power_bus, radiation)
* **So that** I can analyze immediate trends.
* **NFR:** Real-time updates must be handled with low latency via WebSocket or SSE.
* **Mockup:** ![Mockup US-16](/booklets/dashboard.png)

#### US-17 – Export sensor charts to PDF
* **As a** system operator
* **I want to** export and store the sensor telemetry charts as a PDF file
* **So that** I can archive, share, and review historical telemetry reports outside the system.
* **NFR:** The generated PDF must include clearly labeled charts and timestamps for the selected time range.
* **NFR - Resource Management** To prevent memory leaks, the report must cap the in-memory history and use background threads for rendering
* **Mockup:** ![Mockup US-17](/booklets/reporting.png)
