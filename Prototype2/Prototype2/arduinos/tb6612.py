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
        self.millis_time = 0.0
        self.arduino_time = 0.0
        self.motor_output = 0
        self.commanded_speed = 0.0

        self.auto_serialize()


class TB6612(Arduino):
    def __init__(self):
        self.set_logger(write=True)
        super(TB6612, self).__init__("tremor-generator")

        self.prev_message = TB6612Message(0, time.time())
        self.current_message = self.prev_message

        self.current_commanded_speed = 0.0

    async def loop(self):
        counter = 0
        self.start()

        while self.device_active():
            while not self.empty():
                packet_time, arduino_times, packets = self.read()

                for arduino_time, packet in zip(arduino_times, packets):
                    message = self.parse_packet(packet_time, arduino_time, packet, counter)
                    if message is not None:
                        self.log_to_buffer(packet_time, message)
                        self.current_message = message
                        await self.broadcast(message)
                        counter += 1

            await asyncio.sleep(0.0)

    def parse_packet(self, packet_time, arduino_time, packet, packet_num):
        data = packet.split("\t")
        if data.pop(0) != 'motor':
            self.logger.info("TB6612 said: %s" % str(packet))
            return

        message = self.prev_message.copy()
        message.timestamp = time.time()
        message.n = packet_num
        message.packet_time = packet_time
        message.arduino_time = arduino_time

        segment = ""
        try:
            for segment in data:
                if len(segment) > 0:
                    if segment[0] == "t":
                        message.millis_time = float(segment[1:]) / 1000

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
        print("setting speed to %s rps" % speed_rps)
        self.current_commanded_speed = speed_rps
        self.write("s%s" % speed_rps)

    def command_raw(self, motor_command):
        print("setting command to %s" % motor_command)
        self.current_commanded_speed = 0.0
        self.write("d%s" % int(motor_command))

    def command_function(self, t, speed_hz):
        if type(t) == list or type(t) == tuple:
            assert len(t) - 1 == len(speed_hz)
        else:
            t = float(t)

        pause_time = time.time()
        for index in range(0, len(speed_hz)):
            if type(t) == float:
                dt = t / len(speed_hz)
            else:
                t0 = t[index]
                t1 = t[index + 1]

                dt = t1 - t0

            pause_time += dt
            self.pause_command(pause_time, relative_time=False)
            self.command_motor(speed_hz[index])

    def power_off_motor(self):
        self.current_commanded_speed = 0.0
        self.write("d|")

    def set_pid_constants(self, kp, ki, kd):
        self.current_commanded_speed = 0.0
        self.write("kp%s" % kp)
        self.write("ki%s" % ki)
        self.write("kd%s" % kd)
        self.write("r")
