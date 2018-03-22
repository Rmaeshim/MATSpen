
#include <TB6612.h>
#include <SerialManager.h>

SerialManager manager("tremor-generator");

TB6612 motor;

void setup() {
    motor.begin();
    manager.begin();
}

void loop()
{
    if (manager.available()) {
        int status = manager.readSerial();
        if (status == -1) return;

        String command = manager.getCommand();

        if (status == 1) {  // start event

        }
        else if (status == 0) {  // user command
            if (manager.getCommand().charAt(0) == 'r') {
                motor.reset();

                while (abs(motor.getSpeed()) > 0.05) {  // wait for the motor to stop spinning
                    Serial.println(motor.getSpeed());
                }
            }
            else if (command.charAt(0) == 's') {
                motor.setMotorRaw(command.substring(1).toInt());
            }
        }
    }
    if (!manager.isPaused()) {

        double speed = motor.getSpeed();
        double position = motor.getPosition();

        if (abs(speed) > 0.0)
        {
            Serial.print("motor\tt");
            Serial.print(millis());

            Serial.print("\ts");
            Serial.print(speed);

            Serial.print("\tp");
            Serial.print(position);
            Serial.print('\n');
        }

        delay(1);
    }
}
