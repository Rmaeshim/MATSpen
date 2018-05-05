
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include <EEPROM.h>

#include <SerialManager.h>
#include <TB6612.h>
#include <BNO055AngVelContainer.h>

/* ----------------------- *
* BNO055 global variables *
* ----------------------- */

// #define USE_CALIBRATION

#define INCLUDE_FILTERED_DATA
// #define USE_QUATERNIONS
#define INCLUDE_MAG_DATA
#define INCLUDE_GYRO_DATA
// #define INCLUDE_ACCEL_DATA
#define INCLUDE_LINACCEL_DATA

SerialManager manager("BNO055-IMU");

// Accelerometer & gyroscope only for getting relative orientation, subject to gyro drift
// Adafruit_BNO055 bno = Adafruit_BNO055(0x08); // OPERATION_MODE_IMUPLUS

// Accelerometer & magnetometer only for getting relative orientation
// Adafruit_BNO055 bno = Adafruit_BNO055(0x0a);  // OPERATION_MODE_M4G

// Gets heading only from compass
// Adafruit_BNO055 bno = Adafruit_BNO055(0x09); // OPERATION_MODE_COMPASS

// OPERATION_MODE_NDOF without fast magnetometer calibration
// Adafruit_BNO055 bno = Adafruit_BNO055(OPERATION_MODE_NDOF_FMC_OFF);

Adafruit_BNO055 bno = Adafruit_BNO055();

imu::Quaternion quat;
imu::Vector<3> euler;
imu::Vector<3> mag;
imu::Vector<3> gyro;
imu::Vector<3> accel;
imu::Vector<3> linaccel;

/* Set the delay between fresh samples */
#define BNO055_SAMPLERATE_DELAY_MS (1)

double x_ang_vel = 0.0;
double y_ang_vel = 0.0;
double z_ang_vel = 0.0;

BNO055AngVelContainer x_ang_vel_container;
BNO055AngVelContainer y_ang_vel_container;
BNO055AngVelContainer z_ang_vel_container;

uint32_t imu_timer = 0;
uint32_t current_time = 0;

TB6612 motorB(12.0, 75.81, 6.4, 5, 7, 8, 2, 3);  // 75:1
int prev_command = 0;
double prev_commanded_speed = 0.0;

#define IMP_CONST_LEN 3

char selected_imu_axis = 'x';
double command_controller_speed = 0.0;
bool imp_controller_enabled = false;
bool feedforward_controller_enabled = false;
double imp_const_A[IMP_CONST_LEN] = {1.0013, -1.8960, 0.9987};
double imp_const_B[IMP_CONST_LEN] = {1.0000, -1.8960, 1.0000};
double saved_inputs_speed[IMP_CONST_LEN] = {0.0, 0.0, 0.0};
double saved_outputs_ang_vel[IMP_CONST_LEN] = {0.0, 0.0, 0.0};
size_t imp_current_index = 0;

double feedforward_Kp = 1.0;

double updateIMPcontroller(double current_motor_input, double current_sensor_output)
{
    // y(n) = b(1) / a(1) * x(n) + b(2) / a(1) * x(n - 1) + b(3) / a(1) * x(n - 2)
    //                           - a(2) / a(1) * y(n - 1) - a(3) / a(1) * y(n - 2)

    saved_outputs_ang_vel[imp_current_index] = current_sensor_output;
    saved_inputs_speed[imp_current_index] = current_motor_input;

    double output = imp_const_B[0] / imp_const_A[0] * saved_outputs_ang_vel[imp_current_index];

    size_t buffer_i = 0;
    size_t i;
    for (i = 1; i < IMP_CONST_LEN; i++) {
        buffer_i = (i + imp_current_index) % IMP_CONST_LEN;
        output += imp_const_B[i] / imp_const_A[0] * saved_outputs_ang_vel[buffer_i];
    }

    buffer_i = 0;
    for (i = 1; i < IMP_CONST_LEN; i++) {
        buffer_i = (i + imp_current_index) % IMP_CONST_LEN;
        output -= imp_const_A[i] / imp_const_A[0] * saved_inputs_speed[buffer_i];
    }

    if (imp_current_index == 0) {
        imp_current_index = IMP_CONST_LEN - 1;
    }
    else {
        imp_current_index--;
    }

    return output;
}

