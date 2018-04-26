function [ang_vel_sensor_timestamps, sensor_ang_vel, downsampled_torque_hand, sample_time] = data_pruning( ...
        sensor_file_path, motor_file_path, start_time, end_time, sensor_axis ...
    )

    moving_avg_sensors = 4;

    [sensor_timestamps, sensor_angle_x, sensor_angle_y, sensor_angle_z] = read_sensor_data(sensor_file_path, start_time, end_time);
    [motor_timestamps, motor_position, motor_frequency] = read_motor_data(motor_file_path, start_time, end_time);

    if (sensor_axis == 'x')
        sensor_ang_vel = movmean(diff(sensor_angle_x), moving_avg_sensors) ./ diff(sensor_timestamps);
    elseif (sensor_axis == 'y')
        sensor_ang_vel = movmean(diff(sensor_angle_y), moving_avg_sensors) ./ diff(sensor_timestamps);
    elseif (sensor_axis == 'z')
        sensor_ang_vel = movmean(diff(sensor_angle_z), moving_avg_sensors) ./ diff(sensor_timestamps);
    end
    ang_vel_sensor_timestamps = sensor_timestamps(1:end - 1);

    torque_hand = compute_torque(motor_position, motor_frequency, 0, pi / 4);

    downsampled_torque_hand = resample(torque_hand, length(ang_vel_sensor_timestamps), length(torque_hand));
    sample_time = mean(diff(sensor_timestamps));
end

function [index] = get_index(timestamp, times)
    [matched_timestamp, index] = min(abs(times - timestamp));
end

function [timestamps, x, y, z] = read_sensor_data(filename, start_time, end_time)
    data = csvread(filename);
    timestamps = data(:, 2);
    start_index = get_index(start_time, timestamps);
    end_index = get_index(end_time, timestamps);

    timestamps = timestamps(start_index:end_index);
    x = data(start_index:end_index, 3);
    y = data(start_index:end_index, 4);
    z = data(start_index:end_index, 5);
end

function [timestamps, position, frequency] = read_motor_data(filename, start_time, end_time)
    data = csvread(filename);
    timestamps = data(:, 2);

    start_index = get_index(start_time, timestamps);
    end_index = get_index(end_time, timestamps);

    timestamps = timestamps(start_index:end_index);
    position = data(start_index:end_index, 3);
    frequency = data(start_index:end_index, 4);
end
