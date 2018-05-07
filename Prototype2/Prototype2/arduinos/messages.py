from atlasbuggy import Message


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
    def __init__(self, n, timestamp=None):
        super(Bno055Message, self).__init__(n, timestamp)

        self.packet_time = 0.0
        self.arduino_time = 0.0
        self.millis_time = 0.0
        self.euler = Bno055Vector("euler")
        self.ang_v = Bno055Vector("ang_v")
        self.frequency = Bno055Vector("frequency")
        self.mag = Bno055Vector("mag")
        self.gyro = Bno055Vector("gyro")
        self.accel = Bno055Vector("accel")
        self.linaccel = Bno055Vector("linaccel")
        self.quat = Bno055Vector("quat", xyz=False)

        self.vectors = [self.euler, self.ang_v, self.frequency, self.mag, self.gyro, self.accel, self.linaccel, self.quat]

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
        new_message.ang_v = Bno055Vector.copy_vector(message.ang_v)
        new_message.frequency = Bno055Vector.copy_vector(message.frequency)
        new_message.mag = Bno055Vector.copy_vector(message.mag)
        new_message.gyro = Bno055Vector.copy_vector(message.gyro)
        new_message.accel = Bno055Vector.copy_vector(message.accel)
        new_message.linaccel = Bno055Vector.copy_vector(message.linaccel)
        new_message.quat = Bno055Vector.copy_vector(message.quat)
        new_message.vectors = [
            new_message.euler,
            new_message.ang_v,
            new_message.frequency,
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
