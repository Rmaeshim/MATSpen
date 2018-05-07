#include <Arduino.h>

#define BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE 4
#define ANG_V_ZERO_FREQUENCY_BUFFER_MICRO_S 5000

class BNO055AngVelContainer {
public:
    BNO055AngVelContainer();
    double computeAvg(double new_val);
    void reset();
    double getFrequency();

private:
    float deltaBuffer[BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE];
    short timeBuffer[BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE];
    double frequencyBuffer[BNO055_ANG_VEL_CONTAINER_BUFFER_SIZE];

    bool bufferFilledOnce;
    double prevVal;
    uint32_t prevTime;
    size_t bufferIndex;
    double deltaRollingTotal;
    long timeRollingTotal;

    size_t angVbufferIndex;
    double currentAngV;
    uint32_t angVtimeInterval;
    double prevAngV;
    double frequency;
    uint32_t prevNodeTime;
};
