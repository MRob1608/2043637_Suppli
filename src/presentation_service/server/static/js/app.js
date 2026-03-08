// Basic data models

const scalarSensors = [
  {
    id: "greenhouse_temperature",
    label: "Greenhouse Temp",
    unit: "°C",
    icon: "🌱",
    min: 16,
    max: 32,
    warningLow: 18,
    warningHigh: 28,
    criticalLow: 15,
    criticalHigh: 32,
    value: 24,
  },
  {
    id: "entrance_humidity",
    label: "Entrance Humidity",
    unit: "%",
    icon: "💧",
    min: 10,
    max: 90,
    warningLow: 25,
    warningHigh: 70,
    criticalLow: 10,
    criticalHigh: 90,
    value: 40,
  },
  {
    id: "co2_hall",
    label: "Hall CO₂",
    unit: "ppm",
    icon: "🧪",
    min: 300,
    max: 4000,
    warningLow: 400,
    warningHigh: 1200,
    criticalLow: 300,
    criticalHigh: 4000,
    value: 600,
  },
  {
    id: "hydroponic_ph",
    label: "Hydroponic pH",
    unit: "pH",
    icon: "🌊",
    min: 4.0,
    max: 9.0,
    warningLow: 5.5,
    warningHigh: 7.0,
    criticalLow: 4.5,
    criticalHigh: 8.0,
    value: 6.2,
  },
  {
    id: "water_tank_level",
    label: "Water Tank Level",
    unit: "%",
    icon: "🚰",
    min: 0,
    max: 100,
    warningLow: 30,
    warningHigh: 95,
    criticalLow: 10,
    criticalHigh: 100,
    value: 72,
  },
  {
    id: "corridor_pressure",
    label: "Corridor Pressure",
    unit: "kPa",
    icon: "🛡️",
    min: 85,
    max: 110,
    warningLow: 92,
    warningHigh: 104,
    criticalLow: 88,
    criticalHigh: 108,
    value: 98,
  },
  {
    id: "air_quality_pm25",
    label: "PM2.5",
    unit: "µg/m³",
    icon: "🌫️",
    min: 0,
    max: 200,
    warningLow: 0,
    warningHigh: 55,
    criticalLow: 0,
    criticalHigh: 150,
    value: 15,
  },
  {
    id: "air_quality_voc",
    label: "VOC",
    unit: "ppb",
    icon: "☣️",
    min: 0,
    max: 2000,
    warningLow: 0,
    warningHigh: 600,
    criticalLow: 0,
    criticalHigh: 1200,
    value: 220,
  },
];

const telemetryStreams = [
  {
    id: "solar_array",
    topic: "mars/telemetry/solar_array",
    label: "Solar Array Output",
    unit: "kW",
    color: "#47c3ff",
    min: 0,
    max: 40,
  },
  {
    id: "radiation",
    topic: "mars/telemetry/radiation",
    label: "Radiation",
    unit: "µSv/h",
    color: "#ff4b6e",
    min: 0,
    max: 800,
  },
  {
    id: "life_support",
    topic: "mars/telemetry/life_support",
    label: "Life Support Load",
    unit: "%",
    color: "#5ff7b0",
    min: 0,
    max: 100,
  },
  {
    id: "thermal_loop",
    topic: "mars/telemetry/thermal_loop",
    label: "Thermal Loop ΔT",
    unit: "K",
    color: "#e27b58",
    min: 0,
    max: 40,
  },
  {
    id: "power_bus",
    topic: "mars/telemetry/power_bus",
    label: "Power Bus",
    unit: "kW",
    color: "#b987ff",
    min: 0,
    max: 60,
  },
  {
    id: "power_consumption",
    topic: "mars/telemetry/power_consumption",
    label: "Power Consumption",
    unit: "kW",
    color: "#ffd86b",
    min: 0,
    max: 50,
  },
  {
    id: "airlock",
    topic: "mars/telemetry/airlock",
    label: "Airlock Cycle",
    unit: "",
    color: "#5ff7b0",
    min: 0,
    max: 1,
  },
];

