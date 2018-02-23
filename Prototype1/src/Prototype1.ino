/*
*  Simple HTTP get webclient test
*/
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include <EEPROM.h>

#include <ESP8266WiFi.h>

#define BNO055_SAMPLERATE_DELAY_MS (10)

const char* ssid     = "CMU";
const char* password = "";

const char* host = "wifitest.adafruit.com";

uint32 website_ping_timer = millis();

void setup() {
    Serial.begin(115200);
    delay(100);

    // We start by connecting to a WiFi network

    Serial.println();
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(ssid);

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.println("MAC address: ");
    Serial.println(WiFi.macAddress());
}

int value = 0;

void pingWebsite() {
    Serial.print("connecting to ");
    Serial.println(host);

    // Use WiFiClient class to create TCP connections
    WiFiClient client;
    const int httpPort = 80;
    if (!client.connect(host, httpPort)) {
        Serial.println("connection failed");
        return;
    }

    // We now create a URI for the request
    String url = "/testwifi/index.html";
    Serial.print("Requesting URL: ");
    Serial.println(url);

    // This will send the request to the server
    client.print(String("GET ") + url + " HTTP/1.1\r\n" +
    "Host: " + host + "\r\n" +
    "Connection: close\r\n\r\n");
    delay(500);

    // Read all the lines of the reply from server and print them to Serial
    while(client.available()){
        String line = client.readStringUntil('\r');
        Serial.print(line);
    }

    Serial.println();
    Serial.println("closing connection");
}

void loop()
{
    // If millis wraps around, reset timer
    if (millis() - website_ping_timer < 0) website_ping_timer = millis();

    // Ping the website every 5 seconds
    if (millis() - website_ping_timer > 5000) {
        website_ping_timer = millis();
        ++value;
        pingWebsite();
    }

    // Print sensor data every 10 ms
    delay(BNO055_SAMPLERATE_DELAY_MS);
}
