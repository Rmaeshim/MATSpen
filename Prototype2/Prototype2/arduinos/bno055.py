import os
import time
import math
import asyncio

from atlasbuggy import Message
from atlasbuggy.device import Arduino
from atlasbuggy.log.playback import PlaybackNode


class Bno055Vector:
    def __init__(self, name, *vector, xyz=True):
        self.name = name
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.w = 0.0

        self.xyz = xyz

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

    def get_tuple(self):
        if self.xyz:
            return self.x, self.y, self.z
        else:
            return self.x, self.y, self.z, self.w

    @classmethod
    def copy_vector(cls, vector):
        new_vector = cls(vector.name, xyz=vector.xyz)
        new_vector.x = vector.x
        new_vector.y = vector.y
        new_vector.z = vector.z
        new_vector.w = vector.w

        return new_vector

    def __str__(self):
        return str(self.get_tuple())


class Bno055Message(Message):
    message_regex = r"Bno055Message\(t: (\d.*), pt: (\d.*), at: (\d.*), n: (\d*), " \
                    r"euler: \(([-\d., ]*)\), " \
                    r"mag: \(([-\d., ]*)\), gyro: \(([-\d., ]*)\), accel: \(([-\d., ]*)\), " \
                    r"linaccel: \(([-\d., ]*)\), quat: \(([-\d., ]*)\), " \
                    r"status; sys: (\d*), a: (\d*), g: (\d*), m: (\d*)\)"

    def __init__(self, n, timestamp=None):
        super(Bno055Message, self).__init__(n, timestamp)

        self.packet_time = 0.0
        self.arduino_time = 0.0
        self.millis_time = 0.0
        self.euler = Bno055Vector("euler")
        self.mag = Bno055Vector("mag")
        self.gyro = Bno055Vector("gyro")
        self.accel = Bno055Vector("accel")
        self.linaccel = Bno055Vector("linaccel")
        self.quat = Bno055Vector("quat", xyz=False)

        self.vectors = [self.euler, self.mag, self.gyro, self.accel, self.linaccel, self.quat]

        self.system_status = 0
        self.accel_status = 0
        self.gyro_status = 0
        self.mag_status = 0

        self.ignore_properties("vectors")
        self.auto_serialize()

    @classmethod
    def copy_message(cls, message):
        new_message = cls(message.timestamp, message.n)
        new_message.packet_time = message.packet_time
        new_message.arduino_time = message.arduino_time

        new_message.euler = Bno055Vector.copy_vector(message.euler)
        new_message.mag = Bno055Vector.copy_vector(message.mag)
        new_message.gyro = Bno055Vector.copy_vector(message.gyro)
        new_message.accel = Bno055Vector.copy_vector(message.accel)
        new_message.linaccel = Bno055Vector.copy_vector(message.linaccel)
        new_message.quat = Bno055Vector.copy_vector(message.quat)
        new_message.vectors = [
            new_message.euler,
            new_message.mag,
            new_message.gyro,
            new_message.accel,
            new_message.linaccel,
            new_message.quat
        ]

        new_message.system_status = message.system_status
        new_message.accel_status = message.accel_status
        new_message.gyro_status = message.gyro_status
        new_message.mag_status = message.mag_status

        return new_message

    @classmethod
    def parse_field(cls, name, value):
        data = tuple(map(float, value[1:-1].split(", ")))
        return Bno055Vector(name, *data)


class BNO055(Arduino):
    def __init__(self, enabled=True):
        self.set_logger(write=True)
        super(BNO055, self).__init__(
            "BNO055-IMU", enabled=enabled,
        )
        self.prev_message = Bno055Message(time.time())

    async def loop(self):
        counter = 0
        self.start()
        while self.device_active():
            while not self.empty():
                packet_time, arduino_times, packets = self.read()

                for arduino_time, packet in zip(arduino_times, packets):
                    message = self.parse_packet(packet_time, arduino_time, packet, counter)
                    self.log_to_buffer(packet_time, message)
                    await self.broadcast(message)
                    counter += 1

            await asyncio.sleep(0.0)

    def parse_packet(self, packet_time, arduino_time, packet, packet_num):
        data = packet.split("\t")
        if data.pop(0) != 'imu':
            self.logger.warning("Invalid message header: %s" % str(packet))
            return

        segment = ""

        message = Bno055Message.copy_message(self.prev_message)

        message.timestamp = time.time()
        message.n = packet_num
        message.packet_time = packet_time
        message.arduino_time = arduino_time

        try:
            for segment in data:
                if len(segment) > 0:
                    if segment[0] == "t":
                        message.millis_time = float(segment[1:]) / 1000
                    elif segment[0] == "e":
                        message.euler[segment[1]] = math.radians(float(segment[2:]))
                    elif segment[0] == "a":
                        message.accel[segment[1]] = float(segment[2:])
                    elif segment[0] == "g":
                        message.gyro[segment[1]] = float(segment[2:])
                    elif segment[0] == "m":
                        message.mag[segment[1]] = float(segment[2:])
                    elif segment[0] == "l":
                        message.linaccel[segment[1]] = float(segment[2:])
                    elif segment[0] == "q":
                        message.quat[segment[1]] = float(segment[2:])
                    elif segment[0] == "s":
                        if segment[1] == "s":
                            message.system_status = int(segment[2:])
                        elif segment[1] == "a":
                            message.accel_status = int(segment[2:])
                        elif segment[1] == "g":
                            message.gyro_status = int(segment[2:])
                        elif segment[1] == "m":
                            message.mag_status = int(segment[2:])
                    else:
                        self.logger.warning("Invalid segment type! Segment: '%s', packet: '%s'" % (segment[0], data))
                else:
                    self.logger.warning("Empty segment! Packet: '%s'" % data)
        except ValueError:
            self.logger.error("Failed to parse: '%s'" % segment)

        self.prev_message = message
        return message


class BNO055Playback(PlaybackNode):
    def __init__(self, file_name, directory=None, enabled=True, **playback_kwargs):
        bno055_name = "BNO055"

        directory = os.path.join(directory, bno055_name)
        super(BNO055Playback, self).__init__(file_name, directory=directory, enabled=enabled,
                                             message_class=Bno055Message, name=bno055_name, **playback_kwargs)