const actuators = [
  {
    id: "cooling_fan",
    label: "Cooling Fan",
    icon: "🌀",
    status: "off",
    mode: "auto",
    lastChangedAt: null,
  },
  {
    id: "habitat_heater",
    label: "Habitat Heater",
    icon: "🔥",
    status: "on",
    mode: "auto",
    lastChangedAt: null,
  },
  {
    id: "co2_scrubber",
    label: "CO₂ Scrubber",
    icon: "🧽",
    status: "on",
    mode: "auto",
    lastChangedAt: null,
  },
  {
    id: "hydroponic_pump",
    label: "Hydroponic Pump",
    icon: "💧",
    status: "on",
    mode: "auto",
    lastChangedAt: null,
  },
  {
    id: "airlock_inner",
    label: "Airlock Inner Seal",
    icon: "🚪",
    status: "on",
    mode: "manual",
    lastChangedAt: null,
  },
  {
    id: "airlock_outer",
    label: "Airlock Outer Seal",
    icon: "🛰️",
    status: "off",
    mode: "manual",
    lastChangedAt: null,
  },
];

let rules = [
  {
    id: "rule1",
    name: "Cool greenhouse if hot",
    sensorId: "greenhouse_temperature",
    operator: ">",
    threshold: 27,
    actuatorId: "cooling_fan",
    actuatorState: "on",
    enabled: true,
    priority: 1,
  },
  {
    id: "rule2",
    name: "Reduce CO₂",
    sensorId: "co2_hall",
    operator: ">",
    threshold: 1200,
    actuatorId: "co2_scrubber",
    actuatorState: "on",
    enabled: true,
    priority: 2,
  },
  {
    id: "rule3",
    name: "Secure airlock on radiation spike",
    sensorId: "air_quality_voc",
    operator: ">",
    threshold: 1000,
    actuatorId: "airlock_outer",
    actuatorState: "off",
    enabled: false,
    priority: 3,
  },
];

// State for telemetry drawing
const telemetryState = {};

// Utilities

function randomJitter(value, span, clampMin, clampMax) {
  const delta = (Math.random() - 0.5) * span;
  let next = value + delta;
  if (next < clampMin) next = clampMin;
  if (next > clampMax) next = clampMax;
  return next;
}

function formatValue(value, decimals = 1) {
  if (value == null || Number.isNaN(value)) return "–";
  if (Number.isInteger(value)) return String(value);
  return value.toFixed(decimals);
}

function evaluateStatus(sensor) {
  const v = sensor.value;
  if (v <= sensor.criticalLow || v >= sensor.criticalHigh) return "critical";
  if (v <= sensor.warningLow || v >= sensor.warningHigh) return "warning";
  return "ok";
}

function formatTime(date) {
  return date.toISOString().substring(11, 19);
}

// DOM rendering

function renderScalarSensors() {
  const grid = document.getElementById("scalar-sensors-grid");
  grid.innerHTML = "";

  for (const sensor of scalarSensors) {
    const card = document.createElement("div");
    card.className = "scalar-card";
    card.dataset.sensorId = sensor.id;

    const header = document.createElement("div");
    header.className = "scalar-header";

    const title = document.createElement("div");
    title.className = "scalar-title";

    const iconEl = document.createElement("div");
    iconEl.className = "scalar-icon";
    iconEl.textContent = sensor.icon;

    const labelWrap = document.createElement("div");
    const label = document.createElement("div");
    label.className = "scalar-label";
    label.textContent = sensor.label;
    const unit = document.createElement("div");
    unit.className = "scalar-unit";
    unit.textContent = sensor.unit;
    labelWrap.appendChild(label);
    labelWrap.appendChild(unit);

    title.appendChild(iconEl);
    title.appendChild(labelWrap);

    const status = document.createElement("div");
    status.className = "scalar-status";
    status.dataset.role = "status";

    header.appendChild(title);
    header.appendChild(status);

    const valueRow = document.createElement("div");
    valueRow.className = "scalar-value-row";

    const valueEl = document.createElement("div");
    valueEl.className = "scalar-value";
    valueEl.dataset.role = "value";

    const unitMain = document.createElement("div");
    unitMain.className = "scalar-unit-main";
    unitMain.textContent = sensor.unit;

    valueRow.appendChild(valueEl);
    valueRow.appendChild(unitMain);

    const meta = document.createElement("div");
    meta.className = "scalar-meta";
    meta.innerHTML = `<span>MIN ${sensor.min}${sensor.unit}</span><span>MAX ${sensor.max}${sensor.unit}</span>`;

    card.appendChild(header);
    card.appendChild(valueRow);
    card.appendChild(meta);
    grid.appendChild(card);
  }

  updateScalarSensorsUI();
}

