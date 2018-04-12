
#include <SerialManager.h>
// #define DEBUG

const unsigned long DEFAULT_TIME = 1357041600; // Jan 1 2013


SerialManager::SerialManager(String whoiam)
{
    _command = "";
    _whoiam = whoiam;
    _initPacket = "";
    _paused = true;
    _arduinoPrevTime = 0;
    _overflowCount = 0;
}

void SerialManager::setInitData(String initData) {
    _initPacket = initData;
}


int SerialManager::readSerial()
{
    if (_paused) {
        delay(100);  // minimize activity while paused
    }
    _command = Serial.readStringUntil('\n');
    #ifdef DEBUG
    Serial.println(_command);
    #endif

    if (_command.charAt(0) == '~')
    {
        unsigned long new_time;
        switch (_command.charAt(1)) {
            case '>':  // start command
                #ifdef DEBUG
                Serial.println("start command received");
                Serial.print("_paused is ");
                Serial.println(!_paused);
                #endif

                if (_command.length() > 2) {
                    new_time = _command.substring(2).toInt();
                    if (new_time >= DEFAULT_TIME) { // check the integer is a valid time (greater than Jan 1 2013)
                        setTime(new_time); // Sync Arduino clock to the time received on the serial port
                    }
                }
                if (unpause()) return 1;
                else return -1;
            case '<':  // stop command
                #ifdef DEBUG
                Serial.println("stop command received");
                Serial.print("_paused is ");
                Serial.println(!_paused);
                #endif
                if (pause()) return 2;
                else return -1;
            case '|':  // get initialization data command
                #ifdef DEBUG
                Serial.println("init command received");
                #endif
                writeInit();
                return 3;
            case '?':  // get board ID command
                #ifdef DEBUG
                Serial.println("whoiam command received");
                #endif
                writeWhoiam();
                return 4;
        }
    }
    else {
        if (!_paused) return 0;
    }
    return -1;
}

void SerialManager::changeBaud(int newBaud)
{
    #ifdef DEBUG
    Serial.println("changing baud");
    #endif
    delay(50);
    Serial.end();
    delay(50);
    Serial.begin(newBaud);
}


void SerialManager::writeWhoiam()
{
    Serial.print("~iam");
    Serial.print(_whoiam);
    Serial.print(PACKET_END);
}

void SerialManager::writeInit()
{
    Serial.print("~init:");
    Serial.print(_initPacket);
    Serial.print(PACKET_END);
}

void SerialManager::writeTime()
{
    uint32_t current_time = micros();
    if (current_time < _arduinoPrevTime) {
        _overflowCount++;
    }
    Serial.print("~ct:");

    if (_overflowCount > 0) {
        Serial.print(_overflowCount);
        Serial.print(':');
    }
    Serial.print(current_time);
    Serial.print(PACKET_END);

    _arduinoPrevTime = current_time;
}



String SerialManager::getCommand() {
    return _command;
}

bool SerialManager::isPaused() {
    return _paused;
}

bool SerialManager::unpause()
{
    if (_paused) {
        _paused = false;
        return true;
    }
    else {
        return false;
    }
}

bool SerialManager::pause()
{
    if (!_paused) {
        Serial.print("\n~stopping\n");
        _paused = true;
        return true;
    }
    else {
        return false;
    }
}
