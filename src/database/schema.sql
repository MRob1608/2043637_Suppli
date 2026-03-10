CREATE TABLE IF NOT EXISTS rules (
    id SERIAL PRIMARY KEY,
    name TEXT,
    sensor_name TEXT NOT NULL,
    operator TEXT NOT NULL,
    threshold_value DOUBLE PRECISION NOT NULL,
    unit TEXT,
    actuator_name TEXT NOT NULL,
    actuator_state TEXT CHECK (actuator_state IN ('ON','OFF')) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO rules 
(name, sensor_name, operator, threshold_value, unit, actuator_name, actuator_state,enabled)
VALUES

-- REST sensors
('High greenhouse temp','greenhouse_temperature', '>', 30, 'C', 'cooling_fan', 'ON', true),

('High entrance humidity','entrance_humidity', '>=', 75, '%', 'entrance_humidifier', 'ON', true),

('Almost empty water tank','water_tank_level', '<=', 20, '%', 'entrance_humidifier', 'OFF', true),

-- TELEMETRY sensors
('High radiation','radiation', '>', 50, 'mSv', 'habitat_heater', 'OFF', true),

('Low power bus','power_bus', '<', 40, 'V', 'cooling_fan', 'OFF', true),

('High termal loop temp','co2_hall', '>=', 1150, 'ppm', 'hall_ventilation', 'ON', true);