function updateScalarSensorsUI() {
  for (const sensor of scalarSensors) {
    const card = document.querySelector(`.scalar-card[data-sensor-id="${sensor.id}"]`);
    if (!card) continue;
    const valueEl = card.querySelector('[data-role="value"]');
    const statusEl = card.querySelector('[data-role="status"]');
    if (!valueEl || !statusEl) continue;

    valueEl.textContent = formatValue(sensor.value, sensor.unit === "ppm" ? 0 : 1);
    const status = evaluateStatus(sensor);
    statusEl.classList.remove("ok", "warning", "critical");
    statusEl.classList.add(status);
    statusEl.textContent = status.toUpperCase();
  }
}

function renderTelemetryCards() {
  const grid = document.getElementById("telemetry-grid");
  grid.innerHTML = "";

  for (const stream of telemetryStreams) {
    const card = document.createElement("div");
    card.className = "telemetry-card";
    card.dataset.streamId = stream.id;

    const header = document.createElement("div");
    header.className = "telemetry-header";

    const title = document.createElement("div");
    title.className = "telemetry-title";
    title.textContent = stream.label;

    const right = document.createElement("div");
    right.style.textAlign = "right";

    const current = document.createElement("div");
    current.className = "telemetry-current";
    current.dataset.role = "telemetry-value";
    current.textContent = "–";

    const topic = document.createElement("div");
    topic.className = "telemetry-topic";
    topic.textContent = stream.topic;

    const unit = document.createElement("div");
    unit.className = "telemetry-unit";
    unit.textContent = stream.unit;

    right.appendChild(current);
    right.appendChild(topic);
    right.appendChild(unit);

    header.appendChild(title);
    header.appendChild(right);

    const wrapper = document.createElement("div");
    wrapper.className = "telemetry-canvas-wrapper";

    const canvas = document.createElement("canvas");
    canvas.className = "telemetry-canvas";
    canvas.width = 320;
    canvas.height = 80;
    wrapper.appendChild(canvas);

    card.appendChild(header);
    card.appendChild(wrapper);
    grid.appendChild(card);

    telemetryState[stream.id] = {
      canvas,
      ctx: canvas.getContext("2d"),
      points: [],
      maxPoints: 60,
      lastValue: (stream.min + stream.max) / 2,
    };
  }
}

function renderActuators() {
  const grid = document.getElementById("actuator-grid");
  grid.innerHTML = "";

  for (const actuator of actuators) {
    const card = document.createElement("div");
    card.className = "actuator-card";
    card.dataset.actuatorId = actuator.id;

    const header = document.createElement("div");
    header.className = "actuator-header";

    const title = document.createElement("div");
    title.className = "actuator-title";

    const icon = document.createElement("div");
    icon.className = "actuator-icon";
    icon.textContent = actuator.icon;

    const labelWrap = document.createElement("div");
    const label = document.createElement("div");
    label.className = "actuator-label";
    label.textContent = actuator.label;
    labelWrap.appendChild(label);

    title.appendChild(icon);
    title.appendChild(labelWrap);

    const mode = document.createElement("div");
    mode.className = "actuator-mode " + actuator.mode;
    mode.textContent = actuator.mode.toUpperCase();

    header.appendChild(title);
    header.appendChild(mode);

    const statusRow = document.createElement("div");
    statusRow.className = "actuator-status-row";

    const statusIndicator = document.createElement("div");
    statusIndicator.className = "actuator-status-indicator";

    const led = document.createElement("div");
    led.className = "actuator-led off";
    led.dataset.role = "led";

    const stateText = document.createElement("div");
    stateText.className = "actuator-state-text";
    stateText.dataset.role = "state-text";

    statusIndicator.appendChild(led);
    statusIndicator.appendChild(stateText);

    const toggle = document.createElement("div");
    toggle.className = "actuator-toggle";
    toggle.dataset.role = "toggle";

    const knob = document.createElement("div");
    knob.className = "actuator-knob";
    toggle.appendChild(knob);

    statusRow.appendChild(statusIndicator);
    statusRow.appendChild(toggle);

    const meta = document.createElement("div");
    meta.className = "actuator-meta";
    meta.dataset.role = "meta";

    card.appendChild(header);
    card.appendChild(statusRow);
    card.appendChild(meta);

    card.addEventListener("click", (event) => {
      // Allow clicking anywhere on card to toggle, except rule actions if needed
      event.stopPropagation();
      toggleActuator(actuator.id);
    });

    grid.appendChild(card);
  }

  updateActuatorsUI();
}

