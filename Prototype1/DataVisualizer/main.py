from atlasbuggy import Orchestrator, run

from bno055 import BNO055


class VisualizerOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        super(VisualizerOrchestrator, self).__init__(event_loop)

        bno055 = BNO055()

        self.add_nodes(bno055)


run(VisualizerOrchestrator)
