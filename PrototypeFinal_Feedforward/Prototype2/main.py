import matplotlib

from atlasbuggy import Orchestrator, run

from graphical.plotter import Plotter
from arduinos.tb6612 import TB6612
from arduinos.bno055 import BNO055

matplotlib.use('TkAgg')  # keeps tkinter happy
from graphical.gui import TkinterGUI


class VisualizerOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(write=False)
        super(VisualizerOrchestrator, self).__init__(event_loop)

        self.tb6612 = TB6612()
        self.bno055 = BNO055(enabled=True)
        self.plotter = Plotter(enabled=True, time_data_window=3.0)
        self.gui = TkinterGUI("constants/pid_constants.pkl")

        self.subscribe(self.tb6612, self.plotter, self.plotter.tb6612_tag)
        self.subscribe(self.bno055, self.plotter, self.plotter.bno055_tag)
        self.subscribe(self.bno055, self.plotter, self.plotter.bno055_motor_tag)
        self.subscribe(self.tb6612, self.gui, self.gui.tb6612_tag)
        self.subscribe(self.bno055, self.gui, self.gui.bno055_tag)


run(VisualizerOrchestrator)
