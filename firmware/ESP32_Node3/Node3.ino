#include <WiFi.h>
#include <esp_now.h>

// =====================================================
// VAYUNETRA NODE 3
// =====================================================

#define NODE_ID 3
#define SURVIVOR_BUTTON_PIN 4

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

// =====================================================
// BUTTON VARIABLES
// =====================================================

bool lastButtonState = HIGH;
bool buttonReady = false;

unsigned long lastButtonTime = 0;

// =====================================================
// RECEIVE BUFFER
// =====================================================

volatile bool packetWaiting = false;

VayuPacket receivedPacket;

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

  Serial.print("[PEER] Node ");
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
// IMPORTANT:
// NO TRANSMISSION HERE
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

  // ---------------------------------------------------
  // EVENT ORIGIN
  // ---------------------------------------------------

  event.source = NODE_ID;

  // Node 3 sends survivor event to Node 1
  event.destination = 1;

  event.messageType = MSG_SURVIVOR;

  event.sequence = sequenceNumber++;

  event.timestamp = millis();

  // ---------------------------------------------------
  // UNIQUE EVENT ID
  //
  // Node 3 events start with 0x3001
  // Decimal = 12289
  // ---------------------------------------------------

  event.eventID =
    (NODE_ID << 12) |
    (eventCounter & 0x0FFF);

  eventCounter++;

  event.ttl = 3;

  strcpy(
    event.payload,
    "SURVIVOR_DETECTED"
  );

  // ---------------------------------------------------
  // DISPLAY EVENT
  // ---------------------------------------------------

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

  // ---------------------------------------------------
  // SEND TO NODE 1
  // ---------------------------------------------------

  if (sendPacket(event)) {

    Serial.println(
      "[EVENT] SURVIVOR_DETECTED sent to Node 1"
    );

  } else {

    Serial.println(
      "[EVENT] FAILED TO SEND"
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

    Serial.println(
      "SURVIVOR_DETECTED"
    );

  else if (packet.messageType == MSG_EVENT_ACK)

    Serial.println(
      "EVENT_ACK"
    );

  else

    Serial.println(
      "UNKNOWN"
    );

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
  // SURVIVOR EVENT RECEIVED
  // ===================================================

  if (packet.messageType == MSG_SURVIVOR) {

    Serial.println();
    Serial.println("***************************************");
    Serial.println("          SURVIVOR DETECTED!");
    Serial.println("***************************************");

    Serial.print("Event ID    : ");
    Serial.println(packet.eventID);

    Serial.print("Origin Node : ");
    Serial.println(packet.source);

    Serial.println("Status      : EVENT CONFIRMED");

    // -------------------------------------------------
    // CREATE ACK
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

    // -------------------------------------------------
    // SEND ACK
    // -------------------------------------------------

    if (sendPacket(ack)) {

      Serial.println(
        "[ACK] EVENT_ACK sent to origin"
      );

    } else {

      Serial.println(
        "[ACK] FAILED TO SEND"
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

  // ===================================================
  // BUTTON
  // ===================================================

  pinMode(
    SURVIVOR_BUTTON_PIN,
    INPUT_PULLUP
  );

  // Read initial button state
  lastButtonState =
    digitalRead(SURVIVOR_BUTTON_PIN);

  // ===================================================
  // STARTUP MESSAGE
  // ===================================================

  Serial.println();
  Serial.println();
  Serial.println("========================================");
  Serial.println("          VAYUNETRA NODE 3");
  Serial.println("========================================");

  WiFi.mode(WIFI_STA);

  Serial.print("Node ID: ");
  Serial.println(NODE_ID);

  Serial.print("MAC: ");
  Serial.println(WiFi.macAddress());

  // ===================================================
  // ESP-NOW INITIALIZATION
  // ===================================================

  if (esp_now_init() != ESP_OK) {

    Serial.println(
      "ERROR: ESP-NOW INITIALIZATION FAILED"
    );

    return;
  }

  esp_now_register_send_cb(
    OnDataSent
  );

  esp_now_register_recv_cb(
    OnDataRecv
  );

  // ===================================================
  // ADD NODE 1 AND NODE 2
  // ===================================================

  addPeer(1);
  addPeer(2);

  // ===================================================
  // READY
  // ===================================================

  Serial.println();
  Serial.println("========================================");
  Serial.println("NODE 3 READY");
  Serial.println("Peers: NODE 1 + NODE 2");
  Serial.println("No automatic messages");
  Serial.println("Waiting for button press...");
  Serial.println("GPIO 4 -> BUTTON -> GND");
  Serial.println("========================================");

  // ===================================================
  // ARM BUTTON
  // ===================================================

  if (lastButtonState == HIGH) {

    buttonReady = true;

    Serial.println("[BUTTON] READY");

  } else {

    Serial.println(
      "[BUTTON] RELEASE BUTTON TO ARM"
    );
  }
}

// =====================================================
// LOOP
// =====================================================

void loop() {

  // ===================================================
  // PROCESS RECEIVED PACKET
  // ===================================================

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

  // ===================================================
  // BUTTON STATE
  // ===================================================

  bool buttonState =
    digitalRead(SURVIVOR_BUTTON_PIN);

  // ---------------------------------------------------
  // WAIT FOR RELEASE AFTER RESET
  // ---------------------------------------------------

  if (!buttonReady) {

    if (buttonState == HIGH) {

      buttonReady = true;

      lastButtonState = HIGH;

      Serial.println("[BUTTON] READY");
    }

    delay(10);

    return;
  }

  // ---------------------------------------------------
  // NEW BUTTON PRESS
  // HIGH -> LOW
  // ---------------------------------------------------

  if (
    buttonState == LOW &&
    lastButtonState == HIGH &&
    millis() - lastButtonTime > 500
  ) {

    lastButtonTime = millis();

    createSurvivorEvent();
  }

  // ---------------------------------------------------
  // SAVE BUTTON STATE
  // ---------------------------------------------------

  lastButtonState = buttonState;

  delay(10);
}