void feedforward(double current_sensor_output)
{
    //reference value is always zero
    //pidErr is error = (desired value) - (actual value)
    //pidErr will also give opposite direction for motor to turn
    float pidErr = -current_sensor_output/(2*PI);

    //want fast adjustment, should only have Kp as gain
    //adjustedSpeed is new speed of PID controller, convert from radians/s to rps
    //should tune Kp until appropriate
    //in terms of feedfoward, Kp should be 1
    return feedforward_Kp*pidErr;
}

/**************************************************************************/
/*
Displays some basic information on this sensor from the unified
sensor API sensor_t type (see Adafruit_Sensor for more information)
*/
/**************************************************************************/
void displaySensorDetails(void)
{
    sensor_t sensor;
    bno.getSensor(&sensor);
    Serial.println("------------------------------------");
    Serial.print("Sensor:       "); Serial.println(sensor.name);
    Serial.print("Driver Ver:   "); Serial.println(sensor.version);
    Serial.print("Unique ID:    "); Serial.println(sensor.sensor_id);
    Serial.print("Max Value:    "); Serial.print(sensor.max_value); Serial.println(" xxx");
    Serial.print("Min Value:    "); Serial.print(sensor.min_value); Serial.println(" xxx");
    Serial.print("Resolution:   "); Serial.print(sensor.resolution); Serial.println(" xxx");
    Serial.println("------------------------------------");
    Serial.println("");
    delay(500);
}

/**************************************************************************/
/*
Display some basic info about the sensor status
*/
/**************************************************************************/
void displaySensorStatus(void)
{
    /* Get the system status values (mostly for debugging purposes) */
    uint8_t system_status, self_test_results, system_error;
    system_status = self_test_results = system_error = 0;
    bno.getSystemStatus(&system_status, &self_test_results, &system_error);

    /* Display the results in the Serial Monitor */
    Serial.println("");
    Serial.print("System Status: 0x");
    Serial.println(system_status, HEX);
    Serial.print("Self Test:     0x");
    Serial.println(self_test_results, HEX);
    Serial.print("System Error:  0x");
    Serial.println(system_error, HEX);
    Serial.println("");
    delay(500);
}

/**************************************************************************/
/*
Display sensor calibration status
*/
/**************************************************************************/
void displayCalStatus(void)
{
    /* Get the four calibration values (0..3) */
    /* Any sensor data reporting 0 should be ignored, */
    /* 3 means 'fully calibrated" */
    uint8_t system, gyro, accel, mag;
    system = gyro = accel = mag = 0;
    bno.getCalibration(&system, &gyro, &accel, &mag);

    /* The data should be ignored until the system calibration is > 0 */
    Serial.print("\t");
    if (!system)
    {
        Serial.print("! ");
    }

    /* Display the individual values */
    Serial.print("Sys:");
    Serial.print(system, DEC);
    Serial.print(" G:");
    Serial.print(gyro, DEC);
    Serial.print(" A:");
    Serial.print(accel, DEC);
    Serial.print(" M:");
    Serial.print(mag, DEC);
}

