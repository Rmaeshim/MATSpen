#include "BNO055AngVelContainer.h"

BNO055AngVelContainer::BNO055AngVelContainer() {
    reset();
}

void BNO055AngVelContainer::reset()
{
    bufferIndex = 0;
    deltaRollingTotal = 0.0;
    timeRollingTotal = 0;
    prevVal = 0.0;
    prevTime = 0;
    bufferFilledOnce = false;

    currentAngV = 0.0;
    prevAngV = 0.0;
    frequency = 0.0;
    angVbufferIndex = 0;

    for (size_t i = 0; i < BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE; i++) {
        deltaBuffer[i] = 0;
        timeBuffer[i] = 0;
    }
}

double BNO055AngVelContainer::getFrequency() {
    return frequency;
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

        currentAngV = deltaRollingTotal / timeRollingTotalSec;

        if (prevAngV < 0 && currentAngV > 0)  {  // detect rising edge
            angVtimeInterval = current_time - prevNodeTime;
            frequency = 1E6 / (double)(angVtimeInterval);
            prevNodeTime = current_time;
        }
        else if (frequency != 0.0 && current_time - prevNodeTime > angVtimeInterval + ANG_V_ZERO_FREQUENCY_BUFFER_MICRO_S) {
            // if no rising edges detected since last peak, reset
            frequency = 0.0;
        }

        prevAngV = currentAngV;
    }
    else {
        currentAngV = 0.0;
    }

    return currentAngV;
}