function updateActuatorsUI() {
  for (const actuator of actuators) {
    const card = document.querySelector(
      `.actuator-card[data-actuator-id="${actuator.id}"]`
    );
    if (!card) continue;

    const led = card.querySelector('[data-role="led"]');
    const stateText = card.querySelector('[data-role="state-text"]');
    const toggle = card.querySelector('[data-role="toggle"]');
    const meta = card.querySelector('[data-role="meta"]');

    if (led && stateText && toggle && meta) {
      led.classList.toggle("on", actuator.status === "on");
      led.classList.toggle("off", actuator.status !== "on");

      toggle.classList.toggle("on", actuator.status === "on");

      stateText.textContent = actuator.status === "on" ? "ONLINE" : "OFFLINE";

      meta.textContent = actuator.lastChangedAt
        ? `Last change ${actuator.lastChangedAt}`
        : "Awaiting first command";
    }
  }
}

function renderRules() {
  const tbody = document.getElementById("rules-tbody");
  tbody.innerHTML = "";

  const sensorMap = new Map(scalarSensors.map((s) => [s.id, s]));
  const actuatorMap = new Map(actuators.map((a) => [a.id, a]));

  const sortedRules = [...rules].sort((a, b) => a.priority - b.priority);

  for (const rule of sortedRules) {
    const tr = document.createElement("tr");
    tr.className = "rules-row";
    if (!rule.enabled) tr.classList.add("disabled");
    tr.dataset.ruleId = rule.id;

    const sensor = sensorMap.get(rule.sensorId);
    const actuator = actuatorMap.get(rule.actuatorId);

    const condText = sensor
      ? `IF ${rule.sensorId} ${rule.operator} ${rule.threshold}${sensor.unit}`
      : `IF ${rule.sensorId} ${rule.operator} ${rule.threshold}`;
    const actionText = actuator
      ? `THEN ${rule.actuatorId} -> ${rule.actuatorState.toUpperCase()}`
      : `THEN ${rule.actuatorId} -> ${rule.actuatorState.toUpperCase()}`;

    const enabledTd = document.createElement("td");
    const toggle = document.createElement("div");
    toggle.className = "rule-toggle" + (rule.enabled ? " enabled" : "");
    toggle.dataset.role = "rule-toggle";
    const knob = document.createElement("div");
    knob.className = "rule-toggle-knob";
    toggle.appendChild(knob);
    enabledTd.appendChild(toggle);

    const nameTd = document.createElement("td");
    nameTd.textContent = rule.name;

    const condTd = document.createElement("td");
    condTd.className = "rule-condition";
    condTd.textContent = condText;

    const actionTd = document.createElement("td");
    actionTd.className = "rule-action";
    actionTd.textContent = actionText;

    const priorityTd = document.createElement("td");
    const priority = document.createElement("div");
    priority.className = "rule-priority" + (rule.priority <= 1 ? " rule-priority--high" : "");
    const dot = document.createElement("span");
    const text = document.createElement("span");
    text.textContent = `P${rule.priority}`;
    priority.appendChild(dot);
    priority.appendChild(text);
    priorityTd.appendChild(priority);

    const actionsTd = document.createElement("td");
    actionsTd.className = "rule-actions";
    const editBtn = document.createElement("button");
    editBtn.className = "icon-btn";
    editBtn.innerHTML = "✎";
    editBtn.title = "Edit rule";
    editBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      openRuleModal(rule.id);
    });
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "icon-btn";
    deleteBtn.innerHTML = "✕";
    deleteBtn.title = "Delete rule";
    deleteBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteRule(rule.id);
    });
    actionsTd.appendChild(editBtn);
    actionsTd.appendChild(deleteBtn);

    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleRuleEnabled(rule.id);
    });

    tr.appendChild(enabledTd);
    tr.appendChild(nameTd);
    tr.appendChild(condTd);
    tr.appendChild(actionTd);
    tr.appendChild(priorityTd);
    tr.appendChild(actionsTd);

    tbody.appendChild(tr);
  }
}

