#include <Arduino.h>

#define BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE 4

class BNO055AngVelContainer {
public:
    BNO055AngVelContainer();
    double computeAvg(double new_val);

private:
    float deltaBuffer[BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE];
    short timeBuffer[BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE];

    bool bufferFilledOnce;
    double prevVal;
    uint32_t prevTime;
    size_t bufferIndex;
    double deltaRollingTotal;
    long timeRollingTotal;

};
