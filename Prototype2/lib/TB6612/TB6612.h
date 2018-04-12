#include <Encoder.h>

#define TB6612_MOTOR_ENCODER_PIN_1 2
#define TB6612_MOTOR_ENCODER_PIN_2 3
#define TB6612_PWM_MOTOR_PIN_A 5
#define TB6612_MOTOR_STANDBY_PIN 6
#define TB6612_MOTOR_DIRECTION_PIN_1 7
#define TB6612_MOTOR_DIRECTION_PIN_2 8
#define TB6612_POSITION_BUFFER_SIZE 20

class TB6612
{
    public:
        TB6612(double counts_per_rotation, double gear_ratio, double max_speed, double Kp, double Ki, double Kd);
        TB6612(double counts_per_rotation, double gear_ratio, double max_speed);

        void begin();
        void reset();
        void standby();
        void wakeup();
        bool isAwake();

        void setMotorRaw(int speed);
        void setSpeed(double rps);
        double getPosition();
        double getSpeed();
        int getCurrentCommand();
        double getCommandedSpeed();

        void update();

        double Kp, Ki, Kd;
        bool pidEnabled;

    private:
        double motorTickConversion;
        double motorPosRad;
        int currentMotorCommand;
        double currentMotorSpeed;
        bool motorIsAwake;

        uint32_t prevTime;
        long prevMotorPos;

        Encoder* motorEncoder;

        short motorDeltaPositionBuffer[TB6612_POSITION_BUFFER_SIZE];
        short timeBuffer[TB6612_POSITION_BUFFER_SIZE];

        size_t positionBufferIndex;
        long motorDeltaPositionRollingTotal;
        long timeRollingTotal;

        void clearBuffers();
        void clearVariables();

        double pidSpeedSetPoint;
        int openLoopSetPoint;
        double openLoopK;
        double pidPrevError;
        double pidSumError;
        uint32_t prevPidTimer = 0;
        uint32_t pidDelay;  // microseconds
};
