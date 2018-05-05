#include "BNO055AngVelContainer.h"

BNO055AngVelContainer::BNO055AngVelContainer()
{
    bufferIndex = 0;
    deltaRollingTotal = 0.0;
    timeRollingTotal = 0;
    prevVal = 0.0;
    prevTime = 0;
    bufferFilledOnce = false;

    for (size_t i = 0; i < BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE; i++) {
        deltaBuffer[i] = 0;
        timeBuffer[i] = 0;
    }
}

double BNO055AngVelContainer::computeAvg(double new_val)
{
    uint32_t current_time = micros();
    if (prevTime > current_time) {  // if timer loops, reset timer
        prevTime = current_time;
        return 0.0;
    }

    short dt = (short)(current_time - prevTime);
    prevTime = current_time;

    double delta = new_val - prevVal;
    prevVal = new_val;

    deltaRollingTotal -= deltaBuffer[bufferIndex];
    deltaBuffer[bufferIndex] = delta;
    deltaRollingTotal += delta;

    timeRollingTotal -= timeBuffer[bufferIndex];
    timeBuffer[bufferIndex] = dt;
    timeRollingTotal += dt;

    bufferIndex++;
    if (bufferIndex >= BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE) {
        bufferIndex = 0;
        bufferFilledOnce = true;
    }

    if (timeRollingTotal > 0 && bufferFilledOnce) {
        double timeRollingTotalSec = (double)timeRollingTotal / 1E6;

        return deltaRollingTotal / timeRollingTotalSec;
    }
    else {
        return 0.0;
    }
}
