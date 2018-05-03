
#include <TB6612.h>
#include <SerialManager.h>

#define TB6612_MOTOR_STANDBY_PIN 6

SerialManager manager("tremor-generator");

TB6612 motorA(12.0, 51.45, 6.7, 5, 7, 8, 2, 3);  // 50:1
int prev_command = 0;
double prev_commanded_speed = 0.0;

void standbyMotor() {
    digitalWrite(TB6612_MOTOR_STANDBY_PIN, LOW);
}

void wakeMotor() {
    digitalWrite(TB6612_MOTOR_STANDBY_PIN, HIGH);
}

void setup() {
    motorA.begin();
    Serial.begin(115200);

    pinMode(TB6612_MOTOR_STANDBY_PIN, OUTPUT);

    standbyMotor();

    manager.writeHello();
    manager.writeReady();
}


void loop()
{
    if (manager.available()) {
        int status = manager.readSerial();
        if (status == -1) return;

        String command = manager.getCommand();

        if (status == 1) {  // start event
            motorA.reset();
            wakeMotor();
        }
        else if (status == 2) {  // stop event
            motorA.reset();
            standbyMotor();
        }
        else if (status == 0) {  // user command
            if (command.charAt(0) == 'r') {
                motorA.reset();
            }
            else if (command.charAt(0) == 's') {
                if (command.charAt(1) == '|') {
                    motorA.pidEnabled = false;
                }
                else {
                    if (!motorA.pidEnabled) {
                        motorA.pidEnabled = true;
                    }
                    motorA.setSpeed(command.substring(1).toDouble());
                }
            }
            else if (command.charAt(0) == 'd') {
                motorA.pidEnabled = false;
                motorA.setMotorRaw(command.substring(1).toInt());
            }
            else if (command.charAt(0) == 'k') {
                switch(command.charAt(1)) {
                    case 'p': motorA.Kp = command.substring(2).toDouble(); break;
                    case 'i': motorA.Ki = command.substring(2).toDouble(); break;
                    case 'd': motorA.Kd = command.substring(2).toDouble(); break;
                }
            }
        }
    }
    if (!manager.isPaused()) {
        Serial.print("motor\tt");
        Serial.print(millis());

        Serial.print("\ts");
        Serial.print(motorA.getSpeed(), 8);

        Serial.print("\tp");
        Serial.print(motorA.getPosition(), 8);

        if (prev_command != motorA.getCurrentCommand()) {
            Serial.print("\to");
            Serial.print(motorA.getCurrentCommand());
            prev_command = motorA.getCurrentCommand();
        }

        if (prev_commanded_speed != motorA.getCommandedSpeed()) {
            Serial.print("\tx");
            Serial.print(motorA.getCommandedSpeed());
            prev_commanded_speed = motorA.getCommandedSpeed();
        }

        Serial.print('\n');

        motorA.update();
        delay(1);
    }
}