/**************************************************************************/
/*
Display the raw calibration offset and radius data
*/
/**************************************************************************/
void displaySensorOffsets(const adafruit_bno055_offsets_t &calibData)
{
    Serial.print("Accelerometer: ");
    Serial.print(calibData.accel_offset_x); Serial.print(" ");
    Serial.print(calibData.accel_offset_y); Serial.print(" ");
    Serial.print(calibData.accel_offset_z); Serial.print(" ");

    Serial.print("\nGyro: ");
    Serial.print(calibData.gyro_offset_x); Serial.print(" ");
    Serial.print(calibData.gyro_offset_y); Serial.print(" ");
    Serial.print(calibData.gyro_offset_z); Serial.print(" ");

    Serial.print("\nMag: ");
    Serial.print(calibData.mag_offset_x); Serial.print(" ");
    Serial.print(calibData.mag_offset_y); Serial.print(" ");
    Serial.print(calibData.mag_offset_z); Serial.print(" ");

    Serial.print("\nAccel Radius: ");
    Serial.print(calibData.accel_radius);

    Serial.print("\nMag Radius: ");
    Serial.print(calibData.mag_radius);
}


/**************************************************************************/
/*
Initialize the BNO055
*/
/**************************************************************************/
void initImuCalibration() {
    delay(1000);
    Serial.println("Atlasbuggy BNO055 driver code"); Serial.println("");

    /* Initialise the sensor */
    if (!bno.begin())
    {
        /* There was a problem detecting the BNO055 ... check your connections */
        Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
        while (1);
    }

    int eeAddress = 0;
    long bnoID;
    bool foundCalib = false;

    EEPROM.get(eeAddress, bnoID);

    adafruit_bno055_offsets_t calibrationData;
    sensor_t sensor;

    /*
    *  Look for the sensor's unique ID at the beginning oF EEPROM.
    *  This isn't foolproof, but it's better than nothing.
    */
    bno.getSensor(&sensor);
    Serial.print("BNO055 sensor ID: "); Serial.println(sensor.sensor_id);
    Serial.print("EEPROM sensor ID: "); Serial.println(bnoID);

    if (bnoID != sensor.sensor_id)
    {
        Serial.println("\nNo Calibration Data for this sensor exists in EEPROM");
        delay(500);
    }
    else
    {
        Serial.println("\nFound Calibration for this sensor in EEPROM.");
        eeAddress += sizeof(long);
        EEPROM.get(eeAddress, calibrationData);

        displaySensorOffsets(calibrationData);

        Serial.println("\n\nRestoring Calibration data to the BNO055...");
        bno.setSensorOffsets(calibrationData);

        Serial.println("\n\nCalibration data loaded into BNO055");
        foundCalib = true;
    }

    delay(1000);

    /* Display some basic information on this sensor */
    displaySensorDetails();

    /* Optional: Display current status */
    displaySensorStatus();

    //Crystal must be configured AFTER loading calibration data into BNO055.
    bno.setExtCrystalUse(true);

    sensors_event_t event;
    bno.getEvent(&event);
    if (foundCalib){
        Serial.println("Move sensor slightly to calibrate magnetometers. Press any key to escape.");
        while (!bno.isFullyCalibrated())
        {
            if (Serial.available()) {
                break;
            }
            bno.getEvent(&event);
            delay(BNO055_SAMPLERATE_DELAY_MS);
        }
    }
    else
    {
        Serial.println("Please Calibrate Sensor: ");
        while (!bno.isFullyCalibrated())
        {
            bno.getEvent(&event);

            Serial.print("X: ");
            Serial.print(event.orientation.x, 4);
            Serial.print("\tY: ");
            Serial.print(event.orientation.y, 4);
            Serial.print("\tZ: ");
            Serial.print(event.orientation.z, 4);

            /* Optional: Display calibration status */
            displayCalStatus();

            /* New line for the next sample */
            Serial.println("");

            /* Wait the specified delay before requesting new data */
            delay(BNO055_SAMPLERATE_DELAY_MS);
        }
    }

    Serial.println("\nFully calibrated!");
    Serial.println("--------------------------------");
    Serial.println("Calibration Results: ");
    adafruit_bno055_offsets_t newCalib;
    bno.getSensorOffsets(newCalib);
    displaySensorOffsets(newCalib);

    Serial.println("\n\nStoring calibration data to EEPROM...");

    eeAddress = 0;
    bno.getSensor(&sensor);
    bnoID = sensor.sensor_id;

    EEPROM.put(eeAddress, bnoID);

    eeAddress += sizeof(long);
    EEPROM.put(eeAddress, newCalib);
    Serial.println("Data stored to EEPROM.");

    Serial.println("\n--------------------------------\n");
    delay(500);
}

