// CDC.ino - CD changer controller for BMW E39
// Author: @slowtouge_racer (Instagram) - <https://discord.gg/TAAp7jkGBY>
// This code runs on a Wemos D1 board (ESP8266) and controls a relay to switch between the OEM CD changer and the RaspBerryPi. 
// The reason why i use an additional board instead of controlling the relay directly from the RaspBerryPi is that i have a hifi DAC HAT on the rPi that does not give me access to the GPIO pins (i already ordered a different HAT but for now i'm gonna use this solution)

#define RELAY_PIN 14
#define SERIAL_BAUD 115200
#define TIMEOUT_MS 10000 

String line = "";
bool relayOn = false;
unsigned long lastCommandMs = 0;

void setRelay(bool on) {
    relayOn = on;
    digitalWrite(RELAY_PIN, on ? HIGH : LOW);
}

void replyState() {
    if (relayOn) {
        Serial.println("STATE PI");
    } else {
        Serial.println("STATE OEM");
    }
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "SRC PI") {
    setRelay(true);
    lastCommandMs = millis();
    Serial.println("OK PI");
  } 
  else if (cmd == "SRC OEM") {
    setRelay(false);
    lastCommandMs = millis();
    Serial.println("OK OEM");
  } 
  else if (cmd == "STATE") {
    replyState();
  } 
  else if (cmd == "PING") {
    lastCommandMs = millis();
    Serial.println("PONG");
  } 
  else {
    Serial.print("ERR ");
    Serial.println(cmd);
  }
}

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  setRelay(false);                 
  Serial.begin(SERIAL_BAUD);
  Serial.setTimeout(50);
  lastCommandMs = millis();
  Serial.println("BOOT OEM");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    if (c == '\n' || c == '\r') {
      if (line.length() > 0) {
        handleCommand(line);
        line = "";
      }
    } else {
      line += c;
      if (line.length() > 64) {
        line = "";
        Serial.println("ERR OVERFLOW");
      }
    }
  }

  if (relayOn && (millis() - lastCommandMs > TIMEOUT_MS)) {
    setRelay(false);
    Serial.println("TIMEOUT OEM");
  }
}
