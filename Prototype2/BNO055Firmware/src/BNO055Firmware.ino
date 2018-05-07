
#include <SerialManager.h>
#include <TB6612.h>
#include <BNO055Manager.h>

SerialManager manager("BNO055-IMU");

uint32_t imu_timer = 0;
uint32_t current_time = 0;

TB6612 motorB(12.0, 75.81, 6.4, 5, 7, 8, 2, 3);  // 75:1
int prev_command = 0;
double prev_commanded_speed = 0.0;

#define IMP_CONST_LEN 3

char selected_imu_axis = 'x';
bool imp_controller_enabled = false;
bool feedforward_controller_enabled = false;
double command_controller_speed = 0.0;

double imp_A[IMP_CONST_LEN] = {1.0012, -1.8398, 0.9988};
double imp_B[IMP_CONST_LEN] = {1.0000, -1.8398, 1.0000};
double imp_xn[IMP_CONST_LEN] = {0.0, 0.0, 0.0};
double imp_yn[IMP_CONST_LEN] = {0.0, 0.0, 0.0};
size_t imp_current_index = 0;

double feedforward_Kp = 1.0;
double imp_Kp = 1.0;

double updateIMPcontroller(double current_error_signal)
{
    // y(n) = b(1) / a(1) * x(n) + b(2) / a(1) * x(n - 1) + b(3) / a(1) * x(n - 2)
    //                           - a(2) / a(1) * y(n - 1) - a(3) / a(1) * y(n - 2)

    double current_motor_output = imp_B[0] / imp_A[0] * imp_xn[imp_current_index];

    size_t buffer_i = 0;
    size_t i;
    for (i = 1; i < IMP_CONST_LEN; i++) {
        buffer_i = (imp_current_index + IMP_CONST_LEN - i) % IMP_CONST_LEN;
        current_motor_output += imp_B[i] / imp_A[0] * imp_xn[buffer_i];
    }

    buffer_i = 0;
    for (i = 1; i < IMP_CONST_LEN; i++) {
        buffer_i = (imp_current_index + IMP_CONST_LEN - i) % IMP_CONST_LEN;
        current_motor_output -= imp_A[i] / imp_A[0] * imp_yn[buffer_i];
    }

    imp_xn[imp_current_index] = current_error_signal;
    imp_yn[imp_current_index] = current_motor_output;

    imp_current_index++;
    if (imp_current_index >= IMP_CONST_LEN) {
        imp_current_index = 0;
    }

    // return current_error_signal + imp_Kp * current_motor_output;
    return imp_Kp * current_motor_output;
}


void updateMotor()
{
    Serial.print("motor\tt");
    Serial.print(millis());

    Serial.print("\ts");
    Serial.print(motorB.getSpeed(), 8);

    Serial.print("\tp");
    Serial.print(motorB.getPosition(), 8);

    if (prev_command != motorB.getCurrentCommand()) {
        Serial.print("\to");
        Serial.print(motorB.getCurrentCommand());
        prev_command = motorB.getCurrentCommand();
    }

    if (prev_commanded_speed != motorB.getCommandedSpeed()) {
        Serial.print("\tx");
        Serial.print(motorB.getCommandedSpeed());
        prev_commanded_speed = motorB.getCommandedSpeed();
    }

    Serial.print('\n');

    motorB.update();
}

void print_int64(int64_t value)
{
    int32_t part1 = value >> 32;
    int32_t part2 = value & 0xffffffff;
    Serial.print(part1);
    Serial.print("|");
    Serial.print(part2);
}


void setup() {
    // manager.begin();
    Serial.begin(115200);
    motorB.begin();

    manager.writeHello();

    #ifdef USE_CALIBRATION
    initImuCalibration();
    #else
    initImu();
    #endif

    manager.writeReady();
}

void loop() {
    if (manager.available()) {
        int status = manager.readSerial();
        String command = manager.getCommand();

        if (status == 1)  {  // start event
            motorB.reset();
        }
        else if (status == 2)  { // stop event
            motorB.reset();
        }
        else if (status == 0)  // user command
        {
            if (command.equals("clear")) {
                clearEeprom();
            }

            if (command.charAt(0) == 'r') {
                motorB.reset();
            }
            else if (command.charAt(0) == 's') {
                if (command.charAt(1) == '|') {
                    motorB.pidEnabled = false;
                }
                else {
                    motorB.setSpeed(command.substring(1).toDouble());
                }
            }
            else if (command.charAt(0) == 'c') {
                if (command.charAt(1) == '0') {
                    imp_controller_enabled = false;
                }
                else if (command.charAt(1) == '1') {
                    selected_imu_axis = command.charAt(2);
                    if (command.charAt(3) == 'i') {
                        imp_controller_enabled = true;
                        imp_Kp = command.substring(4).toDouble();
                    }
                    else if (command.charAt(3) == 'f') {
                        feedforward_controller_enabled = true;
                        feedforward_Kp = command.substring(4).toDouble();
                    }
                }
            }
            else if (command.charAt(0) == 'd') {
                motorB.pidEnabled = false;
                motorB.setMotorRaw(command.substring(1).toInt());
            }
            else if (command.charAt(0) == 'k') {
                switch(command.charAt(1)) {
                    case 'p': motorB.Kp = command.substring(2).toDouble(); break;
                    case 'i': motorB.Ki = command.substring(2).toDouble(); break;
                    case 'd': motorB.Kd = command.substring(2).toDouble(); break;
                }
            }
        }
    }

    if (!manager.isPaused()) {
        current_time = millis();
        if (current_time < imu_timer) {
            imu_timer = current_time;
        }
        if (current_time - imu_timer > BNO055_SAMPLERATE_DELAY_MS) {
            updateIMU();
            imu_timer = current_time;
        }

        manager.writeTime();
        updateMotor();


        if (imp_controller_enabled) {
            switch (selected_imu_axis) {
                case 'x': command_controller_speed = updateIMPcontroller(-get_x_ang_vel()); break;
                case 'y': command_controller_speed = updateIMPcontroller(-get_y_ang_vel()); break;
                case 'z': command_controller_speed = updateIMPcontroller(-get_z_ang_vel()); break;
            }
            motorB.setSpeed(command_controller_speed);
        }
        else if (feedforward_controller_enabled) {
            switch (selected_imu_axis) {
                case 'x': command_controller_speed = -feedforward_Kp * get_x_ang_vel(); break;
                case 'y': command_controller_speed = -feedforward_Kp * get_y_ang_vel(); break;
                case 'z': command_controller_speed = -feedforward_Kp * get_z_ang_vel(); break;
            }
            motorB.setSpeed(command_controller_speed);
        }
    }
}
