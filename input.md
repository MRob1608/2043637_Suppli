{
  "schema": "normalized.telemetry.v1",
  "event_id": "string",
  "topic": "string",
  "timestamp": "date-time",
  "source": {
    "type": "sensor | telemetry",
    "id": "string",
    "location": "string"
  },
  "measurements": [
    {
      "metric": "string",
      "value": "number",
      "unit": "string"
    }
  ],
  "status": "ok | warning"
}
