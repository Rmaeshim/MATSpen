import asyncio
from threading import Event

import numpy as np
from atlasbuggy import Node


class DataPlotterBase(Node):
    def __init__(self, enabled=True, time_data_window=3.0):
        super(DataPlotterBase, self).__init__(enabled)

        self.pause_time = 1 / 30
        self.exit_event = Event()
        self.plot_paused = False
        self.tb6612_times = []
        self.bno055_times = []

        self.tb6612_tag = "tb6612"
        self.tb6612_sub = self.define_subscription(self.tb6612_tag)
        self.tb6612_queue = None

        self.bno055_tag = "bno055"
        self.bno055_sub = self.define_subscription(self.bno055_tag, is_required=False)
        self.bno055_queue = None

        self.time_data_window = time_data_window

        self.plt = None
        if self.enabled:
            self.enable_matplotlib()
            self.fig = self.plt.figure(1)
            self.fig.canvas.mpl_connect('key_press_event', self.press)
            self.fig.canvas.mpl_connect('close_event', lambda event: self.exit_event.set())

        self.speed_timestamps = []
        self.speed_data = []
        self.position_data = []
        self.speed_t0 = None

        self.bno_timestamps = []
        self.x_data = []
        self.y_data = []
        self.z_data = []
        self.bno_t0 = None

    def enable_matplotlib(self):
        from matplotlib import pyplot as plt
        self.plt = plt

    def take(self):
        self.tb6612_queue = self.tb6612_sub.get_queue()
        if self.is_subscribed(self.bno055_tag):
            self.bno055_queue = self.bno055_sub.get_queue()

    async def setup(self):
        if self.is_subscribed(self.bno055_tag):
            self.bno_plot = self.fig.add_subplot(2, 1, 1)
            self.bno_x_line = self.bno_plot.plot([], [], '-', label="x")[0]
            # self.bno_y_line = self.bno_plot.plot([], [], '-', label="y")[0]
            # self.bno_z_line = self.bno_plot.plot([], [], '-', label="z")[0]

            self.speed_plot = self.fig.add_subplot(2, 1, 2)

            self.bno_plot.legend(fontsize="x-small", shadow="True", loc=0)
        else:
            self.speed_plot = self.fig.add_subplot(1, 1, 1)

        self.speed_line = self.speed_plot.plot([], [], '-', label="Hz")[0]
        self.speed_plot.legend(fontsize="x-small", shadow="True", loc=0)

        self.plt.ion()
        self.plt.show(block=False)

    async def loop(self):
        while True:
            if self.exit_event.is_set():
                return

            if self.plot_paused:
                await self.draw()
                continue

            await self.get_tb6612_data()
            if self.is_subscribed(self.bno055_tag):
                await self.get_bno055_data()

            if self.is_subscribed(self.bno055_tag):
                if len(self.speed_timestamps) == 0 or len(self.bno_timestamps) == 0:
                    await self.draw()
                    continue
            else:
                if len(self.speed_timestamps) == 0:
                    await self.draw()
                    continue

            while self.speed_timestamps[-1] - self.speed_timestamps[0] > self.time_data_window:
                self.position_data.pop(0)
                self.speed_timestamps.pop(0)
                self.speed_data.pop(0)

            if self.is_subscribed(self.bno055_tag):
                while self.bno_timestamps[-1] - self.bno_timestamps[0] > self.time_data_window:
                    self.bno_timestamps.pop(0)
                    self.x_data.pop(0)
                    self.y_data.pop(0)
                    self.z_data.pop(0)

            self.plot_data()
            await self.draw()

    def plot_data(self):
        pass

    async def get_tb6612_data(self):
        while not self.tb6612_queue.empty():
            message = await asyncio.wait_for(self.tb6612_queue.get(), timeout=1)
            if self.speed_t0 is None:
                self.speed_t0 = message.arduino_time
            message.arduino_time -= self.speed_t0

            self.tb6612_times.append(message.arduino_time)
            self.speed_data.append(message.speed)
            self.position_data.append(message.position)
            self.speed_timestamps.append(message.arduino_time)

    async def get_bno055_data(self):
        while not self.bno055_queue.empty():
            message = await asyncio.wait_for(self.bno055_queue.get(), timeout=1)

            if self.bno_t0 is None:
                self.bno_t0 = message.arduino_time
            message.arduino_time -= self.bno_t0

            self.bno055_times.append(message.arduino_time)
            self.x_data.append(message.euler.x)
            self.y_data.append(message.euler.y)
            self.z_data.append(message.euler.z)
            self.bno_timestamps.append(message.arduino_time)

    def press(self, event):
        """matplotlib key press event. Close all figures when q is pressed"""
        if event.key == "q":
            self.exit_event.set()
        if event.key == " ":
            self.plot_paused = not self.plot_paused
            print("Plot is paused:", self.plot_paused)

    async def draw(self):
        self.fig.canvas.draw()
        self.plt.pause(self.pause_time)
        await asyncio.sleep(self.pause_time)

    async def teardown(self):
        self.plt.close("all")

        if len(self.tb6612_times) > 1:
            time_diff = np.diff(self.tb6612_times)
            print("tb6612 time fps avg: %0.4f" % (len(self.tb6612_times) / sum(time_diff)))

        if len(self.bno055_times) > 1:
            time_diff = np.diff(self.bno055_times)
            print("bno055 time fps avg: %0.4f" % (len(self.bno055_times) / sum(time_diff)))
