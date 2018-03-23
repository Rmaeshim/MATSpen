import time
import asyncio
from atlasbuggy import Message
from atlasbuggy.device.arduino import Arduino


class TB6612Message(Message):
    def __init__(self, n, timestamp=None):
        super(TB6612Message, self).__init__(n, timestamp)

        self.speed = 0.0
        self.position = 0.0
        self.packet_time = 0.0
        self.arduino_time = 0.0
        self.motor_output = 0

        self.auto_serialize()


class TB6612(Arduino):
    def __init__(self):
        super(TB6612, self).__init__("tremor-generator")

        self.prev_message = TB6612Message(0, time.time())
        self.current_message = self.prev_message

    async def loop(self):
        counter = 0
        self.start()
        while self.device_active():
            while not self.empty():
                packet_time, packets = self.read()

                for packet in packets:
                    message = self.parse_packet(packet_time, packet, counter)
                    if message is not None:
                        self.log_to_buffer(packet_time, message)
                        self.current_message = message
                        await self.broadcast(message)
                        counter += 1

            await asyncio.sleep(0.0)

    def parse_packet(self, packet_time, packet, packet_num):
        data = packet.split("\t")
        if data.pop(0) != 'motor':
            self.logger.info("TB6612 said: %s" % str(packet))
            return

        message = self.prev_message.copy()
        message.timestamp = time.time()
        message.n = packet_num
        message.packet_time = packet_time

        segment = ""
        try:
            for segment in data:
                if len(segment) > 0:
                    if segment[0] == "t":
                        message.arduino_time = float(segment[1:]) / 1000

                    elif segment[0] == "s":
                        message.speed = float(segment[1:])

                    elif segment[0] == "p":
                        message.position = float(segment[1:])

                    elif segment[0] == "o":
                        message.motor_output = int(segment[1:])

        except ValueError:
            self.logger.error("Failed to parse: '%s'" % segment)

        self.prev_message = message
        return message

    def command_motor(self, speed_rps):
        self.write("s%s" % speed_rps)

    def command_raw(self, motor_command):
        self.write("d%s" % int(motor_command))

    def power_off_motor(self):
        self.write("d|")

    def set_pid_constants(self, kp, ki, kd):
        self.write("kp%s" % kp)
        self.write("ki%s" % ki)
        self.write("kd%s" % kd)
        self.write("r")

