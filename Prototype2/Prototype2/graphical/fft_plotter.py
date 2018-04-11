
import numpy as np

from .data_plotter_base import DataPlotterBase


class Plotter(DataPlotterBase):
    def __init__(self, enabled=True, time_data_window=3.0):
        super(Plotter, self).__init__(enabled, time_data_window)

    def plot_data(self):
        if self.is_subscribed(self.bno055_tag):
            self.calculate_sensing_fft()
        self.calculate_input_fft()

    def calculate_sensing_fft(self):
        bno_freq = np.fft.fftfreq(len(self.bno_timestamps), np.mean(np.diff(self.bno_timestamps)))
        bno_fft = abs(np.fft.fft(self.y_data))

        indices = (0.1 < bno_freq) & (bno_freq < 20.0)
        bno_freq = bno_freq[indices]
        bno_fft = bno_fft[indices]

        self.bno_x_line.set_xdata(bno_freq)
        self.bno_x_line.set_ydata(bno_fft)

        self.bno_plot.relim()
        self.bno_plot.autoscale_view()

    def calculate_input_fft(self):
        # speed_freq = np.fft.fftfreq(len(self.speed_timestamps), np.mean(np.diff(self.speed_timestamps)))
        # speed_fft = abs(np.fft.fft(self.position_data))
        #
        # indices = (0.1 < speed_freq) & (speed_freq < 40.0)
        # speed_freq = speed_freq[indices]
        # speed_fft = speed_fft[indices]

        # plt.hist(x, 50, normed=1, facecolor='green', alpha=0.75)
        speed_fft, bin_edges = np.histogram(self.speed_data, density=True, bins=np.arange(0, 20, 0.01))
        speed_freq = np.linspace(0, 20, len(speed_fft))

        self.speed_line.set_xdata(speed_freq)
        self.speed_line.set_ydata(speed_fft)

        self.speed_plot.relim()
        self.speed_plot.autoscale_view()

