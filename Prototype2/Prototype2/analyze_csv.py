import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    return ret / n
    # ret[n:] = ret[n:] - ret[:-n]
    # return ret[n - 1:] / n


def find_bounding_indices(times, start_time, end_time):
    start_index = np.argmin(np.abs(times - start_time))
    end_index = np.argmin(np.abs(times - end_time))
    return start_index, end_index


def main(file_path):
    with open(file_path) as file:
        reader = csv.reader(file)

        timestamps = []
        angular_position = []

        for row in reader:
            index, timestamp, x, y, z = row

            timestamps.append(float(timestamp))
            angular_position.append(float(x))

    timestamps = np.array(timestamps)
    angular_position = np.array(angular_position)

    # start_index, end_index = find_bounding_indices(timestamps, 7.54, 41.1617)
    start_index, end_index = find_bounding_indices(timestamps, 8.87, 19.01)
    timestamps = timestamps[start_index:end_index]
    angular_position = angular_position[start_index:end_index]

    plt.figure(1)

    y_spl = UnivariateSpline(timestamps, angular_position, s=0.001, k=4)

    plt.plot(timestamps, y_spl(timestamps))
    plt.plot(timestamps, angular_position)

    plt.figure(2)

    freq = np.fft.fftfreq(len(timestamps), np.mean(np.diff(timestamps)))
    fft = abs(np.fft.fft(y_spl(timestamps)))
    indices = (0.1 < freq) & (freq < 20.0)
    freq = freq[indices]
    fft = fft[indices]
    plt.plot(freq, fft)

    plt.figure(3)

    # y_spl_1d = y_spl.derivative(n=1)
    # plt.plot(timestamps, y_spl_1d(timestamps))
    y_spl_2d = y_spl.derivative(n=2)
    plt.plot(timestamps, y_spl_2d(timestamps))

    plt.show()


# main('data/chirp, 3.0-6.4Hz 20_51_15 2018_Apr_15-BNO055.csv')
main('data/constant, 6.4Hz 20_52_03 2018_Apr_15-BNO055.csv')