void initImu() {
    delay(1000);
    Serial.println("Atlasbuggy BNO055 driver code"); Serial.println("");

    int eeAddress = 0;
    long bnoID;

    sensor_t sensor;
    bno.getSensor(&sensor);

    EEPROM.get(eeAddress, bnoID);

    if (bnoID == sensor.sensor_id)
    {
        Serial.println("\nCalibration Data for this sensor exists in EEPROM. Erasing it.");
        clearEeprom();
    }

    /* Initialise the sensor */
    if (!bno.begin())
    {
        /* There was a problem detecting the BNO055 ... check your connections */
        Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
        while (1);
    }

    Serial.print("BNO055 sensor ID: "); Serial.println(sensor.sensor_id);

    delay(1000);

    /* Display some basic information on this sensor */
    displaySensorDetails();

    /* Optional: Display current status */
    displaySensorStatus();

    //Crystal must be configured AFTER loading calibration data into BNO055.
    bno.setExtCrystalUse(true);

    Serial.println("--------------------------------");
}

void clearEeprom()
{
    Serial.println("Clearing EEPROM");
    pinMode(13, OUTPUT);
    bool state = LOW;

    for (size_t i = 0 ; i < EEPROM.length() ; i++) {
        EEPROM.write(i, 0);

        if (i % 15 == 0) {
            state = !state;
            digitalWrite(13, state);
        }
    }

    // turn the LED on when we're done
    digitalWrite(13, LOW);
    Serial.println("EEPROM cleared!!");
}

float qw, qx, qy, qz;
float ex, ey, ez;
float mx, my, mz;
float gx, gy, gz;
float ax, ay, az;
float lx, ly, lz;
uint8_t sys_stat, gyro_stat, accel_stat, mag_stat = 0;


