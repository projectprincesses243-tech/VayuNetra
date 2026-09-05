#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// =====================================================
// VAYUNETRA NODE 1
// =====================================================

#define NODE_ID 1
#define SURVIVOR_BUTTON_PIN 4

// =====================================================
// LCD CONFIGURATION
// =====================================================

#define LCD_SDA 21
#define LCD_SCL 22

LiquidCrystal_I2C lcd(0x27, 16, 2);

// =====================================================
// VERIFIED MAC ADDRESSES
// =====================================================

uint8_t NODE1_MAC[] = {
  0xEC, 0x64, 0xC9, 0x6D, 0x7B, 0x00
};

uint8_t NODE2_MAC[] = {
  0xC0, 0xCD, 0xD6, 0x85, 0x3B, 0x78
};

uint8_t NODE3_MAC[] = {
  0xC0, 0xCD, 0xD6, 0x85, 0x5E, 0xB8
};

// =====================================================
// MESSAGE TYPES
// =====================================================

enum MessageType {
  MSG_SURVIVOR = 4,
  MSG_EVENT_ACK = 5
};

// =====================================================
// VAYUNETRA PACKET
// =====================================================

struct VayuPacket {

  uint8_t source;
  uint8_t destination;
  uint8_t messageType;

  uint16_t sequence;

  uint32_t timestamp;

  uint16_t eventID;

  uint8_t ttl;

  char payload[48];
};

// =====================================================
// GLOBAL VARIABLES
// =====================================================

uint16_t sequenceNumber = 1;
uint16_t eventCounter = 1;

bool lastButtonState = HIGH;

unsigned long lastButtonTime = 0;

// =====================================================
// RECEIVE BUFFER
// =====================================================

volatile bool packetWaiting = false;

VayuPacket receivedPacket;

// =====================================================
// LCD FUNCTIONS
// =====================================================

void showLCD(String line1, String line2) {

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print(line1.substring(0, 16));

  lcd.setCursor(0, 1);
  lcd.print(line2.substring(0, 16));
}


// =====================================================
// DISPLAY RECEIVED PACKET
// =====================================================

void displayReceivedPacket(VayuPacket packet) {

  if (packet.messageType == MSG_SURVIVOR) {

    String line1 = "RX NODE ";
    line1 += String(packet.source);

    showLCD(
      line1,
      "SURVIVOR"
    );

  }

  else if (packet.messageType == MSG_EVENT_ACK) {

    String line1 = "ACK NODE ";
    line1 += String(packet.source);

    showLCD(
      line1,
      "EVENT CONFIRMED"
    );

  }

  else {

    String line1 = "RX NODE ";
    line1 += String(packet.source);

    showLCD(
      line1,
      "MESSAGE RX"
    );
  }
}


// =====================================================
// GET NODE MAC
// =====================================================

uint8_t* getNodeMAC(uint8_t node) {

  if (node == 1)
    return NODE1_MAC;

  if (node == 2)
    return NODE2_MAC;

  if (node == 3)
    return NODE3_MAC;

  return nullptr;
}


// =====================================================
// ADD PEER
// =====================================================

void addPeer(uint8_t node) {

  if (node == NODE_ID)
    return;

  uint8_t* mac = getNodeMAC(node);

  if (mac == nullptr)
    return;

  if (esp_now_is_peer_exist(mac))
    return;

  esp_now_peer_info_t peerInfo = {};

  memcpy(
    peerInfo.peer_addr,
    mac,
    6
  );

  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  esp_err_t result =
    esp_now_add_peer(&peerInfo);

  Serial.print("Adding Node ");
  Serial.print(node);
  Serial.print(": ");

  if (result == ESP_OK)
    Serial.println("SUCCESS");
  else
    Serial.println("FAILED");
}


// =====================================================
// SEND PACKET
// =====================================================

bool sendPacket(VayuPacket &packet) {

  uint8_t* mac =
    getNodeMAC(packet.destination);

  if (mac == nullptr)
    return false;

  esp_err_t result =
    esp_now_send(
      mac,
      (uint8_t*)&packet,
      sizeof(packet)
    );

  return result == ESP_OK;
}


// =====================================================
// SEND CALLBACK
// =====================================================

