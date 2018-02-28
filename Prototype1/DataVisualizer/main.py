import time
import random
import asyncio
from threading import Event
from matplotlib import pyplot as plt

from atlasbuggy import Node, Orchestrator, run

from bno055 import BNO055


class Visualizer(Node):
    def __init__(self, enabled=True):
        super(Visualizer, self).__init__(enabled)

        self.pause_time = 1 / 30
        self.exit_event = Event()
        self.arduino_times = []

        self.bno055_tag = "bno055"
        self.bno055_sub = self.define_subscription(self.bno055_tag)
        self.bno055_queue = None

        self.fig = plt.figure(1)
        self.fig.canvas.mpl_connect('key_press_event', self.press)
        self.fig.canvas.mpl_connect('close_event', lambda event: self.exit_event.set())

        self.bno_plot = self.fig.add_subplot(1, 1, 1)

        self.x_line = self.bno_plot.plot([], [], label="x")[0]
        self.y_line = self.bno_plot.plot([], [], label="y")[0]
        self.z_line = self.bno_plot.plot([], [], label="z")[0]

        plt.legend(fontsize="x-small", shadow="True", loc=0)
        plt.ion()
        plt.show(block=False)

    def take(self):
        self.bno055_queue = self.bno055_sub.get_queue()

    async def loop(self):
        timestamps = []
        x_data = []
        y_data = []
        z_data = []

        while not self.exit_event.is_set():
            while not self.bno055_queue.empty():
                message = await asyncio.wait_for(self.bno055_queue.get(), timeout=1)

                self.arduino_times.append(message.arduino_time)

                x_data.append(message.euler.x)
                y_data.append(message.euler.y)
                z_data.append(message.euler.z)

                timestamps.append(time.time())

            self.x_line.set_xdata(timestamps)
            self.x_line.set_ydata(x_data)

            self.y_line.set_xdata(timestamps)
            self.y_line.set_ydata(y_data)

            self.z_line.set_xdata(timestamps)
            self.z_line.set_ydata(z_data)

            self.bno_plot.relim()
            self.bno_plot.autoscale_view()

            await self.draw()

    def press(self, event):
        """matplotlib key press event. Close all figures when q is pressed"""
        if event.key == "q":
            self.exit_event.set()

    async def draw(self):
        self.fig.canvas.draw()
        plt.pause(self.pause_time)
        await asyncio.sleep(self.pause_time)

    async def teardown(self):
        plt.close("all")
        print("arduino time fps avg: %0.4fms" % (sum(self.arduino_times) / len(self.arduino_times)))


class VisualizerOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(write=False)
        super(VisualizerOrchestrator, self).__init__(event_loop)

        bno055 = BNO055()
        visualizer = Visualizer(enabled=True)

        self.add_nodes(bno055, visualizer)

        self.subscribe(bno055, visualizer, visualizer.bno055_tag)


run(VisualizerOrchestrator)
