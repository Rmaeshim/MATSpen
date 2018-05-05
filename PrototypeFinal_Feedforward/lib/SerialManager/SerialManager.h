#ifndef _SERIAL_MANAGER_H_
#define _SERIAL_MANAGER_H_

#include <Arduino.h>
#include <TimeLib.h>

#define PACKET_END '\n'

class SerialManager {
public:
    SerialManager(String whoiam);
    bool available();
    int readSerial();
    String getCommand();
    bool isPaused();

    void changeBaud(int newBaud);

    bool unpause();
    bool pause();

    void setInitData(String initData);
    void writeHello();
    void writeReady();

    void writeTime();
private:
    String _command;
    String _whoiam;
    String _initPacket;
    bool _paused;

    void writeWhoiam();
    void writeInit();

    void printInt64(int64_t value);
    void printUInt64(uint64_t value);

    uint32_t _arduinoPrevTime;
    uint32_t _overflowCount;
    uint64_t _sequence_num;
    char _timePrintBuffer[32];
};

#endif  // _SERIAL_MANAGER_H_
