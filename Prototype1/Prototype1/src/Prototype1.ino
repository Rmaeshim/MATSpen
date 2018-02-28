/*
*  Simple HTTP get webclient test
*/

#include <ESP8266WiFi.h>

#include <BNO055_lib.cpp>
#include <Atlasbuggy.h>

Atlasbuggy robot = Atlasbuggy("BNO055-IMU");

void setup() {
    robot.begin();
    initIMU();
}

void loop()
{
    if (robot.available())
    {
        int status = robot.readSerial();
//        String command = robot.getCommand();
    }

    if (!robot.isPaused()) {
        updateIMU();

        // 100Hz update rate for imu
        delay(10);
    }
}
