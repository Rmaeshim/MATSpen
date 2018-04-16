
#include <TB6612.h>
#include <SerialManager.h>

SerialManager manager("tremor-generator");

// TB6612 motor(12.0, 75.81, 6.4, 8.55, 3.2, 0.39);  // 75:1
TB6612 motor(12.0, 51.45, 6.7, 8.55, 3.2, 0.39);  // 50:1

void setup() {
    motor.begin();
    Serial.begin(115200);

    manager.writeHello();
    manager.writeReady();
}

int prev_command = 0;
double prev_commanded_speed = 0.0;
void loop()
{
    if (manager.available()) {
        int status = manager.readSerial();
        if (status == -1) return;

        String command = manager.getCommand();

        if (status == 1) {  // start event
            motor.reset();
        }
        else if (status == 2) {  // stop event
            motor.reset();
        }
        else if (status == 0) {  // user command
            if (manager.getCommand().charAt(0) == 'r') {
                motor.reset();
            }
            else if (command.charAt(0) == 's') {
                if (command.charAt(1) == '|') {
                    motor.pidEnabled = false;
                }
                else {
                    if (!motor.pidEnabled) {
                        motor.pidEnabled = true;
                    }
                    motor.setSpeed(command.substring(1).toDouble());
                }
            }
            else if (command.charAt(0) == 'd') {
                if (command.charAt(1) == '|') {
                    motor.standby();
                }
                else {
                    motor.pidEnabled = false;
                    if (!motor.isAwake()) {
                        motor.wakeup();
                    }
                    motor.setMotorRaw(command.substring(1).toInt());
                }

            }
            else if (command.charAt(0) == 'k') {
                switch(command.charAt(1)) {
                    case 'p': motor.Kp = command.substring(2).toDouble(); break;
                    case 'i': motor.Ki = command.substring(2).toDouble(); break;
                    case 'd': motor.Kd = command.substring(2).toDouble(); break;
                }
            }
        }
    }
    if (!manager.isPaused()) {
        Serial.print("motor\tt");
        Serial.print(millis());

        Serial.print("\ts");
        Serial.print(motor.getSpeed(), 8);

        Serial.print("\tp");
        Serial.print(motor.getPosition(), 8);

        if (prev_command != motor.getCurrentCommand()) {
            Serial.print("\to");
            Serial.print(motor.getCurrentCommand());
            prev_command = motor.getCurrentCommand();
        }

        if (prev_commanded_speed != motor.getCommandedSpeed()) {
            Serial.print("\tx");
            Serial.print(motor.getCommandedSpeed());
            prev_commanded_speed = motor.getCommandedSpeed();
        }

        Serial.print('\n');

        motor.update();
        delay(1);
    }
}
