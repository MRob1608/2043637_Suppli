CREATE TABLE IF NOT EXISTS rules (
    id SERIAL PRIMARY KEY,
    sensor_name TEXT NOT NULL,
    operator TEXT NOT NULL,
    threshold_value DOUBLE PRECISION NOT NULL,
    unit TEXT,
    actuator_name TEXT NOT NULL,
    actuator_state TEXT CHECK (actuator_state IN ('ON','OFF')) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
