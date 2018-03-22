#include <Encoder.h>

#define TB6612_MOTOR_ENCODER_PIN_1 2
#define TB6612_MOTOR_ENCODER_PIN_2 3
#define TB6612_PWM_MOTOR_PIN_A 5
#define TB6612_MOTOR_STANDBY_PIN 6
#define TB6612_MOTOR_DIRECTION_PIN_1 7
#define TB6612_MOTOR_DIRECTION_PIN_2 8

class TB6612
{
    public:
        TB6612();

        void begin();
        void reset();
        void setMotorRaw(int speed);
        double getPosition();
        double getSpeed();

    private:
        double motorTickConversion;
        double motorPosRad;
        int currentMotorCommand;
        double currentMotorSpeed;
        uint32_t speed_timer;

        Encoder* motorEncoder;
        long prevMotorPosition;
};