// Telemetry update & drawing

function updateTelemetry() {
  for (const stream of telemetryStreams) {
    const state = telemetryState[stream.id];
    if (!state || !state.ctx) continue;

    // generate pseudo-random but smooth series
    let base;
    if (stream.id === "solar_array") {
      const now = new Date();
      const hour = now.getUTCHours();
      const dayFactor = Math.max(0, Math.sin(((hour - 6) / 12) * Math.PI)); // 0 at "night"
      base = (stream.max - stream.min) * dayFactor * 0.9;
    } else if (stream.id === "radiation") {
      base = (stream.min + stream.max) / 2;
      if (Math.random() < 0.02) {
        base = stream.max * 0.9;
      }
    } else {
      base = (stream.min + stream.max) / 2;
    }

    const jitterSpan = (stream.max - stream.min) * 0.12;
    const next = randomJitter(base, jitterSpan, stream.min, stream.max);
    state.lastValue = next;
    state.points.push(next);
    if (state.points.length > state.maxPoints) {
      state.points.shift();
    }

    drawTelemetryStream(stream, state);

    const card = document.querySelector(
      `.telemetry-card[data-stream-id="${stream.id}"]`
    );
    if (card) {
      const valueEl = card.querySelector('[data-role="telemetry-value"]');
      if (valueEl) {
        valueEl.textContent = `${formatValue(
          next,
          stream.unit && stream.unit.includes("ppm") ? 0 : 1
        )} ${stream.unit}`;
      }
    }
  }

  updateRadiationPill();
}

function drawTelemetryStream(stream, state) {
  const { canvas, ctx, points } = state;
  if (!canvas || !ctx || points.length === 0) return;

  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  // background grid
  ctx.save();
  ctx.strokeStyle = "rgba(255,255,255,0.06)";
  ctx.lineWidth = 1;
  ctx.setLineDash([3, 6]);
  const rows = 3;
  for (let i = 1; i <= rows; i += 1) {
    const y = (h / (rows + 1)) * i;
    ctx.beginPath();
    ctx.moveTo(0, y + 0.5);
    ctx.lineTo(w, y + 0.5);
    ctx.stroke();
  }
  ctx.restore();

  const min = stream.min;
  const max = stream.max;
  const span = max - min || 1;

  const count = points.length;
  const stepX = w / Math.max(1, state.maxPoints - 1);

  ctx.beginPath();
  ctx.lineWidth = 1.6;
  ctx.strokeStyle = stream.color;

  points.forEach((value, index) => {
    const x = index * stepX;
    const normalized = (value - min) / span;
    const y = h - normalized * h;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });

  ctx.stroke();

  // glow
  ctx.save();
  ctx.shadowColor = stream.color;
  ctx.shadowBlur = 12;
  ctx.lineWidth = 0.5;
  ctx.stroke();
  ctx.restore();
}

function updateRadiationPill() {
  const stream = telemetryStreams.find((t) => t.id === "radiation");
  if (!stream) return;
  const state = telemetryState[stream.id];
  if (!state) return;
  const value = state.lastValue ?? (stream.min + stream.max) / 2;

  const pill = document.getElementById("radiation-pill");
  if (!pill) return;

  let label = "RAD: LOW";
  if (value > 600) label = "RAD: CRITICAL";
  else if (value > 250) label = "RAD: ELEVATED";

  pill.textContent = label;
}

// Actuator logic

function toggleActuator(actuatorId) {
  const actuator = actuators.find((a) => a.id === actuatorId);
  if (!actuator) return;
  actuator.status = actuator.status === "on" ? "off" : "on";
  actuator.lastChangedAt = formatTime(new Date());
  updateActuatorsUI();
}