void OnDataSent(
  const wifi_tx_info_t *info,
  esp_now_send_status_t status
) {

  if (status == ESP_NOW_SEND_SUCCESS)
    Serial.println("[TX] DELIVERY SUCCESS");
  else
    Serial.println("[TX] DELIVERY FAILED");
}


// =====================================================
// RECEIVE CALLBACK
// =====================================================

void OnDataRecv(
  const esp_now_recv_info_t *recv_info,
  const uint8_t *data,
  int len
) {

  if (len != sizeof(VayuPacket))
    return;

  if (packetWaiting)
    return;

  memcpy(
    &receivedPacket,
    data,
    sizeof(VayuPacket)
  );

  packetWaiting = true;
}


// =====================================================
// CREATE SURVIVOR EVENT
// =====================================================

void createSurvivorEvent() {

  VayuPacket event = {};

  event.source = NODE_ID;

  // Node 1 sends to Node 2
  event.destination = 2;

  event.messageType = MSG_SURVIVOR;

  event.sequence = sequenceNumber++;

  event.timestamp = millis();

  // Unique event ID
  event.eventID =
    (NODE_ID << 12) |
    (eventCounter & 0x0FFF);

  eventCounter++;

  event.ttl = 3;

  strcpy(
    event.payload,
    "SURVIVOR_DETECTED"
  );

  Serial.println();
  Serial.println();
  Serial.println("########################################");
  Serial.println("       SURVIVOR EVENT CREATED");
  Serial.println("########################################");

  Serial.print("Origin Node : ");
  Serial.println(NODE_ID);

  Serial.print("Event ID    : ");
  Serial.println(event.eventID);

  Serial.println("Detection   : PHYSICAL BUTTON");

  // Node 1 sends to Node 2
  if (sendPacket(event)) {

    Serial.println(
      "[EVENT] SURVIVOR_DETECTED sent to Node 2"
    );

    showLCD(
      "SURVIVOR",
      "NODE 1 -> NODE 2"
    );
  }

  else {

    Serial.println(
      "[EVENT] FAILED TO SEND"
    );

    showLCD(
      "EVENT SEND",
      "FAILED"
    );
  }

  Serial.println("########################################");
}


// =====================================================
// PROCESS RECEIVED PACKET
// =====================================================

void processReceivedPacket(VayuPacket packet) {

  Serial.println();
  Serial.println("========================================");
  Serial.println("       VAYUNETRA PACKET RECEIVED");
  Serial.println("========================================");

  Serial.print("Source      : ");
  Serial.println(packet.source);

  Serial.print("Destination : ");
  Serial.println(packet.destination);

  Serial.print("Type        : ");

  if (packet.messageType == MSG_SURVIVOR)
    Serial.println("SURVIVOR_DETECTED");

  else if (packet.messageType == MSG_EVENT_ACK)
    Serial.println("EVENT_ACK");

  else
    Serial.println("UNKNOWN");

  Serial.print("Sequence    : ");
  Serial.println(packet.sequence);

  Serial.print("Event ID    : ");
  Serial.println(packet.eventID);

  Serial.print("TTL         : ");
  Serial.println(packet.ttl);

  Serial.print("Payload     : ");
  Serial.println(packet.payload);

  Serial.println("========================================");


  // ===================================================
  // DISPLAY MESSAGE ON LCD
  // ===================================================

  displayReceivedPacket(packet);


  // ===================================================
  // SURVIVOR EVENT RECEIVED
  // ===================================================

  if (packet.messageType == MSG_SURVIVOR) {

    Serial.println();
    Serial.println("***************************************");
    Serial.println("       SURVIVOR DETECTED!");
    Serial.println("***************************************");

    Serial.print("Event ID    : ");
    Serial.println(packet.eventID);

    Serial.print("Origin Node : ");
    Serial.println(packet.source);

    Serial.println("Status      : EVENT CONFIRMED");


    // -------------------------------------------------
    // SEND ACK BACK TO ORIGIN
    // -------------------------------------------------

    VayuPacket ack = {};

    ack.source = NODE_ID;

    ack.destination = packet.source;

    ack.messageType = MSG_EVENT_ACK;

    ack.sequence = sequenceNumber++;

    ack.timestamp = millis();

    ack.eventID = packet.eventID;

    ack.ttl = 3;

    strcpy(
      ack.payload,
      "EVENT_RECEIVED"
    );

    if (sendPacket(ack)) {

      Serial.println(
        "[ACK] EVENT_ACK sent to origin"
      );
    }

    Serial.println("***************************************");
  }


  // ===================================================
  // EVENT ACK RECEIVED
  // ===================================================

  if (packet.messageType == MSG_EVENT_ACK) {

    Serial.println();
    Serial.println("+++++++++++++++++++++++++++++++++++++++");
    Serial.println("       SURVIVOR EVENT ACKNOWLEDGED");
    Serial.println("+++++++++++++++++++++++++++++++++++++++");

    Serial.print("Event ID        : ");
    Serial.println(packet.eventID);

    Serial.print("Acknowledged by : Node ");
    Serial.println(packet.source);

    Serial.println(
      "STATUS          : SWARM NODE CONFIRMED"
    );

    Serial.println("+++++++++++++++++++++++++++++++++++++++");
  }
}


