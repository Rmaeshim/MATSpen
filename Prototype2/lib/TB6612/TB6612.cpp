#include <TB6612.h>

TB6612::TB6612(double counts_per_rotation, double gear_ratio, double max_speed,
    int pwm_pin, int dir_pin_1, int dir_pin_2, int enc_pin_1, int enc_pin_2)
{
    Kp = 1.0;
    Ki = 0.0;
    Kd = 0.0;

    openLoopK = 255.0 / max_speed;
    pidDelay = 5000;

    motorTickConversion = counts_per_rotation * gear_ratio;
    clearVariables();

    TB6612_MOTOR_ENCODER_PIN_1 = enc_pin_1;
    TB6612_MOTOR_ENCODER_PIN_2 = enc_pin_2;
    TB6612_PWM_MOTOR_PIN = pwm_pin;
    TB6612_MOTOR_DIRECTION_PIN_1 = dir_pin_1;
    TB6612_MOTOR_DIRECTION_PIN_2 = dir_pin_2;

    motorEncoder = new Encoder(TB6612_MOTOR_ENCODER_PIN_1, TB6612_MOTOR_ENCODER_PIN_2);
}


void TB6612::begin()
{
    pinMode(TB6612_PWM_MOTOR_PIN, OUTPUT);
    pinMode(TB6612_MOTOR_DIRECTION_PIN_1, OUTPUT);
    pinMode(TB6612_MOTOR_DIRECTION_PIN_2, OUTPUT);
}

void TB6612::reset() {
    setMotorRaw(0);
    delay(50);
    while (abs(getSpeed()) > 0.0);  // wait for the motor to stop spinning
    delay(50);

    clearVariables();
    motorEncoder->write(0);
}

void TB6612::setSpeed(double rps) {
    pidEnabled = true;
    pidSpeedSetPoint = rps;
    openLoopSetPoint = pidSpeedSetPoint * openLoopK;
}

void TB6612::update() {
    if (!pidEnabled) {
        return;
    }

    uint32_t current_time = micros();
    if (prevPidTimer > current_time) {  // if timer loops, reset timer
        prevPidTimer = current_time;
        return;
    }

    if ((current_time - prevPidTimer) < pidDelay) {
        return;
    }

    double dt = (double)(current_time - prevPidTimer) / 1E6;
    double error = pidSpeedSetPoint - getSpeed();
    double d_error = (error - pidPrevError) / dt;
    double i_error = pidSumError * dt;

    int motorOutput = openLoopSetPoint + (int)(Kp * error + Ki * i_error + Kd * d_error);
    if (motorOutput > 255) {
        motorOutput = 255;
    }
    if (motorOutput < -255) {
        motorOutput = -255;
    }
    if (abs(motorOutput) <= 7) {
        motorOutput = 0;
    }

    pidPrevError = error;
    pidSumError += error;
    prevPidTimer = micros();

    setMotorRaw(motorOutput);
}

void TB6612::clearVariables() {
    motorPosRad = 0.0;
    currentMotorCommand = 0;
    currentMotorSpeed = 0.0;
    prevTime = micros();
    prevMotorPos = 0;
    positionBufferIndex = 0;
    motorDeltaPositionRollingTotal = 0;
    timeRollingTotal = 0;
    pidEnabled = false;
    pidSpeedSetPoint = 0.0;
    openLoopSetPoint = 0;
    pidPrevError = 0.0;
    pidSumError = 0.0;
    prevPidTimer = micros();

    clearBuffers();
}

void TB6612::clearBuffers() {
    for (size_t i = 0; i < TB6612_POSITION_BUFFER_SIZE; i++) {
        motorDeltaPositionBuffer[i] = 0;
        timeBuffer[i] = 0;
    }
}

void TB6612::setMotorRaw(int speed)
{
    currentMotorCommand = speed;
    if (speed > 0) {
        digitalWrite(TB6612_MOTOR_DIRECTION_PIN_1, LOW);
        digitalWrite(TB6612_MOTOR_DIRECTION_PIN_2, HIGH);
    }
    else if (speed < 0) {
        digitalWrite(TB6612_MOTOR_DIRECTION_PIN_1, HIGH);
        digitalWrite(TB6612_MOTOR_DIRECTION_PIN_2, LOW);
    }

    speed = abs(speed);
    if (speed > 255) {
        speed = 255;
    }
    analogWrite(TB6612_PWM_MOTOR_PIN, speed);
}

double TB6612::getPosition()
{
    long motorPosition = motorEncoder->read();
    return (double)motorPosition / motorTickConversion * 2 * PI;
}

int TB6612::getCurrentCommand() {
    return currentMotorCommand;
}

double TB6612::getCommandedSpeed() {
    return pidSpeedSetPoint;
}

double TB6612::getSpeed()
{
    uint32_t current_time = micros();
    if (prevTime > current_time) {  // if timer loops, reset timer
        prevTime = current_time;
        return currentMotorSpeed;
    }

    short dt = (short)(current_time - prevTime);
    prevTime = current_time;

    long currentPos = motorEncoder->read();
    short deltaPos = (short)(currentPos - prevMotorPos);
    prevMotorPos = currentPos;

    motorDeltaPositionRollingTotal -= motorDeltaPositionBuffer[positionBufferIndex];
    motorDeltaPositionBuffer[positionBufferIndex] = deltaPos;
    motorDeltaPositionRollingTotal += deltaPos;

    timeRollingTotal -= timeBuffer[positionBufferIndex];
    timeBuffer[positionBufferIndex] = dt;
    timeRollingTotal += dt;

    positionBufferIndex++;
    if (positionBufferIndex >= TB6612_POSITION_BUFFER_SIZE) {
        positionBufferIndex = 0;
    }

    if (timeRollingTotal > 0) {
        double motorDeltaPositionRollingTotalRad = (double)motorDeltaPositionRollingTotal / motorTickConversion;
        double timeRollingTotalSec = (double)timeRollingTotal / 1E6;

        currentMotorSpeed = motorDeltaPositionRollingTotalRad / timeRollingTotalSec;
    }
    else {
        currentMotorSpeed = 0.0;
    }
    return currentMotorSpeed;
}
