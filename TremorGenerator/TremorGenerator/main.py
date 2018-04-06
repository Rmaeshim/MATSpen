import matplotlib

from atlasbuggy import Orchestrator, run

from plotter import Plotter
from tb6612 import TB6612
from bno055 import BNO055

matplotlib.use('TkAgg')  # keeps tkinter happy
from gui import TkinterGUI


class VisualizerOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(write=False)
        super(VisualizerOrchestrator, self).__init__(event_loop)

        self.tb6612 = TB6612()
        self.bno055 = BNO055()
        self.plotter = Plotter(enabled=True, log_to_csv=False)
        self.gui = TkinterGUI()

        self.subscribe(self.tb6612, self.plotter, self.plotter.tb6612_tag)
        self.subscribe(self.bno055, self.plotter, self.plotter.bno055_tag)
        self.subscribe(self.tb6612, self.gui, self.gui.tb6612_tag)

    async def setup(self):
        self.tb6612.command_motor(6.0)

run(VisualizerOrchestrator)