void updateIMU() {
    // Possible vector values can be:
    // - VECTOR_ACCELEROMETER - m/s^2
    // - VECTOR_MAGNETOMETER  - uT
    // - VECTOR_GYROSCOPE     - rad/s
    // - VECTOR_EULER         - degrees
    // - VECTOR_LINEARACCEL   - m/s^2
    // - VECTOR_GRAVITY       - m/s^2

    Serial.print("imu\tt");
    Serial.print(millis());

    #ifdef INCLUDE_FILTERED_DATA

    #ifdef USE_QUATERNIONS
    // Quaternion data
    imu::Quaternion quat = bno.getQuat();

    float new_qw = quat.w();
    float new_qx = quat.x();
    float new_qy = quat.y();
    float new_qz = quat.z();

    if (new_qw != qw) {
        Serial.print("\tqw");
        Serial.print(qw, 4);
        qw = new_qw;
    }

    if (new_qx != qx) {
        Serial.print("\tqx");
        Serial.print(qx, 4);
        qx = new_qx;
    }

    if (new_qy != qy) {
        Serial.print("\tqy");
        Serial.print(qy, 4);
        qy = new_qy;
    }

    if (new_qz != qz) {
        Serial.print("\tqz");
        Serial.print(qz, 4);
        qz = new_qz;
    }

    #else  //  USE_QUATERNIONS
    imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);

    float new_ex = euler.x();
    float new_ey = euler.y();
    float new_ez = euler.z();

    // xyz is yaw pitch roll. switching roll pitch yaw
    if (new_ex != ex) {
        Serial.print("\tez");
        Serial.print(ex, 4);
        ex = new_ex;
        x_ang_vel = x_ang_vel_container.computeAvg(ex);
    }

    if (new_ey != ey) {
        Serial.print("\tey");
        Serial.print(ey, 4);
        ey = new_ey;
        y_ang_vel = y_ang_vel_container.computeAvg(ey);
    }

    if (new_ez != ez) {
        Serial.print("\tex");
        Serial.print(ez, 4);
        ez = new_ez;
        z_ang_vel = z_ang_vel_container.computeAvg(ez);
    }
    #endif  // USE_QUATERNIONS
    #endif  // INCLUDE_FILTERED_DATA

    #ifdef INCLUDE_MAG_DATA
    imu::Vector<3> mag = bno.getVector(Adafruit_BNO055::VECTOR_MAGNETOMETER);

    float new_mx = mag.x();
    float new_my = mag.y();
    float new_mz = mag.z();

    if (new_mx != mx) {
        Serial.print("\tmx");
        Serial.print(mx, 4);
        mx = new_mx;
    }

    if (new_my != my) {
        Serial.print("\tmy");
        Serial.print(my, 4);
        my = new_my;
    }

    if (new_mz != mz) {
        Serial.print("\tmz");
        Serial.print(mz, 4);
        mz = new_mz;
    }
    #endif

    #ifdef INCLUDE_GYRO_DATA
    imu::Vector<3> gyro = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);

    float new_gx = gyro.x();
    float new_gy = gyro.y();
    float new_gz = gyro.z();

    if (new_gx != gx) {
        Serial.print("\tgx");
        Serial.print(gx, 4);
        gx = new_gx;
    }

    if (new_gy != gy) {
        Serial.print("\tgy");
        Serial.print(gy, 4);
        gy = new_gy;
    }

    if (new_gz != gz) {
        Serial.print("\tgz");
        Serial.print(gz, 4);
        gz = new_gz;
    }
    #endif

    #ifdef INCLUDE_ACCEL_DATA
    imu::Vector<3> accel = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);

    float new_ax = accel.x();
    float new_ay = accel.y();
    float new_az = accel.z();

    if (new_ax != ax) {
        Serial.print("\tax");
        Serial.print(ax, 4);
        ax = new_ax;
    }

    if (new_ay != ay) {
        Serial.print("\tay");
        Serial.print(ay, 4);
        ay = new_ay;
    }

    if (new_az != az) {
        Serial.print("\taz");
        Serial.print(az, 4);
        az = new_az;
    }
    #endif

    #ifdef INCLUDE_LINACCEL_DATA
    imu::Vector<3> linaccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);

    float new_lx = linaccel.x();
    float new_ly = linaccel.y();
    float new_lz = linaccel.z();

    if (new_lx != lx) {
        Serial.print("\tlx");
        Serial.print(lx, 4);
        lx = new_lx;
    }

    if (new_ly != ly) {
        Serial.print("\tly");
        Serial.print(ly, 4);
        ly = new_ly;
    }

    if (new_lz != lz) {
        Serial.print("\tlz");
        Serial.print(lz, 4);
        lz = new_lz;
    }
    #endif

    /* Display calibration status for each sensor. */
    bno.getCalibration(&sys_stat, &gyro_stat, &accel_stat, &mag_stat);
    Serial.print("\tss");
    Serial.print(sys_stat, DEC);
    Serial.print("\tsg");
    Serial.print(gyro_stat, DEC);
    Serial.print("\tsa");
    Serial.print(accel_stat, DEC);
    Serial.print("\tsm");
    Serial.print(mag_stat, DEC);

    Serial.print('\n');
}

void updateMotor()
{
    Serial.print("motor\tt");
    Serial.print(millis());

    Serial.print("\ts");
    Serial.print(motorB.getSpeed(), 8);

    Serial.print("\tp");
    Serial.print(motorB.getPosition(), 8);

    if (prev_command != motorB.getCurrentCommand()) {
        Serial.print("\to");
        Serial.print(motorB.getCurrentCommand());
        prev_command = motorB.getCurrentCommand();
    }

    if (prev_commanded_speed != motorB.getCommandedSpeed()) {
        Serial.print("\tx");
        Serial.print(motorB.getCommandedSpeed());
        prev_commanded_speed = motorB.getCommandedSpeed();
    }

    Serial.print('\n');

    motorB.update();
}

