import os

from atlasbuggy import Orchestrator, run
from atlasbuggy.log.playback import PlaybackNode

from graphical.fft_plotter import Plotter
from arduinos.bno055 import BNO055Playback
from arduinos.tb6612 import TB6612Message
from csv_creator import CsvCreator


class PlaybackOrchestrator(Orchestrator):
    def __init__(self, event_loop):
        self.set_default(write=False)
        super(PlaybackOrchestrator, self).__init__(event_loop)

        log_date = "logs/2018_Mar_28"
        log_time = "18_44_43.log"

        tb6612_name = "TB6612"
        tb6612_directory = os.path.join(log_date, tb6612_name)

        bno055 = BNO055Playback(log_time, log_date)
        tb6612 = PlaybackNode(log_time, directory=tb6612_directory, message_class=TB6612Message, name=tb6612_name)

        plotter = Plotter(enabled=True)

        csv_creator = CsvCreator(os.path.join("data", "%s %s.csv" % (log_time[:-4], log_date[5:])))

        self.subscribe(tb6612, plotter, plotter.tb6612_tag)
        self.subscribe(bno055, plotter, plotter.bno055_tag)

        self.subscribe(tb6612, csv_creator, csv_creator.tb6612_tag)
        self.subscribe(bno055, csv_creator, csv_creator.bno055_tag)

run(PlaybackOrchestrator)
