/* Encoder Library - Basic Example
* http://www.pjrc.com/teensy/td_libs_Encoder.html
*
* This example code is in the public domain.
*/

#include <PIDAutotuner.h>
#include <Encoder.h>

class TB6612
{
    public:
        #define motEncPin1 2
        #define motEncPin2 3
        #define pwmMotorPinA 5
        #define motorStandbyPin 6
        #define dirMotorPin1 7
        #define dirMotorPin2 8

        TB6612() {
            motorTickConversion = 12.0 * 75.81;
            motorPosRad = 0.0;
            speed_timer = 0;
            currentMotorSpeed = 0;
            prevMotorPosition = -1;

            motorEncoder = new Encoder(motEncPin1, motEncPin2);
        }

        void begin()
        {
            pinMode(pwmMotorPinA, OUTPUT);
            pinMode(motorStandbyPin, OUTPUT);
            pinMode(dirMotorPin1, OUTPUT);
            pinMode(dirMotorPin2, OUTPUT);

            digitalWrite(motorStandbyPin, LOW);
        }

        void reset() {
            motorEncoder->write(0);

            motorPosRad = 0.0;
            speed_timer = 0;
            currentMotorSpeed = 0;
            prevMotorPosition = -1;
            setMotorRaw(0);
        }

        void setMotorRaw(int speed)
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
        };

        double getPosition()
        {
            long motorPosition = motorEncoder->read();
            return (double)motorPosition / motorTickConversion * 2 * PI;
        }

        double getSpeed()
        {
            long motorPosition = motorEncoder->read();

            if (prevMotorPosition != motorPosition)
            {
                prevMotorPosition = motorPosition;

                uint32_t current_time = micros();
                if (speed_timer > current_time) {  // if timer loops, reset timer
                    speed_timer = current_time;
                    return 0.0;
                }
                double dt = (current_time - speed_timer) / 1E6;
                speed_timer = current_time;

                double newMotorPosRad = (double)motorPosition / motorTickConversion * 2 * PI;
                double deltaMotorPos = newMotorPosRad - motorPosRad;
                motorPosRad = newMotorPosRad;

                return deltaMotorPos / dt;
            }

            return 0.0;
        }

    private:
        double motorTickConversion;
        double motorPosRad;
        int currentMotorSpeed;
        uint32_t speed_timer;

        Encoder* motorEncoder;
        long prevMotorPosition;
};

double motor_speed_setpoint, motor_input;
int motor_output;

double Kp=1.0, Ki=0.0, Kd=0.0;

double prev_error = 0.0;
double sum_error = 0.0;
uint32_t pid_timer = 0;

TB6612 motor;

void computePID()
{
    uint32_t current_pid_timer = millis();
    double dt = (double)(current_pid_timer - pid_timer) / 1000.0;
    double error = motor_speed_setpoint - motor_input;
    double d_error = (error - prev_error) / dt;
    double i_error = sum_error * dt;

    motor_output = (int)(Kp * error + Ki * i_error + Kd * d_error);
    if (motor_output > 255) {
        motor_output = 255;
    }
    if (motor_output < -255) {
        motor_output = -255;
    }

    prev_error = error;
    sum_error += error;
    pid_timer = current_pid_timer;
}

void autotunePID(double targetInputValue, double loopInterval, int tuningCycles) {

    PIDAutotuner tuner = PIDAutotuner();

    // Set the target value to tune to
    // This will depend on what you are tuning. This should be set to a value within
    // the usual range of the setpoint. For low-inertia systems, values at the lower
    // end of this range usually give better results. For anything else, start with a
    // value at the middle of the range.
    tuner.setTargetInputValue(targetInputValue);

    // Set the loop interval in microseconds
    // This must be the same as the interval the PID control loop will run at
    tuner.setLoopInterval(loopInterval);

    tuner.setTuningCycles(tuningCycles);

    // Set the output range
    // These are the maximum and minimum possible output values of whatever you are
    // using to control the system (analogWrite is 0-255)
    tuner.setOutputRange(-255, 255);

    // Set the Ziegler-Nichols tuning mode
    // Set it to either PIDAutotuner::znModeBasicPID, PIDAutotuner::znModeLessOvershoot,
    // or PIDAutotuner::znModeNoOvershoot. Test with znModeBasicPID first, but if there
    // is too much overshoot you can try the others.
    tuner.setZNMode(PIDAutotuner::znModeBasicPID);

    // This must be called immediately before the tuning loop
    tuner.startTuningLoop();

    // Run a loop until tuner.isFinished() returns true
    long microseconds;
    while (!tuner.isFinished()) {

        // This loop must run at the same speed as the PID control loop being tuned
        long prevMicroseconds = microseconds;
        microseconds = micros();

        // Get input value here (temperature, encoder position, velocity, etc)
        double input = motor.getSpeed();

        // Call tunePID() with the input value
        double output = tuner.tunePID(input);

        // Set the output - tunePid() will return values within the range configured
        // by setOutputRange(). Don't change the value or the tuning results will be
        // incorrect.
        motor.setMotorRaw((int)output);

        // This loop must run at the same speed as the PID control loop being tuned
        while (micros() - microseconds < loopInterval) delayMicroseconds(1);

        // Serial.print("tuning... setpoint: ");
        // Serial.print(targetInputValue);
        // Serial.print("\t input: ");
        // Serial.print(input);
        // Serial.print("\t output: ");
        // Serial.println(output);
    }

    // Turn the output off here.
    motor.setMotorRaw(0);

    // Get PID gains - set your PID controller's gains to these
    Kp = tuner.getKp();
    Ki = tuner.getKi();
    Kd = tuner.getKd();

    Serial.print("Kp: "); Serial.print(Kp);
    Serial.print(", Ki: "); Serial.print(Ki);
    Serial.print(", Kd: "); Serial.println(Kd);
}


void setup() {
    Serial.begin(9600);

    motor.begin();

    // autotunePID(20.0, 1000.0, 50);
}


String command;


void loop()
{
    if (Serial.available()) {
        command = Serial.readStringUntil('\n');
        if (command.charAt(0) == 'r') {
            Serial.println("resetting");
            motor.reset();

            motor_speed_setpoint = 0.0;
            motor_input = 0.0;
            motor_output = 0;
            prev_error = 0.0;
            sum_error = 0.0;
            Serial.println(motor.getSpeed());
            while (abs(motor.getSpeed()) > 0.5) {
                Serial.println(motor.getSpeed());
            }
            delay(500);
        }
        else if (command.charAt(0) == 's') {
            while(1);
        }
        else if (command.charAt(0) == 'k') {
            switch(command.charAt(1)) {
                case 'p': Kp = command.substring(2).toDouble(); break;
                case 'i': Ki = command.substring(2).toDouble(); break;
                case 'd': Kd = command.substring(2).toDouble(); break;
            }
            Serial.print("Kp: "); Serial.print(Kp);
            Serial.print(", Ki: "); Serial.print(Ki);
            Serial.print(", Kd: "); Serial.println(Kd);
        }
        else {
            motor_speed_setpoint = command.toDouble();
        }
    }

    motor_input = motor.getSpeed();
    computePID();
    motor.setMotorRaw(motor_output);

    Serial.print("setpoint: ");
    Serial.print(motor_speed_setpoint);
    Serial.print("\t input: ");
    Serial.print(motor_input);
    Serial.print("\t output: ");
    Serial.println(motor_output);

    delay(1);
}
