import csv
from atlasbuggy import Node


class CsvCreator(Node):
    def __init__(self, file_path):
        super(CsvCreator, self).__init__()

        self.file_path = file_path

        self.tb6612_tag = "tb6612"
        self.tb6612_sub = self.define_subscription(self.tb6612_tag, callback=self.tb6612_fn)

        self.bno055_tag = "bno055"
        self.bno055_sub = self.define_subscription(self.bno055_tag, is_required=False, callback=self.bno055_fn)

        self.data = []

    def tb6612_fn(self, message):
        self.data.append(("motor", message.n, message.timestamp, message.position, message.speed))

    def bno055_fn(self, message):
        self.data.append(("bno055", message.n, message.timestamp, message.euler.x, message.euler.y, message.euler.z))

    async def teardown(self):
        with open(self.file_path, 'w+') as file:
            csv_writer = csv.writer(file)
            for row in self.data:
                csv_writer.writerow(row)
