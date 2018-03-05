import csv
import peakutils
import numpy as np
import matplotlib.pyplot as plt

current_fig = None  # the current matplotlib figure to use
current_fig_num = 0  # the current matplotlib figure number


def press(event):
    """matplotlib key press event. Close all figures when q is pressed"""
    if event.key == "q":
        plt.close("all")


def new_fig(fig_num=None):
    """Create a new figure"""

    global current_fig_num, current_fig
    if fig_num is None:
        current_fig_num += 1
    else:
        current_fig_num = fig_num
    fig = plt.figure(current_fig_num)
    fig.canvas.mpl_connect('key_press_event', press)
    current_fig = fig

    return fig


def find_local_max(time_t, x_dist, peak_threshold, peak_min_dist, index_diff_threshold):
    """Find the local maximums and the times they occur at"""

    peak_indices = peakutils.indexes(x_dist, thres=peak_threshold, min_dist=peak_min_dist)
    print(peak_indices)

    assert len(peak_indices) != 0, "no peaks found!! thres=%s, min_dist=%s" % (peak_threshold, peak_min_dist)

    # eliminate small clusters
    peak_index_diff = np.diff(peak_indices)
    peak_indices = np.delete(peak_indices, np.where(peak_index_diff < index_diff_threshold))

    # extract peak values
    peak_disp = x_dist[peak_indices]
    peak_times = time_t[peak_indices]

    local_max_disp = peak_disp[peak_disp > 0]
    local_max_times = peak_times[peak_disp > 0]

    return local_max_disp, local_max_times


def analyze_data(file_path, axis, start_time, end_time, peak_threshold, peak_min_dist, index_diff_threshold,
                 show_plot=False, annotate=True):
    timestamps = []
    x_data = []
    y_data = []
    z_data = []

    t0 = None
    x0 = None
    y0 = None
    z0 = None

    if end_time is None:
        end_time = 1E10

    with open(file_path) as file:
        reader = csv.reader(file)

        for row in reader:
            t, x, y, z = tuple(map(float, row))
            if t0 is None:
                t0 = t
            t -= t0

            if start_time <= t <= end_time:
                if x0 is None:
                    x0 = x
                if y0 is None:
                    y0 = y
                if z0 is None:
                    z0 = z

                timestamps.append(t)
                x_data.append(x - x0)
                y_data.append(y - y0)
                z_data.append(z - z0)

    timestamps = np.array(timestamps)
    if axis == "x":
        disp_data = np.array(x_data)
    elif axis == "y":
        disp_data = np.array(y_data)
    else:
        disp_data = np.array(z_data)

    disp_data += abs(np.min(disp_data))
    local_max_disp, local_max_times = find_local_max(timestamps, disp_data, peak_threshold, peak_min_dist,
                                                     index_diff_threshold)

    print(local_max_times)

    average_hz = np.mean(1 / np.diff(local_max_times))
    print("average rate:", average_hz)

    new_fig()

    if annotate:
        for index, (max_disp, max_time) in enumerate(zip(local_max_disp, local_max_times)):
            plt.annotate("n=%s" % index, xy=(max_time, max_disp), xytext=(-10, 20),
                         textcoords='offset points',
                         arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    plt.plot(local_max_times, local_max_disp, '.')

    plt.xlabel("time (ms)")
    plt.ylabel("roll euler angle (radians)")

    plt.plot(timestamps, disp_data, label="%0.4fHz" % average_hz)
    plt.legend()
    plt.savefig("figures/%s.png" % file_path, dpi=200)

    if show_plot:
        plt.show()


show = False

analyze_data("data/1520187646.64607.csv", "x", 0.01, 1.3, 0.15, 10, 10, show_plot=show, annotate=False)  # max time: 5.119
analyze_data("data/1520189209.8862138.csv", "x", 0.01, 1.3, 0.05, 0.1, 1, show_plot=show, annotate=False)  # max time: 13.07
analyze_data("data/1520191062.34681.csv", "x", 3.26, 7.6, 0.55, 0.5, 1, show_plot=show, annotate=False)
analyze_data("data/1520192590.187405.csv", "x", 12.0, 14.0, 0.15, 0.1, 1, show_plot=show, annotate=False)
analyze_data("data/1520192673.6106648.csv", "x", 3.5, 5.25, 0.15, 0.1, 1, show_plot=show, annotate=False)
