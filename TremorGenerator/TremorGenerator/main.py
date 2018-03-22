import csv
import time
import asyncio
import numpy as np
from threading import Event
from matplotlib import pyplot as plt

from atlasbuggy import Node, Orchestrator, run

from tb6612 import TB6612


class Visualizer(Node):
    def __init__(self, enabled=True):
        super(Visualizer, self).__init__(enabled)

        self.pause_time = 1 / 30
        self.exit_event = Event()
        self.plot_paused = False
        self.arduino_times = []

        self.tb6612_tag = "tb6612"
        self.tb6612_sub = self.define_subscription(self.tb6612_tag)
        self.tb6612_queue = None

        self.fig = plt.figure(1)
        self.fig.canvas.mpl_connect('key_press_event', self.press)
        self.fig.canvas.mpl_connect('close_event', lambda event: self.exit_event.set())

        self.position_plot = self.fig.add_subplot(2, 1, 1)
        self.position_line = self.position_plot.plot([], [], '.-', label="angle (rad)")[0]

        self.speed_plot = self.fig.add_subplot(2, 1, 2)
        self.arduino_speed_line = self.speed_plot.plot([], [], '.-', label="arduino speed (rad/s)")[0]
        self.calc_speed_line = self.speed_plot.plot([], [], '.-', label="calc speed (rad/s)")[0]

        self.data_log = open("%s.csv" % time.time(), 'w+')
        self.data_writer = csv.writer(self.data_log)

        plt.legend(fontsize="x-small", shadow="True", loc=0)
        plt.ion()
        plt.show(block=False)

    def take(self):
        self.tb6612_queue = self.tb6612_sub.get_queue()

    async def loop(self):
        timestamps = []
        pos_data = []
        arduino_speed_data = []
        calc_speed_times = []
        calc_speed_data = []

        while not self.exit_event.is_set():
            while not self.tb6612_queue.empty():
                message = await asyncio.wait_for(self.tb6612_queue.get(), timeout=1)
                self.arduino_times.append(message.arduino_time)

                pos_data.append(message.position)
                arduino_speed_data.append(message.speed)

                timestamps.append(message.arduino_time)

                if len(pos_data) > 20:
                    calculated_speed = np.mean(np.diff(pos_data[-20:])) / np.mean(np.diff(timestamps[-20:]))
                    calc_speed_times.append(message.arduino_time)
                    calc_speed_data.append(calculated_speed)

                self.data_writer.writerow([message.arduino_time, message.position, message.speed])

                if len(timestamps) > 500:
                    timestamps.pop(0)
                    pos_data.pop(0)
                    arduino_speed_data.pop(0)

                if len(calc_speed_data) > 500:
                    calc_speed_times.pop(0)
                    calc_speed_data.pop(0)

            if not self.plot_paused:
                self.position_line.set_xdata(timestamps)
                self.position_line.set_ydata(pos_data)

                self.arduino_speed_line.set_xdata(timestamps)
                self.arduino_speed_line.set_ydata(arduino_speed_data)

                self.calc_speed_line.set_xdata(calc_speed_times)
                self.calc_speed_line.set_ydata(calc_speed_data)

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
        plt.pause(self.pause_time)
        await asyncio.sleep(self.pause_time)

    async def teardown(self):
        plt.close("all")

        self.data_log.close()

        if len(self.arduino_times) > 1:
            time_diff = np.diff(self.arduino_times)
            print("arduino time fps avg: %0.4f" % (len(self.arduino_times) / sum(time_diff)))


class VisualizerOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(write=False)
        super(VisualizerOrchestrator, self).__init__(event_loop)

        tb6612 = TB6612()
        visualizer = Visualizer(enabled=True)

        self.add_nodes(tb6612, visualizer)

        self.subscribe(tb6612, visualizer, visualizer.tb6612_tag)

run(VisualizerOrchestrator)
