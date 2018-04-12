#ifndef _SERIAL_MANAGER_H_
#define _SERIAL_MANAGER_H_

#include <Arduino.h>
#include <TimeLib.h>

#define PACKET_END '\n'

class SerialManager {
public:
    SerialManager(String whoiam);
    int readSerial();
    String getCommand();
    bool isPaused();

    void changeBaud(int newBaud);

    bool unpause();
    bool pause();

    void writeWhoiam();
    void writeInit();
    void setInitData(String initData);
    void writeTime();

private:
    String _command;
    String _whoiam;
    String _initPacket;
    bool _paused;
    uint32_t _arduinoPrevTime;
    uint32_t _overflowCount;
    char _timePrintBuffer[32];
    uint32_t fake_time;
    uint32_t debugMicros();
};

#endif  // _SERIAL_MANAGER_H_
