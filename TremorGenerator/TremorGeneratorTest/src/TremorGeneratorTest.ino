/* Encoder Library - Basic Example
* http://www.pjrc.com/teensy/td_libs_Encoder.html
*
* This example code is in the public domain.
*/

#include <Encoder.h>

#define motEncPin1 2
#define motEncPin2 3
#define pwmMotorPinA 5
#define motorStandbyPin 6
#define dirMotorPin1 7
#define dirMotorPin2 8

double motorTickConversion = 12.0 * 75.81;

double motorPosRad = 0.0;
uint32_t speed_timer = 0;


// Change these two numbers to the pins connected to your encoder.
//   Best Performance: both pins have interrupt capability
//   Good Performance: only the first pin has interrupt capability
//   Low Performance:  neither pin has interrupt capability
Encoder motorEncoder(motEncPin1, motEncPin2);
//   avoid using pins with LEDs attached

int currentMotorSpeed;


void setMotor(int speed)
{
    currentMotorSpeed = speed;
    if (speed > 0) {
        digitalWrite(motorStandbyPin, HIGH);
        digitalWrite(dirMotorPin1, LOW);
        digitalWrite(dirMotorPin2, HIGH);
    }
    else if (speed < 0) {
        digitalWrite(motorStandbyPin, HIGH);
        digitalWrite(dirMotorPin1, HIGH);
        digitalWrite(dirMotorPin2, LOW);

    }
    else {
        digitalWrite(motorStandbyPin, HIGH);
    }

    analogWrite(pwmMotorPinA, abs(speed));
}


void setup() {
    Serial.begin(9600);
    Serial.println("Basic Encoder Test:");

    pinMode(pwmMotorPinA, OUTPUT);
    pinMode(motorStandbyPin, OUTPUT);
    pinMode(dirMotorPin1, OUTPUT);
    pinMode(dirMotorPin2, OUTPUT);

    digitalWrite(motorStandbyPin, LOW);

    // setMotor(255);
}

long prevMotorPosition = -1;

String command;

void loop() {
    if (Serial.available()) {
        command = Serial.readStringUntil('\n');
        if (command.charAt(0) == 'r') {
            motorEncoder.write(0);
        }
        else {
            int motorSpeed = command.toInt();
            setMotor(motorSpeed);
        }
    }

    long motorPosition = motorEncoder.read();

    if (prevMotorPosition != motorPosition)
    {
        uint32_t current_time = micros();
        if (speed_timer > current_time) {  // if timer loops, reset timer
            speed_timer = current_time;
            return;
        }
        double dt = (current_time - speed_timer) / 1E6;
        speed_timer = current_time;

        double newMotorPosRad = (double)motorPosition / motorTickConversion * 2 * PI;
        double deltaMotorPos = newMotorPosRad - motorPosRad;
        motorPosRad = newMotorPosRad;

        double speed = deltaMotorPos / dt;

        // if (motorPosRad > PI / 4) {
        //     setMotor(-255);
        // }
        // if (motorPosRad < 0.0) {
        //     setMotor(255);
        // }

        Serial.print(speed);
        Serial.print(", ");
        Serial.println(motorPosRad);
    }
    prevMotorPosition = motorPosition;

    delay(15);
}
