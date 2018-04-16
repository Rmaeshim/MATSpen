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

        # log_date = "logs/2018_Mar_28"
        # log_time = "18_44_43.log"

        log_date = "logs/2018_Apr_15"

        log_time = "20_50_28.log"
        data_set_name = "random, 0-6.4Hz"

        # log_time = "20_51_15.log"
        # data_set_name = "chirp, 3.0-6.4Hz"

        # log_time = "20_52_03.log"
        # data_set_name = "constant, 6.4Hz"

        tb6612_name = "TB6612"
        tb6612_directory = os.path.join(log_date, tb6612_name)

        # update_rate = 0.0  # go as fast as possible
        update_rate = None  # run in real time

        bno055 = BNO055Playback(log_time, log_date, update_rate=update_rate)
        tb6612 = PlaybackNode(log_time, directory=tb6612_directory, message_class=TB6612Message, name=tb6612_name, update_rate=update_rate)

        plotter = Plotter(enabled=True, time_data_window=6.0)

        csv_creator_tb6612 = CsvCreator(os.path.join("data", "%s %s %s-TB6612.csv" % (data_set_name, log_time[:-4], log_date[5:])),
                                        use_tb6612=True, use_bno055=False)
        csv_creator_bno055 = CsvCreator(os.path.join("data", "%s %s %s-BNO055.csv" % (data_set_name, log_time[:-4], log_date[5:])),
                                        use_bno055=True, use_tb6612=False)

        self.subscribe(tb6612, plotter, plotter.tb6612_tag)
        self.subscribe(bno055, plotter, plotter.bno055_tag)

        self.subscribe(tb6612, csv_creator_tb6612, csv_creator_tb6612.tb6612_tag)
        self.subscribe(bno055, csv_creator_bno055, csv_creator_bno055.bno055_tag)


run(PlaybackOrchestrator)