// =====================================================
// SETUP
// =====================================================

void setup() {

  Serial.begin(115200);

  delay(1000);


  // ---------------------------------------------------
  // LCD
  // ---------------------------------------------------

  Wire.begin(
    LCD_SDA,
    LCD_SCL
  );

  lcd.init();
  lcd.backlight();

  showLCD(
    "VAYUNETRA",
    "NODE 1 GATEWAY"
  );

  delay(2000);

  showLCD(
    "ESP-NOW READY",
    "WAITING..."
  );


  // ---------------------------------------------------
  // BUTTON
  // ---------------------------------------------------

  pinMode(
    SURVIVOR_BUTTON_PIN,
    INPUT_PULLUP
  );


  Serial.println();
  Serial.println();
  Serial.println("========================================");
  Serial.println("          VAYUNETRA NODE 1");
  Serial.println("========================================");


  // ---------------------------------------------------
  // WIFI
  // ---------------------------------------------------

  WiFi.mode(WIFI_STA);

  Serial.print("Node ID: ");
  Serial.println(NODE_ID);

  Serial.print("MAC: ");
  Serial.println(WiFi.macAddress());


  // ---------------------------------------------------
  // ESP-NOW
  // ---------------------------------------------------

  if (esp_now_init() != ESP_OK) {

    Serial.println(
      "ERROR: ESP-NOW INITIALIZATION FAILED"
    );

    showLCD(
      "ESP-NOW",
      "INIT FAILED"
    );

    return;
  }


  esp_now_register_send_cb(
    OnDataSent
  );

  esp_now_register_recv_cb(
    OnDataRecv
  );


  // ---------------------------------------------------
  // ADD NODE 2
  // ---------------------------------------------------

  addPeer(2);


  // ---------------------------------------------------
  // ADD NODE 3
  // ---------------------------------------------------

  addPeer(3);


  Serial.println();
  Serial.println("========================================");
  Serial.println("NODE 1 READY");
  Serial.println("Waiting for button press...");
  Serial.println("GPIO 4 -> BUTTON -> GND");
  Serial.println("LCD I2C -> SDA/SCL");
  Serial.println("========================================");

  showLCD(
    "NODE 1 READY",
    "WAITING..."
  );
}


// =====================================================
// LOOP
// =====================================================

void loop() {

  // ---------------------------------------------------
  // PROCESS RECEIVED PACKETS
  // ---------------------------------------------------

  if (packetWaiting) {

    VayuPacket packet;

    noInterrupts();

    memcpy(
      &packet,
      &receivedPacket,
      sizeof(VayuPacket)
    );

    packetWaiting = false;

    interrupts();

    processReceivedPacket(packet);
  }


  // ---------------------------------------------------
  // BUTTON
  // ---------------------------------------------------

  bool buttonState =
    digitalRead(SURVIVOR_BUTTON_PIN);


  // Detect ONLY HIGH -> LOW transition

  if (
    buttonState == LOW &&
    lastButtonState == HIGH &&
    millis() - lastButtonTime > 500
  ) {

    lastButtonTime = millis();

    createSurvivorEvent();
  }


  lastButtonState = buttonState;

  delay(10);
}