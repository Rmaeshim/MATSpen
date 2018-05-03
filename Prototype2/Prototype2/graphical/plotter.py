
from .data_plotter_base import DataPlotterBase


class Plotter(DataPlotterBase):
    def __init__(self, enabled=True, time_data_window=3.0):
        super(Plotter, self).__init__(enabled, time_data_window)

    def plot_data(self):
        if self.is_subscribed(self.bno055_tag):
            self.bno_data_line.set_xdata(self.bno_timestamps)
            self.bno_data_line.set_ydata(self.x_data)

        if self.is_subscribed(self.bno055_motor_tag):
            self.bno_motor_line.set_xdata(self.bno_motor_speed_timestamps)
            self.bno_motor_line.set_ydata(self.bno_motor_speed_data)

        if self.is_subscribed(self.bno055_tag) or self.is_subscribed(self.bno055_motor_tag):
            self.bno_plot.relim()
            self.bno_plot.autoscale_view()

        self.speed_line.set_xdata(self.speed_timestamps)
        self.speed_line.set_ydata(self.speed_data)

        self.speed_plot.relim()
        self.speed_plot.autoscale_view()
