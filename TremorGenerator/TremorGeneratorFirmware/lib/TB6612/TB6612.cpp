#include <TB6612.h>

TB6612::TB6612()
{
    motorTickConversion = 12.0 * 75.81;
    motorPosRad = 0.0;
    speed_timer = 0;
    currentMotorCommand = 0;
    currentMotorSpeed = 0.0;
    prevMotorPosition = -1;

    motorEncoder = new Encoder(TB6612_MOTOR_ENCODER_PIN_1, TB6612_MOTOR_ENCODER_PIN_2);
}

void TB6612::begin()
{
    pinMode(TB6612_PWM_MOTOR_PIN_A, OUTPUT);
    pinMode(TB6612_MOTOR_STANDBY_PIN, OUTPUT);
    pinMode(TB6612_MOTOR_DIRECTION_PIN_1, OUTPUT);
    pinMode(TB6612_MOTOR_DIRECTION_PIN_2, OUTPUT);

    digitalWrite(TB6612_MOTOR_STANDBY_PIN, LOW);
}

void TB6612::reset() {
    motorEncoder->write(0);

    motorPosRad = 0.0;
    speed_timer = 0;
    currentMotorCommand = 0;
    prevMotorPosition = -1;
    setMotorRaw(0);
}

void TB6612::setMotorRaw(int speed)
{
    currentMotorCommand = speed;
    if (speed > 0) {
        digitalWrite(TB6612_MOTOR_STANDBY_PIN, HIGH);
        digitalWrite(TB6612_MOTOR_DIRECTION_PIN_1, LOW);
        digitalWrite(TB6612_MOTOR_DIRECTION_PIN_2, HIGH);
    }
    else if (speed < 0) {
        digitalWrite(TB6612_MOTOR_STANDBY_PIN, HIGH);
        digitalWrite(TB6612_MOTOR_DIRECTION_PIN_1, HIGH);
        digitalWrite(TB6612_MOTOR_DIRECTION_PIN_2, LOW);

    }
    else {
        digitalWrite(TB6612_MOTOR_STANDBY_PIN, HIGH);
    }

    analogWrite(TB6612_PWM_MOTOR_PIN_A, abs(speed));
}

double TB6612::getPosition()
{
    long motorPosition = motorEncoder->read();
    return (double)motorPosition / motorTickConversion * 2 * PI;
}

double TB6612::getSpeed()
{
    long motorPosition = motorEncoder->read();

    if (prevMotorPosition != motorPosition)
    {
        uint32_t current_time = millis();
        if (speed_timer > current_time) {  // if timer loops, reset timer
            speed_timer = current_time;
            return currentMotorSpeed;
        }

        if ((current_time - speed_timer) > 5 {  // if 5 ms have passed
            prevMotorPosition = motorPosition;

            double dt = (current_time - speed_timer) / 1E3;
            speed_timer = current_time;

            double newMotorPosRad = (double)motorPosition / motorTickConversion * 2 * PI;
            double deltaMotorPos = newMotorPosRad - motorPosRad;
            motorPosRad = newMotorPosRad;

            currentMotorSpeed = deltaMotorPos / dt;
        }

        return currentMotorSpeed;
    }
    else {
        return 0.0;
    }
}
