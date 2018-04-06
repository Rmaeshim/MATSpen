import csv
import time
import asyncio
from threading import Event

import numpy as np
from atlasbuggy import Node


class Plotter(Node):
    def __init__(self, enabled=True, log_to_csv=False, time_data_window=3.0):
        super(Plotter, self).__init__(enabled)

        self.pause_time = 1 / 30
        self.exit_event = Event()
        self.plot_paused = False
        self.tb6612_times = []
        self.bno055_times = []

        self.tb6612_tag = "tb6612"
        self.tb6612_sub = self.define_subscription(self.tb6612_tag)
        self.tb6612_queue = None

        self.bno055_tag = "bno055"
        self.bno055_sub = self.define_subscription(self.bno055_tag)
        self.bno055_queue = None

        self.log_to_csv = log_to_csv

        self.time_data_window = time_data_window

        self.plt = None
        if self.enabled:
            self.enable_matplotlib()
            self.fig = self.plt.figure(1)
            self.fig.canvas.mpl_connect('key_press_event', self.press)
            self.fig.canvas.mpl_connect('close_event', lambda event: self.exit_event.set())

            self.bno_plot = self.fig.add_subplot(2, 1, 1)
            self.x_line = self.bno_plot.plot([], [], '-', label="x")[0]
            # self.y_line = self.bno_plot.plot([], [], '-', label="y")[0]
            # self.z_line = self.bno_plot.plot([], [], '-', label="z")[0]

            self.speed_plot = self.fig.add_subplot(2, 1, 2)
            self.speed_line = self.speed_plot.plot([], [], '-', label="Hz")[0]

            if self.log_to_csv:
                self.data_log = open("%s.csv" % time.time(), 'w+')
                self.data_writer = csv.writer(self.data_log)

            self.bno_plot.legend(fontsize="x-small", shadow="True", loc=0)
            self.speed_plot.legend(fontsize="x-small", shadow="True", loc=0)
            self.plt.ion()
            self.plt.show(block=False)

    def enable_matplotlib(self):
        from matplotlib import pyplot as plt
        self.plt = plt

    def take(self):
        self.tb6612_queue = self.tb6612_sub.get_queue()
        self.bno055_queue = self.bno055_sub.get_queue()

    async def loop(self):
        speed_timestamps = []
        speed_data = []
        speed_t0 = None

        bno_timestamps = []
        x_data = []
        y_data = []
        z_data = []
        bno_t0 = None

        while True:
            if self.exit_event.is_set():
                return

            if self.plot_paused:
                await self.draw()
                continue

            while not self.tb6612_queue.empty():
                message = await asyncio.wait_for(self.tb6612_queue.get(), timeout=1)
                if speed_t0 is None:
                    speed_t0 = message.arduino_time
                message.arduino_time -= speed_t0

                self.tb6612_times.append(message.arduino_time)
                speed_data.append(message.speed)
                speed_timestamps.append(message.arduino_time)

                if self.log_to_csv:
                    self.data_writer.writerow([message.arduino_time, message.position, message.speed])

            while not self.bno055_queue.empty():
                message = await asyncio.wait_for(self.bno055_queue.get(), timeout=1)

                if bno_t0 is None:
                    bno_t0 = message.arduino_time
                message.arduino_time -= speed_t0

                self.bno055_times.append(message.arduino_time)
                x_data.append(message.euler.x)
                y_data.append(message.euler.y)
                z_data.append(message.euler.z)
                bno_timestamps.append(message.arduino_time)

                current_bno_time = message.arduino_time

            if len(speed_timestamps) == 0 or len(bno_timestamps) == 0:
                await self.draw()
                continue

            while speed_timestamps[-1] - speed_timestamps[0] > self.time_data_window:
                speed_timestamps.pop(0)
                speed_data.pop(0)

            while bno_timestamps[-1] - bno_timestamps[0] > self.time_data_window:
                bno_timestamps.pop(0)
                x_data.pop(0)
                y_data.pop(0)
                z_data.pop(0)

            self.x_line.set_xdata(bno_timestamps)
            self.x_line.set_ydata(x_data)

            # self.y_line.set_xdata(bno_timestamps)
            # self.y_line.set_ydata(y_data)
            #
            # self.z_line.set_xdata(bno_timestamps)
            # self.z_line.set_ydata(z_data)

            self.bno_plot.relim()
            self.bno_plot.autoscale_view()

            self.speed_line.set_xdata(speed_timestamps)
            self.speed_line.set_ydata(speed_data)

            self.speed_plot.relim()
            self.speed_plot.autoscale_view()

            await self.draw()

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

        if self.log_to_csv:
            self.data_log.close()

        if len(self.tb6612_times) > 1:
            time_diff = np.diff(self.tb6612_times)
            print("tb6612 time fps avg: %0.4f" % (len(self.tb6612_times) / sum(time_diff)))

        if len(self.bno055_times) > 1:
            time_diff = np.diff(self.bno055_times)
            print("bno055 time fps avg: %0.4f" % (len(self.bno055_times) / sum(time_diff)))
