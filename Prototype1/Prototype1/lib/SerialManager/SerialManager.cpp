
#include <SerialManager.h>
// #define DEBUG

SerialManager::SerialManager(String whoiam)
{
    _command = "";
    _whoiam = whoiam;
    _initPacket = "";
    _paused = true;
}

void SerialManager::begin()
{
    Serial.begin(DEFAULT_RATE);
    Serial.setTimeout(100);  // 100 ms
    #ifdef DEBUG
    Serial.print("BAUD is ");
    Serial.println(DEFAULT_RATE);
    #endif
}

void SerialManager::setInitData(String initData) {
    _initPacket = initData;
}

bool SerialManager::available() {
    return Serial.available() > 0;
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
        switch (_command.charAt(1)) {
            case '>':  // start command
                if (unpause()) return 1;
                else return -1;
            case '<':  // end command
                if (pause()) return 2;
                else return -1;
            case '|':  // get initialization data command
                writeInit();
                return 3;
            case '?':  // get board ID command
                writeWhoiam();
                return 4;
            default:
                break;
        }
    }
    else {
        if (!_paused) return 0;
        else return -1;
    }
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
    Serial.print("iam");
    Serial.print(_whoiam);
    Serial.print(PACKET_END);
}

void SerialManager::writeInit()
{
    Serial.print("init:");
    Serial.print(_initPacket);
    Serial.print(PACKET_END);
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
        Serial.print("\nstopping\n");
        _paused = true;
        return true;
    }
    else {
        return false;
    }
}
