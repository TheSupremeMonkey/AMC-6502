#include <Arduino.h>

// Pro Micro has USB activity LEDs rather than an Uno-style pin-13 LED.
// The selected variant supplies active-low RX LED macros (PB0).
namespace {
bool ledOn = false;
bool serialWasOpen = false;
unsigned long lastBlink = 0;
unsigned long lastMessage = 0;
unsigned long heartbeat = 0;

void printStartup() {
    Serial.print(F("AMC-6502 chip-tester bring-up; configured F_CPU="));
    Serial.print(F_CPU);
    Serial.println(F(" Hz; blink/USB serial only"));
}
}

void setup() {
    TX_RX_LED_INIT;
    RXLED0;
    Serial.begin(115200);
    // Never wait for a monitor: blink also works with USB serial closed.
}

void loop() {
    const unsigned long now = millis();
    if (now - lastBlink >= 500) {
        lastBlink = now;
        ledOn = !ledOn;
        if (ledOn) {
            RXLED1;
        } else {
            RXLED0;
        }
    }

    const bool serialOpen = static_cast<bool>(Serial);
    if (serialOpen && !serialWasOpen) {
        printStartup();
        lastMessage = now;
    }
    serialWasOpen = serialOpen;
    if (serialOpen && now - lastMessage >= 1000) {
        lastMessage = now;
        Serial.print(F("alive "));
        Serial.println(++heartbeat);
    }
}