function applyAutomation() {
  const sensorMap = new Map(scalarSensors.map((s) => [s.id, s]));
  const sortedRules = rules
    .filter((r) => r.enabled)
    .sort((a, b) => a.priority - b.priority);

  for (const rule of sortedRules) {
    const sensor = sensorMap.get(rule.sensorId);
    if (!sensor) continue;
    if (!evaluateRuleCondition(rule, sensor.value)) continue;

    const actuator = actuators.find((a) => a.id === rule.actuatorId);
    if (!actuator) continue;
    const desired = rule.actuatorState === "on" ? "on" : "off";
    if (actuator.status !== desired && actuator.mode === "auto") {
      actuator.status = desired;
      actuator.lastChangedAt = `${formatTime(new Date())} via ${rule.name}`;
    }
  }

  updateActuatorsUI();
}

function evaluateRuleCondition(rule, value) {
  if (value == null) return false;
  const t = rule.threshold;
  switch (rule.operator) {
    case ">":
      return value > t;
    case ">=":
      return value >= t;
    case "<":
      return value < t;
    case "<=":
      return value <= t;
    case "==":
      return value === t;
    case "!=":
      return value !== t;
    default:
      return false;
  }
}

// Rules management

function toggleRuleEnabled(ruleId) {
  const rule = rules.find((r) => r.id === ruleId);
  if (!rule) return;
  rule.enabled = !rule.enabled;
  renderRules();
}

function deleteRule(ruleId) {
  rules = rules.filter((r) => r.id !== ruleId);
  renderRules();
}

function openRuleModal(ruleId) {
  const modal = document.getElementById("rule-modal");
  const title = document.getElementById("rule-modal-title");
  const nameInput = document.getElementById("rule-name");
  const sensorSelect = document.getElementById("rule-sensor");
  const operatorSelect = document.getElementById("rule-operator");
  const thresholdInput = document.getElementById("rule-threshold");
  const actuatorSelect = document.getElementById("rule-actuator");
  const actuatorStateSelect = document.getElementById("rule-actuator-state");
  const priorityInput = document.getElementById("rule-priority");
  const enabledCheckbox = document.getElementById("rule-enabled");

  modal.dataset.editingRuleId = ruleId || "";

  if (ruleId) {
    const rule = rules.find((r) => r.id === ruleId);
    if (!rule) return;
    title.textContent = "Edit automation rule";
    nameInput.value = rule.name;
    sensorSelect.value = rule.sensorId;
    operatorSelect.value = rule.operator;
    thresholdInput.value = rule.threshold;
    actuatorSelect.value = rule.actuatorId;
    actuatorStateSelect.value = rule.actuatorState;
    priorityInput.value = rule.priority;
    enabledCheckbox.checked = rule.enabled;
  } else {
    title.textContent = "New automation rule";
    nameInput.value = "";
    sensorSelect.selectedIndex = 0;
    operatorSelect.value = ">";
    thresholdInput.value = "";
    actuatorSelect.selectedIndex = 0;
    actuatorStateSelect.value = "on";
    priorityInput.value = 3;
    enabledCheckbox.checked = true;
  }

  modal.classList.remove("hidden");
}

function closeRuleModal() {
  const modal = document.getElementById("rule-modal");
  modal.classList.add("hidden");
}

function handleRuleFormSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const modal = document.getElementById("rule-modal");
  const editingId = modal.dataset.editingRuleId || null;

  const formData = new FormData(form);
  const name = formData.get("name").trim();
  const sensorId = formData.get("sensorId");
  const operator = formData.get("operator");
  const threshold = Number(formData.get("threshold"));
  const actuatorId = formData.get("actuatorId");
  const actuatorState = formData.get("actuatorState");
  const priority = Number(formData.get("priority") || 3);
  const enabled = document.getElementById("rule-enabled").checked;

  if (!name || !sensorId || !actuatorId || !Number.isFinite(threshold)) {
    return;
  }

  if (editingId) {
    const rule = rules.find((r) => r.id === editingId);
    if (!rule) return;
    rule.name = name;
    rule.sensorId = sensorId;
    rule.operator = operator;
    rule.threshold = threshold;
    rule.actuatorId = actuatorId;
    rule.actuatorState = actuatorState;
    rule.priority = priority;
    rule.enabled = enabled;
  } else {
    const id = `rule_${Date.now().toString(36)}_${Math.random()
      .toString(36)
      .slice(2, 6)}`;
    rules.push({
      id,
      name,
      sensorId,
      operator,
      threshold,
      actuatorId,
      actuatorState,
      enabled,
      priority: priority || 3,
    });
  }

  renderRules();
  closeRuleModal();
}

