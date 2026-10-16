# ESP32 device protocol

The node talks to a host board (e.g. ESP32) over a serial port using plain text lines (`\n` terminated, ASCII,
115200 baud by default). The default sensor source is a **simulated feed**; the serial adapter is optional
(`pip install pyserial`, set `"device": {"type": "serial", "port": "COM3"}` in `ecaps.config.json`).

**Status:** the Python adapter (`ecaps/devices.py`) is tested only against an in-memory fake port in `tests/test_devices.py`.
The sketch below is an **untested example**: it has not been compiled or run on real hardware by the author of this repo.
Pin numbers and sensor scaling are placeholders you must adapt and calibrate.

## Messages

| Direction | Line | Meaning |
|---|---|---|
| node -> device | `R` | request a reading |
| device -> node | `S name=value name=value ...` | readings, names `[a-z0-9_]+`, finite decimal numbers |
| node -> device | `P on` / `P off` | set pump |
| node -> device | `A <text>` | show/log an alert (free text, no newline) |
| device -> node | `OK ...` or `ERR ...` | acknowledgement of `P` / `A` |

Lines from the device that start with anything else (boot logs, debug) are ignored. If the device does not answer within
the timeout (2 s default) the adapter raises `DeviceError`, and the agent reports the action as failed instead of
pretending it worked. The default sensor names used by the example tasks are `soil_moisture`, `tank_level`, `temperature`.

## Example sketch (untested)

```cpp
// ECAPs example device sketch for ESP32 (Arduino core). UNTESTED EXAMPLE.
const int PIN_SOIL = 34, PIN_TANK = 35, PIN_PUMP = 26;   // placeholders: change for your wiring

float pct(int raw) { return 100.0f * raw / 4095.0f; }     // placeholder scaling, NOT calibrated

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PUMP, OUTPUT);
  digitalWrite(PIN_PUMP, LOW);
}

void loop() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line == "R") {
    float temp = 25.0f;                                    // replace with a real temperature sensor read
    Serial.printf("S soil_moisture=%.1f tank_level=%.1f temperature=%.1f\n",
                  pct(analogRead(PIN_SOIL)), pct(analogRead(PIN_TANK)), temp);
  } else if (line == "P on") {
    digitalWrite(PIN_PUMP, HIGH); Serial.println("OK pump on");
  } else if (line == "P off") {
    digitalWrite(PIN_PUMP, LOW);  Serial.println("OK pump off");
  } else if (line.startsWith("A ")) {
    Serial.println("OK alert");                            // e.g. blink an LED or buzzer here
  } else {
    Serial.println("ERR unknown");
  }
}
```

## Quick check on your machine
    python -m ecaps.devices --port COM3     # prints one JSON snapshot, or an error if the device is silent
