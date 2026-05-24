// CDC.ino - CD changer controller for BMW E39
// Author: @slowtouge_racer (Instagram) - <https://discord.gg/TAAp7jkGBY>
// This code runs on a Wemos D1 board (ESP8266) and controls a relay to switch between the OEM CD changer and the RaspBerryPi. 
// The reason why i use an additional board instead of controlling the relay directly from the RaspBerryPi is that i have a hifi DAC HAT on the rPi that does not give me access to the GPIO pins (i already ordered a different HAT but for now i'm gonna use this solution)
#define RELAY_PIN 14
#define SERIAL_BAUD 115200
#define TIMEOUT_MS 10000
#define LINE_MAX 64

char line[LINE_MAX + 1];
size_t linePos = 0;

bool relayOn = false;
unsigned long lastCommandMs = 0;

void setRelay(bool on) {
  relayOn = on;
  digitalWrite(RELAY_PIN, on ? HIGH : LOW);
}

void sendState() {
  if (relayOn) {
    Serial.println("PI");
  } else {
    Serial.println("OEM");
  }
}

void handleCommand(char *cmd) {
  while (*cmd == ' ') cmd++;

  for (char *p = cmd; *p; ++p) {
    if (*p >= 'a' && *p <= 'z') {
      *p = *p - 'a' + 'A';
    }
  }

  if (strcmp(cmd, "PING") == 0) {
    lastCommandMs = millis();
    Serial.println("PONG");
    return;
  }

  if (strcmp(cmd, "SRC PI") == 0) {
    setRelay(true);
    lastCommandMs = millis();
    Serial.println("PI");
    return;
  }

  if (strcmp(cmd, "SRC OEM") == 0) {
    setRelay(false);
    lastCommandMs = millis();
    Serial.println("OEM");
    return;
  }

  if (strcmp(cmd, "STATE") == 0) {
    lastCommandMs = millis();
    sendState();
    return;
  }

  Serial.println("ERR");
}

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  setRelay(false);
  Serial.begin(SERIAL_BAUD);
  Serial.setTimeout(50);
  lastCommandMs = millis();
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    if (c == '\n' || c == '\r') {
      if (linePos > 0) {
        line[linePos] = '\0';
        handleCommand(line);
        linePos = 0;
      }
    } else {
      if (linePos < LINE_MAX) {
        line[linePos++] = c;
      } else {
        linePos = 0;
        Serial.println("ERR");
      }
    }
  }

  if (relayOn && (millis() - lastCommandMs > TIMEOUT_MS)) {
    setRelay(false);
    Serial.println("OEM");
  }
}