// Navigation

function setupNav() {
  const buttons = document.querySelectorAll(".nav-item");
  const sections = {
    "monitoring-section": document.getElementById("monitoring-section"),
    "control-section": document.getElementById("control-section"),
    "automation-section": document.getElementById("automation-section"),
  };

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const targetId = btn.dataset.target;
      Object.entries(sections).forEach(([id, el]) => {
        if (!el) return;
        el.style.display = id === targetId ? "block" : "none";
      });
    });
  });

  // initial
  sections["monitoring-section"].style.display = "block";
  sections["control-section"].style.display = "block";
  sections["automation-section"].style.display = "block";
}

// Time & connection indicators

function startMissionClock() {
  const timeEl = document.getElementById("mission-time");
  const solEl = document.getElementById("mission-sol");

  let sol = 173;

  setInterval(() => {
    const now = new Date();
    timeEl.textContent = formatTime(now);
    // very rough: advance sol every few minutes in demo
    if (now.getUTCMinutes() === 0 && now.getUTCSeconds() === 0) {
      sol += 1;
      solEl.textContent = String(sol).padStart(4, "0");
    }
  }, 1000);
}

function simulateConnectionIndicator() {
  const dot = document.getElementById("connection-dot");
  if (!dot) return;
  setInterval(() => {
    dot.style.opacity = dot.style.opacity === "0.4" ? "1" : "0.4";
  }, 1200);
}

// Sensor updates + automation loop

function updateSensors() {
  for (const sensor of scalarSensors) {
    const span = (sensor.max - sensor.min) * 0.1 || 1;
    sensor.value = randomJitter(sensor.value, span, sensor.min, sensor.max);
  }
  updateScalarSensorsUI();
}

function mainLoop() {
  updateSensors();
  updateTelemetry();
  applyAutomation();
}

// Initialisation

function populateRuleFormOptions() {
  const sensorSelect = document.getElementById("rule-sensor");
  const actuatorSelect = document.getElementById("rule-actuator");

  sensorSelect.innerHTML = "";
  actuatorSelect.innerHTML = "";

  scalarSensors.forEach((sensor) => {
    const opt = document.createElement("option");
    opt.value = sensor.id;
    opt.textContent = sensor.label;
    sensorSelect.appendChild(opt);
  });

  actuators.forEach((actuator) => {
    const opt = document.createElement("option");
    opt.value = actuator.id;
    opt.textContent = actuator.label;
    actuatorSelect.appendChild(opt);
  });
}

function setupRuleModalEvents() {
  const modal = document.getElementById("rule-modal");
  const closeBtn = document.getElementById("rule-modal-close");
  const cancelBtn = document.getElementById("rule-cancel-btn");
  const form = document.getElementById("rule-form");
  const backdrop = document.querySelector("#rule-modal .modal-backdrop");

  closeBtn.addEventListener("click", closeRuleModal);
  cancelBtn.addEventListener("click", closeRuleModal);
  backdrop.addEventListener("click", closeRuleModal);
  form.addEventListener("submit", handleRuleFormSubmit);

  document.getElementById("add-rule-btn").addEventListener("click", () =>
    openRuleModal(null)
  );
}

function init() {
  renderScalarSensors();
  renderTelemetryCards();
  renderActuators();
  renderRules();

  populateRuleFormOptions();
  setupRuleModalEvents();
  setupNav();
  startMissionClock();
  simulateConnectionIndicator();

  // kick off telemetry state with a few points
  updateTelemetry();

  setInterval(mainLoop, 1500);
}

window.addEventListener("DOMContentLoaded", init);

