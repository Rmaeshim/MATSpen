#ifndef __BNO055_MANAGER_H__
#define __BNO055_MANAGER_H__

#include <Arduino.h>
#include <EEPROM.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include <BNO055AngVelContainer.h>

/* ----------------------- *
* BNO055 global variables *
* ----------------------- */

/* Set the delay between fresh samples */
#define BNO055_SAMPLERATE_DELAY_MS (1)

// #define USE_CALIBRATION

#define INCLUDE_FILTERED_DATA
// #define USE_QUATERNIONS
#define INCLUDE_MAG_DATA
#define INCLUDE_GYRO_DATA
// #define INCLUDE_ACCEL_DATA
#define INCLUDE_LINACCEL_DATA

// Accelerometer & gyroscope only for getting relative orientation, subject to gyro drift
// Adafruit_BNO055 bno = Adafruit_BNO055(0x08); // OPERATION_MODE_IMUPLUS

// Accelerometer & magnetometer only for getting relative orientation
// Adafruit_BNO055 bno = Adafruit_BNO055(0x0a);  // OPERATION_MODE_M4G

// Gets heading only from compass
// Adafruit_BNO055 bno = Adafruit_BNO055(0x09); // OPERATION_MODE_COMPASS

// OPERATION_MODE_NDOF without fast magnetometer calibration
// Adafruit_BNO055 bno = Adafruit_BNO055(OPERATION_MODE_NDOF_FMC_OFF);

double get_x_ang_vel();
double get_y_ang_vel();
double get_z_ang_vel();

void reset_containers();
void displaySensorDetails();
void displaySensorStatus();
void displayCalStatus();
void displaySensorOffsets(const adafruit_bno055_offsets_t &calibData);
void initImuCalibration();
void initImu();
void clearEeprom();
void updateIMU();

#endif  // __BNO055_MANAGER_H__