void print_int64(int64_t value)
{
    int32_t part1 = value >> 32;
    int32_t part2 = value & 0xffffffff;
    Serial.print(part1);
    Serial.print("|");
    Serial.print(part2);
}


void setup() {
    // manager.begin();
    Serial.begin(115200);
    motorB.begin();

    manager.writeHello();

    #ifdef USE_CALIBRATION
    initImuCalibration();
    #else
    initImu();
    #endif

    manager.writeReady();
}

void loop() {
    if (manager.available()) {
        int status = manager.readSerial();
        String command = manager.getCommand();

        if (status == 1)  {  // start event
            motorB.reset();
        }
        else if (status == 2)  { // stop event
            motorB.reset();
        }
        else if (status == 0)  // user command
        {
            if (command.equals("clear")) {
                clearEeprom();
            }

            if (command.charAt(0) == 'r') {
                motorB.reset();
            }
            else if (command.charAt(0) == 'i') {
                if (command.charAt(1) == '0') {
                    imp_controller_enabled = false;
                    feedforward_controller_enabled = false;
                }
                else {
                    imp_controller_enabled = true;
                    feedforward_controller_enabled = false;

                    selected_imu_axis = command.charAt(1);
                }
            }
            else if (command.charAt(0) == 'f') {
                if (command.charAt(1) == '0') {
                    imp_controller_enabled = false;
                    feedforward_controller_enabled = false;
                }
                else {
                    feedforward_controller_enabled = true;
                    imp_controller_enabled = false;

                    selected_imu_axis = command.charAt(1);
                    feedforward_Kp = command.substring(2).toDouble();
                }
            }
            else if (command.charAt(0) == 's') {
                if (command.charAt(1) == '|') {
                    motorB.pidEnabled = false;
                }
                else {
                    if (!motorB.pidEnabled) {
                        motorB.pidEnabled = true;
                    }
                    motorB.setSpeed(command.substring(1).toDouble());
                }
            }
            else if (command.charAt(0) == 'd') {
                motorB.pidEnabled = false;
                motorB.setMotorRaw(command.substring(1).toInt());
            }
            else if (command.charAt(0) == 'k') {
                switch(command.charAt(1)) {
                    case 'p': motorB.Kp = command.substring(2).toDouble(); break;
                    case 'i': motorB.Ki = command.substring(2).toDouble(); break;
                    case 'd': motorB.Kd = command.substring(2).toDouble(); break;
                }
            }
        }
    }

    if (!manager.isPaused()) {
        current_time = millis();
        if (current_time < imu_timer) {
            imu_timer = current_time;
        }
        if (current_time - imu_timer > BNO055_SAMPLERATE_DELAY_MS) {
            updateIMU();
            imu_timer = current_time;
        }

        manager.writeTime();
        updateMotor();

        if (imp_controller_enabled) {
            switch (selected_imu_axis) {
                case 'x': command_controller_speed = updateIMPcontroller(motorB.getSpeed(), x_ang_vel); break;
                case 'y': command_controller_speed = updateIMPcontroller(motorB.getSpeed(), y_ang_vel); break;
                case 'z': command_controller_speed = updateIMPcontroller(motorB.getSpeed(), z_ang_vel); break;
            }
            motorB.setSpeed(command_controller_speed);
        }
        else if (feedforward_controller_enabled) {
            switch (selected_imu_axis) {
                case 'x': command_controller_speed = feedforward(x_ang_vel); break;
                case 'y': command_controller_speed = feedforward(y_ang_vel); break;
                case 'z': command_controller_speed = feedforward(z_ang_vel); break;
            }
            motorB.setSpeed(command_controller_speed);        }
    }
}
