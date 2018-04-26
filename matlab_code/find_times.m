
function [start_time, end_time] = find_times(file_path, data_source)
    data = csvread(file_path);

    timestamps = data(:, 2);
    frequency = data(:, 4);

    plot(timestamps, frequency);
    [clicked_times, clicked_y] = ginput(2);

    start_time = clicked_times(1);
    end_time = clicked_times(2);
end
