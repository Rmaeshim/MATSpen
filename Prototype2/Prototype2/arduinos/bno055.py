import os
import time
import math
import asyncio

from atlasbuggy.device import Arduino
from atlasbuggy.log.playback import PlaybackNode

from .messages import Bno055Message, TB6612Message


class BNO055(Arduino):
    def __init__(self, enabled=True):
        self.set_logger(write=True)
        super(BNO055, self).__init__(
            "BNO055-IMU", enabled=enabled,
        )
        self.prev_imu_message = Bno055Message(0)
        self.prev_motor_message = TB6612Message(0)

        self.current_commanded_speed = 0.0

        self.motor_service = "motor"
        self.define_service(self.motor_service, TB6612Message)

    async def loop(self):
        self.start()
        while self.device_active():
            while not self.empty():
                packet_time, sequence_nums, arduino_times, packets = self.read()
                for n, arduino_time, packet in zip(sequence_nums, arduino_times, packets):
                    await self.parse_packet(packet_time, arduino_time, packet, n)

            await asyncio.sleep(0.0)

    async def parse_packet(self, packet_time, arduino_time, packet, packet_num):
        data = packet.split("\t")
        header_segment = data.pop(0)
        if header_segment == 'imu':
            message = self.parse_imu_msg(packet_time, arduino_time, packet, packet_num, data)
            await self.broadcast(message)

        elif header_segment == 'motor':
            message = self.parse_motor_msg(packet_time, arduino_time, packet, packet_num, data)
            await self.broadcast(message, self.motor_service)

        else:
            self.logger.warning("Invalid message header: %s" % str(packet))
            return None

        self.log_to_buffer(packet_time, message)

    def parse_imu_msg(self, packet_time, arduino_time, packet, packet_num, data):
        segment = ""

        message = Bno055Message.copy_message(self.prev_imu_message)

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

        self.prev_imu_message = message

        return message

    def parse_motor_msg(self, packet_time, arduino_time, packet, packet_num, data):
        message = self.prev_motor_message.copy()
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

        self.prev_motor_message = message
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

    def set_pid_constants(self, kp, ki, kd):
        self.current_commanded_speed = 0.0
        self.write("kp%s" % kp)
        self.write("ki%s" % ki)
        self.write("kd%s" % kd)
        self.write("r")


class BNO055Playback(PlaybackNode):
    def __init__(self, file_name, directory=None, enabled=True, **playback_kwargs):
        bno055_name = "BNO055"

        directory = os.path.join(directory, bno055_name)
        super(BNO055Playback, self).__init__(
            file_name, directory=directory, enabled=enabled,
            message_parse_fn=BNO055Playback.parse_message, name=bno055_name, **playback_kwargs
        )

    @staticmethod
    def parse_message(line):
        if line.startwith("Bno055Message"):
            return Bno055Message.parse(line.message)
        elif line.startwith("TB6612Message"):
            return TB6612Message.parse(line.message)
