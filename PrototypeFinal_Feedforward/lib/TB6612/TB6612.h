#include <Encoder.h>

#define TB6612_POSITION_BUFFER_SIZE 20

class TB6612
{
    public:
        TB6612(double counts_per_rotation, double gear_ratio, double max_speed,
            int pwm_pin, int dir_pin_1, int dir_pin_2, int enc_pin_1, int enc_pin_2);

        void begin();
        void reset();

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
        int TB6612_MOTOR_ENCODER_PIN_1;
        int TB6612_MOTOR_ENCODER_PIN_2;
        int TB6612_PWM_MOTOR_PIN;
        int TB6612_MOTOR_DIRECTION_PIN_1;
        int TB6612_MOTOR_DIRECTION_PIN_2;

        double motorTickConversion;
        double motorPosRad;
        int currentMotorCommand;
        double currentMotorSpeed;

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
