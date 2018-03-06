import csv
import peakutils
import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize
from scipy import signal

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


def retrieve_data(file_path, selected_axis, start_time, end_time):
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

    with open("data/" + file_path) as file:
        reader = csv.reader(file)

        for row in reader:
            row = tuple(map(float, row))
            t = row[0]

            if t0 is None:
                t0 = t
            t -= t0

            if start_time <= t <= end_time:
                timestamps.append(t)

                if len(row) >= 2:
                    x = row[1]
                    if x0 is None:
                        x0 = x
                    x_data.append(x - x0)

                if len(row) >= 3:
                    y = row[2]
                    if y0 is None:
                        y0 = y
                    y_data.append(y - y0)

                if len(row) >= 4:
                    z = row[3]
                    if z0 is None:
                        z0 = z
                    z_data.append(z - z0)

    timestamps = np.array(timestamps)
    x_data = np.array(x_data)
    y_data = np.array(y_data)
    z_data = np.array(z_data)

    return timestamps, x_data, y_data, z_data


def optimize_func(timestamps, x0, x1, x2, x3, x4, x5, x6, x7):
    # timestamps, disp_data = args
    sine1 = x0 * np.sin(timestamps * x1 + x2) + x3
    sine2 = x4 * np.sin(timestamps * x5 + x6) + x7

    return sine1 + sine2


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = signal.lfilter(b, a, data)
    return y


def curve_fit_sine_data(file_path, selected_axis=0, start_time=0, end_time=None):
    timestamps, x_data, y_data, z_data = retrieve_data(file_path, selected_axis, start_time, end_time)
    axes = [x_data, y_data, z_data]
    disp_data = np.array(axes[selected_axis])

    disp_data -= disp_data[0]
    # disp_data += abs(np.min(disp_data))

    sampling_rate = 1 / np.mean(np.diff(timestamps))

    # b, a = signal.butter(11, 0.03)
    # zi = signal.lfilter_zi(b, a)
    # z, _ = signal.lfilter(b, a, disp_data, zi=zi * disp_data[0])
    # z2, _ = signal.lfilter(b, a, z, zi=zi * z[0])
    # disp_data_filtered = signal.filtfilt(b, a, disp_data)

    # disp_data_filtered = signal.savgol_filter(disp_data, 25, 11)

    disp_data_filtered = butter_lowpass_filter(disp_data, 6.0, sampling_rate)

    x_guess = np.array([3.7, 40, np.pi / 0.25, -1.44555422e+05, 2.8, 20, np.pi / 0.2, 1.44562866e+05])

    popt, pcov = optimize.curve_fit(optimize_func, timestamps, disp_data_filtered, x_guess)
    print(popt)

    fitted_disp = optimize_func(timestamps, *popt)

    freq = np.fft.fftfreq(timestamps.shape[-1], np.mean(np.diff(timestamps)))
    sp = np.fft.fft(disp_data_filtered)

    new_fig()
    plt.plot(timestamps, fitted_disp, label="curve fit")
    # plt.plot(timestamps, optimize_func(timestamps, *x_guess), label="initial guess")
    plt.plot(timestamps, disp_data_filtered, label="filtered")
    plt.plot(timestamps, disp_data, label="original", linewidth=0.1)
    plt.legend()

    new_fig()
    plt.plot(freq, abs(sp))

    plt.show()


def analyze_data(file_path, selected_axis, start_time, end_time, peak_threshold, peak_min_dist, index_diff_threshold,
                 show_plot=False, annotate=True):
    timestamps, x_data, y_data, z_data = retrieve_data(file_path, selected_axis, start_time, end_time)
    axes = [x_data, y_data, z_data]
    disp_data = np.array(axes[selected_axis])

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

    new_fig()

    freq = np.fft.fftfreq(timestamps.shape[-1], np.mean(np.diff(timestamps)))
    sp = np.fft.fft(disp_data)

    plt.plot(freq, abs(sp))

    if show_plot:
        plt.show()


show = True

# analyze_data("1520187646.64607.csv", 0, 0.01, 1.3, 0.15, 10, 10, show_plot=show, annotate=False)  # max time: 5.119
# analyze_data("1520189209.8862138.csv", 0, 0.01, 1.3, 0.05, 0.1, 1, show_plot=show, annotate=False)  # max time: 13.07
# analyze_data("1520191062.34681.csv", 0, 3.26, 7.6, 0.55, 0.5, 1, show_plot=show, annotate=False)
# analyze_data("1520192590.187405.csv", 0, 12.0, 14.0, 0.15, 0.1, 1, show_plot=show, annotate=False)
# analyze_data("1520192673.6106648.csv", 0, 3.5, 5.25, 0.15, 0.1, 1, show_plot=show, annotate=False)
# analyze_data("1520358081.516809.csv", 0, 0.2, 7.7, 0.15, 0.1, 1, show_plot=show, annotate=False)
# analyze_data("Upper Left.csv", 0, 0, None, 0.15, 0.1, 1, show_plot=show, annotate=False)

# curve_fit_sine_data("Upper Left.csv")
