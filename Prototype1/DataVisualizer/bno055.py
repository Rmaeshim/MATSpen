import re
import time
import math
import asyncio

from atlasbuggy import Message
from atlasbuggy.device import Arduino


class Bno055Vector:
    def __init__(self, name, *vector):
        self.name = name
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.w = 0.0

        if len(vector) >= 1:
            self.x = vector[0]
        if len(vector) >= 2:
            self.y = vector[1]
        if len(vector) >= 3:
            self.z = vector[2]
        if len(vector) >= 4:
            self.w = vector[3]

    def __getitem__(self, item):
        if type(item) == int:
            if item == 0:
                return self.x
            elif item == 1:
                return self.y
            elif item == 2:
                return self.z
            elif item == 3:
                return self.w
        else:
            return self.__dict__[item]

    def __setitem__(self, item, value):
        if type(item) == int:
            if item == 0:
                self.x = value
            elif item == 1:
                self.y = value
            elif item == 2:
                self.z = value
            elif item == 3:
                self.w = value
        else:
            self.__dict__[item] = value

    def get_tuple(self, xyz=True):
        if xyz:
            return self.x, self.y, self.z
        else:
            return self.x, self.y, self.z, self.w


class Bno055Message(Message):
    message_regex = r"Bno055Message\(t: (\d.*), pt: (\d.*), at: (\d.*), n: (\d*), " \
                    r"euler: \(([-\d., ]*)\), " \
                    r"mag: \(([-\d., ]*)\), gyro: \(([-\d., ]*)\), accel: \(([-\d., ]*)\), " \
                    r"linaccel: \(([-\d., ]*)\), quat: \(([-\d., ]*)\), " \
                    r"status; sys: (\d*), a: (\d*), g: (\d*), m: (\d*)\)"

    def __init__(self, timestamp, n=None):
        self.packet_time = 0.0
        self.arduino_time = 0.0
        self.euler = Bno055Vector("euler")
        self.mag = Bno055Vector("mag")
        self.gyro = Bno055Vector("gyro")
        self.accel = Bno055Vector("accel")
        self.linaccel = Bno055Vector("linaccel")
        self.quat = Bno055Vector("quat")

        self.vectors = [self.euler, self.mag, self.gyro, self.accel, self.linaccel, self.quat]

        self.system_status = 0
        self.accel_status = 0
        self.gyro_status = 0
        self.mag_status = 0

        super(Bno055Message, self).__init__(timestamp, n)

    def __str__(self):
        string = "%s(t: %s, pt: %s, at: %s, n: %s, " % (
            self.name, self.timestamp, self.packet_time, self.arduino_time, self.n)
        for vector in self.vectors[:-1]:
            string += "%s: %s, " % (vector.name, vector.get_tuple())

        string += "%s: %s, " % (self.quat.name, self.quat.get_tuple(xyz=False))

        string += "status; sys: %s, a: %s, g: %s, m: %s)" % (
            self.system_status, self.accel_status, self.gyro_status, self.mag_status)

        return string

    @classmethod
    def parse(cls, message):
        match = re.match(cls.message_regex, message)
        if match is not None:
            message = Bno055Message(float(match.group(1)), int(match.group(4)))
            message.packet_time = float(match.group(2))
            message.arduino_time = float(match.group(3))

            group_index = 5
            for index, vector in enumerate(message.vectors):
                elements = match.group(index + group_index).split(", ")
                for element_index, element in enumerate(elements):
                    vector[element_index] = float(element)

            return message
        else:
            return None


class BNO055(Arduino):
    def __init__(self, enabled=True):
        super(BNO055, self).__init__(
            "BNO055-IMU", enabled=enabled,
        )
        self.message = Bno055Message(time.time())

    async def loop(self):
        counter = 0
        self.start()
        while self.device_active():
            while not self.empty():
                packet_time, packets = self.read()

                for packet in packets:
                    message = self.parse_packet(packet_time, packet, counter)
                    self.log_to_buffer(packet_time, message)
                    await self.broadcast(message)
                    counter += 1

            await asyncio.sleep(0.0)

    def parse_packet(self, packet_time, packet, packet_num):
        data = packet.split("\t")
        if data.pop(0) != 'imu':
            self.logger.warning("Invalid message header: %s" % str(packet))
            return

        segment = ""
        self.message.timestamp = time.time()
        self.message.n = packet_num
        self.message.packet_time = packet_time
        try:
            for segment in data:
                if len(segment) > 0:
                    if segment[0] == "t":
                        self.message.arduino_time = float(segment[1:]) / 1000
                    elif segment[0] == "e":
                        self.message.euler[segment[1]] = math.radians(float(segment[2:]))
                    elif segment[0] == "a":
                        self.message.accel[segment[1]] = float(segment[2:])
                    elif segment[0] == "g":
                        self.message.gyro[segment[1]] = float(segment[2:])
                    elif segment[0] == "m":
                        self.message.mag[segment[1]] = float(segment[2:])
                    elif segment[0] == "l":
                        self.message.linaccel[segment[1]] = float(segment[2:])
                    elif segment[0] == "q":
                        self.message.quat[segment[1]] = float(segment[2:])
                    elif segment[0] == "s":
                        if segment[1] == "s":
                            self.message.system_status = int(segment[2:])
                        elif segment[1] == "a":
                            self.message.accel_status = int(segment[2:])
                        elif segment[1] == "g":
                            self.message.gyro_status = int(segment[2:])
                        elif segment[1] == "m":
                            self.message.mag_status = int(segment[2:])
                    else:
                        self.logger.warning("Invalid segment type! Segment: '%s', packet: '%s'" % (segment[0], data))
                else:
                    self.logger.warning("Empty segment! Packet: '%s'" % data)
        except ValueError:
            self.logger.error("Failed to parse: '%s'" % segment)

        return self.message
