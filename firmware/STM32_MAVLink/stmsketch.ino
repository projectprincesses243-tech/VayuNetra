#include <MAVLink.h>

#define MAV_SYS_ID  1
#define MAV_COMP_ID MAV_COMP_ID_AUTOPILOT1

// ============================================================
// MAVLink TX
// ============================================================

mavlink_message_t msg;
uint8_t txBuffer[MAVLINK_MAX_PACKET_LEN];

void sendMAVLink()
{
    uint16_t length =
        mavlink_msg_to_send_buffer(txBuffer, &msg);

    Serial2.write(txBuffer, length);
}


// ============================================================
// HEARTBEAT
// ============================================================

void sendHeartbeat()
{
    mavlink_msg_heartbeat_pack(
        MAV_SYS_ID,
        MAV_COMP_ID,
        &msg,

        MAV_TYPE_QUADROTOR,
        MAV_AUTOPILOT_GENERIC,

        MAV_MODE_FLAG_MANUAL_INPUT_ENABLED,

        0,
        MAV_STATE_ACTIVE
    );

    sendMAVLink();
}


// ============================================================
// ATTITUDE
// ============================================================

void sendAttitude()
{
    static float yaw = 0.0f;

    yaw += 0.005f;

    if (yaw > 6.283f)
    {
        yaw = 0.0f;
    }

    mavlink_msg_attitude_pack(
        MAV_SYS_ID,
        MAV_COMP_ID,
        &msg,

        millis(),

        0.02f,      // roll
        0.01f,      // pitch
        yaw,        // yaw

        0.0f,       // roll speed
        0.0f,       // pitch speed
        0.01f       // yaw speed
    );

    sendMAVLink();
}


// ============================================================
// SYSTEM STATUS + BATTERY
// ============================================================

void sendSystemStatus()
{
    static int batteryRemaining = 100;
    static uint32_t lastBatteryUpdate = 0;

    uint32_t now = millis();

    if (now - lastBatteryUpdate >= 10000)
    {
        lastBatteryUpdate = now;

        if (batteryRemaining > 20)
        {
            batteryRemaining--;
        }
    }

    uint16_t voltage = 14800;
    int16_t current = 2500;
    int8_t remaining = batteryRemaining;

    uint32_t sensors_present =
        MAV_SYS_STATUS_SENSOR_3D_GYRO |
        MAV_SYS_STATUS_SENSOR_3D_ACCEL |
        MAV_SYS_STATUS_SENSOR_3D_MAG |
        MAV_SYS_STATUS_SENSOR_ABSOLUTE_PRESSURE;

    uint32_t sensors_enabled =
        MAV_SYS_STATUS_SENSOR_3D_GYRO |
        MAV_SYS_STATUS_SENSOR_3D_ACCEL |
        MAV_SYS_STATUS_SENSOR_3D_MAG |
        MAV_SYS_STATUS_SENSOR_ABSOLUTE_PRESSURE;

    uint32_t sensors_health =
        MAV_SYS_STATUS_SENSOR_3D_GYRO |
        MAV_SYS_STATUS_SENSOR_3D_ACCEL |
        MAV_SYS_STATUS_SENSOR_3D_MAG |
        MAV_SYS_STATUS_SENSOR_ABSOLUTE_PRESSURE;

    mavlink_msg_sys_status_pack(
        MAV_SYS_ID,
        MAV_COMP_ID,
        &msg,

        sensors_present,
        sensors_enabled,
        sensors_health,

        500,

        voltage,
        current,
        remaining,

        0,
        0,
        0,
        0,
        0,
        0,

        0,
        0,
        0
    );

    sendMAVLink();
}


// ============================================================
// GLOBAL POSITION
// ============================================================

void sendPosition()
{
    /*
     * Simulated position near Bengaluru.
     *
     * Latitude  : 12.9716 N
     * Longitude : 77.5946 E
     *
     * The position slowly changes to simulate movement.
     */

    static int32_t latitude  = 129344000;
    static int32_t longitude = 776922000;

    static uint32_t lastUpdate = 0;

    uint32_t now = millis();

    if (now - lastUpdate >= 100)
    {
        lastUpdate = now;

        // Approximately a small movement
        latitude += 2;
        longitude += 2;
    }

    int32_t altitude = 120000;       // 120 m AMSL
    int32_t relativeAlt = 50000;     // 50 m above home

    int16_t vx = 150;                // 1.5 m/s North
    int16_t vy = 100;                // 1.0 m/s East
    int16_t vz = 0;                  // stationary vertically

    uint16_t heading = 9000;         // 90 degrees


    mavlink_msg_global_position_int_pack(
        MAV_SYS_ID,
        MAV_COMP_ID,
        &msg,

        millis(),

        latitude,
        longitude,

        altitude,
        relativeAlt,

        vx,
        vy,
        vz,

        heading
    );

    sendMAVLink();
}



void sendVFRHUD()
{
    float airspeed = 2.0f;
    float groundspeed = 2.0f;

    int16_t heading = 90;

    uint16_t throttle = 50;

    float altitude = 50.0f;

    float climb = 0.5f;

    mavlink_msg_vfr_hud_pack(
        MAV_SYS_ID,
        MAV_COMP_ID,
        &msg,

        airspeed,
        groundspeed,
        heading,
        throttle,
        altitude,
        climb
    );

    sendMAVLink();
}


// ============================================================
// SETUP
// ============================================================

void setup()
{
    pinMode(LED_BUILTIN, OUTPUT);

    Serial2.begin(115200);

    delay(2000);
}


// ============================================================
// MAIN LOOP
// ============================================================

void loop()
{
    static uint32_t lastHeartbeat = 0;
    static uint32_t lastAttitude  = 0;
    static uint32_t lastStatus    = 0;
    static uint32_t lastPosition  = 0;
    

    uint32_t now = millis();

    

    


    // --------------------------------------------------------
    // HEARTBEAT — 1 Hz
    // --------------------------------------------------------

    if (now - lastHeartbeat >= 1000)
    {
        lastHeartbeat = now;

        sendHeartbeat();

        digitalWrite(
            LED_BUILTIN,
            !digitalRead(LED_BUILTIN)
        );
    }


    // --------------------------------------------------------
    // ATTITUDE — 10 Hz
    // --------------------------------------------------------

    if (now - lastAttitude >= 100)
    {
        lastAttitude = now;

        sendAttitude();
    }


    // --------------------------------------------------------
    // SYSTEM STATUS — 1 Hz
    // --------------------------------------------------------

    if (now - lastStatus >= 1000)
    {
        lastStatus = now;

        sendSystemStatus();
    }


    // --------------------------------------------------------
    // POSITION — 10 Hz
    // --------------------------------------------------------

    if (now - lastPosition >= 100)
    {
        lastPosition = now;

        sendPosition();
    }
}