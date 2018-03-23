#include <Arduino.h>

#define DEFAULT_RATE 115200
#define LED13 13
#define PACKET_END '\n'

class SerialManager {
public:
    SerialManager(String whoiam);
    void begin();
    int readSerial();
    String getCommand();
    bool isPaused();

    void changeBaud(int newBaud);
    bool available();

    bool unpause();
    bool pause();

    void writeWhoiam();
    void writeInit();
    void setInitData(String initData);

private:
    String _command;
    String _whoiam;
    String _initPacket;
    bool _paused;
};
