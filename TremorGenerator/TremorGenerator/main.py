import csv
import time
import asyncio
import numpy as np
from threading import Event
from atlasbuggy import Node, Orchestrator, run

from tb6612 import TB6612

import matplotlib

matplotlib.use('TkAgg')  # keeps tkinter happy
from gui import TkinterGUI


class Visualizer(Node):
    def __init__(self, enabled=True, log_to_csv=False):
        super(Visualizer, self).__init__(enabled)

        self.pause_time = 1 / 30
        self.exit_event = Event()
        self.plot_paused = False
        self.times = []

        self.tb6612_tag = "tb6612"
        self.tb6612_sub = self.define_subscription(self.tb6612_tag)
        self.tb6612_queue = None

        self.log_to_csv = log_to_csv

        self.plt = None
        if self.enabled:
            self.enable_matplotlib()
            self.fig = self.plt.figure(1)
            self.fig.canvas.mpl_connect('key_press_event', self.press)
            self.fig.canvas.mpl_connect('close_event', lambda event: self.exit_event.set())

            self.position_plot = self.fig.add_subplot(2, 1, 1)
            self.position_line = self.position_plot.plot([], [], '.-', label="angle (rad)")[0]

            self.speed_plot = self.fig.add_subplot(2, 1, 2)
            self.speed_line = self.speed_plot.plot([], [], '-', label="arduino speed (rad/s)")[0]

            if self.log_to_csv:
                self.data_log = open("%s.csv" % time.time(), 'w+')
                self.data_writer = csv.writer(self.data_log)

            self.plt.legend(fontsize="x-small", shadow="True", loc=0)
            self.plt.ion()
            self.plt.show(block=False)

    def enable_matplotlib(self):
        from matplotlib import pyplot as plt
        self.plt = plt

    def take(self):
        self.tb6612_queue = self.tb6612_sub.get_queue()

    async def loop(self):
        timestamps = []
        pos_data = []
        speed_data = []
        t0 = None

        while not self.exit_event.is_set():
            while not self.tb6612_queue.empty():
                message = await asyncio.wait_for(self.tb6612_queue.get(), timeout=1)
                if t0 is None:
                    t0 = message.arduino_time
                message.arduino_time -= t0

                self.times.append(message.arduino_time)

                pos_data.append(message.position)
                speed_data.append(message.speed)

                timestamps.append(message.arduino_time)

                if self.log_to_csv:
                    self.data_writer.writerow([message.arduino_time, message.position, message.speed])

                if timestamps[-1] - timestamps[0] > 3:
                    timestamps.pop(0)
                    pos_data.pop(0)
                    speed_data.pop(0)

            if not self.plot_paused:
                self.position_line.set_xdata(timestamps)
                self.position_line.set_ydata(pos_data)

                self.speed_line.set_xdata(timestamps)
                self.speed_line.set_ydata(speed_data)

                self.position_plot.relim()
                self.position_plot.autoscale_view()

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

        if len(self.times) > 1:
            time_diff = np.diff(self.times)
            print("arduino time fps avg: %0.4f" % (len(self.times) / sum(time_diff)))


class VisualizerOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(write=False)
        super(VisualizerOrchestrator, self).__init__(event_loop)

        tb6612 = TB6612()
        visualizer = Visualizer(enabled=True, log_to_csv=False)
        gui = TkinterGUI()

        self.add_nodes(tb6612, visualizer, gui)

        self.subscribe(tb6612, visualizer, visualizer.tb6612_tag)
        self.subscribe(tb6612, gui, gui.tb6612_tag)


run(VisualizerOrchestrator)
