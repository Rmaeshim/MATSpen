function [] = plant_identification()
    close all
    clear all

    [sensor_timestamps, sensor_angle_x, sensor_angle_y, sensor_angle_z] = read_sensor_data( ...
        'data/2018_Apr_15/chirp, 3.0-6.4Hz 20_51_15 2018_Apr_15-BNO055.csv', ...
        7.61, 40.9 ...
    );
    [motor_timestamps, frequency_rps] = read_motor_data( ...
        'data/2018_Apr_15/chirp, 3.0-6.4Hz 20_51_15 2018_Apr_15-TB6612.csv', ...
        7.61, 40.9 ...
    );

    % [sensor_timestamps, sensor_angle_x, sensor_angle_y, sensor_angle_z] = read_sensor_data( ...
    %     'data/2018_Apr_15/constant, 6.4Hz 20_52_03 2018_Apr_15-BNO055.csv', ...
    %     9.036, 18.890824 ...
    % );
    % [motor_timestamps, frequency_rps] = read_motor_data( ...
    %     'data/2018_Apr_15/constant, 6.4Hz 20_52_03 2018_Apr_15-TB6612.csv', ...
    %     9.036, 18.890824 ...
    % );

    % [sensor_timestamps, sensor_angle_x, sensor_angle_y, sensor_angle_z] = read_sensor_data( ...
    %     'data/2018_Apr_15/random, 0-6.4Hz 20_50_28 2018_Apr_15-BNO055.csv', ...
    %     11.045356, 40.32006 ...
    % );
    % [motor_timestamps, frequency_rps] = read_motor_data( ...
    %     'data/2018_Apr_15/random, 0-6.4Hz 20_50_28 2018_Apr_15-TB6612.csv', ...
    %     11.045356, 40.32006 ...
    % );
    moving_avg_sensors = 7;
    moving_avg_motor = 7;
    sample_time = 1/75;

    sensor_ang_vel = movmean(diff(sensor_angle_x), moving_avg_sensors) ./ diff(sensor_timestamps);
    ang_vel_sensor_timestamps = sensor_timestamps(1:end - 1);
    sensor_ang_accel = movmean(diff(sensor_ang_vel), moving_avg_sensors) ./ diff(ang_vel_sensor_timestamps);
    ang_acc_sensor_timestamps = ang_vel_sensor_timestamps(1:end - 1);

    angular_acceleration_rad2_per_s = movmean(diff(frequency_rps), moving_avg_motor) ./ diff(motor_timestamps);
    moment_of_inertia_bolt = 0.1;
    input_torque = moment_of_inertia_bolt * angular_acceleration_rad2_per_s;

    % [sim_system_response, sim_time, sim_state_space_input, downsampled_input_signal] = run_simulations(ang_acc_sensor_timestamps, input_torque, sensor_ang_accel, sample_time);
    [sim_system_response, sim_time, sim_state_space_input, downsampled_input_signal] = run_simulations(ang_vel_sensor_timestamps, frequency_rps, sensor_ang_vel, sample_time);
    % [sim_system_response, sim_time, sim_state_space_input, downsampled_input_signal] = run_simulations(sensor_timestamps, frequency_rps, sensor_angle_x, sample_time);

    figure(1);
    plot(ang_vel_sensor_timestamps, sensor_ang_vel);
    title('sensed angular velocity');

    figure(2);
    plot(motor_timestamps, frequency_rps);
    title('input motor frequency');

    figure(3);
    plot(sim_time, sim_system_response);
    title('simulated sensed output');

    figure(4);
    plot(sensor_timestamps, sensor_angle_x);
    title('sensed angular position');

end

function [sim_system_response, sim_time, sim_state_space_input, downsampled_input_signal] = run_simulations(timestamps, input_signal, output_signal, sample_time)
    downsampled_input_signal = resample(input_signal, length(timestamps), length(input_signal));

    system_data = iddata(output_signal, downsampled_input_signal, sample_time);
    detrended_system_data = detrend(system_data);
    % identified_sys = n4sid(system_data, 2);
    identified_sys = ssest(detrended_system_data, 2, 'Ts', sample_time)

    sim_time = (0:length(input_signal) - 1) * sample_time;
    [sim_system_response, sim_time, sim_state_space_input] = lsim(identified_sys, input_signal, sim_time);

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

function [timestamps, frequency] = read_motor_data(filename, start_time, end_time)
    data = csvread(filename);
    timestamps = data(:, 2);

    start_index = get_index(start_time, timestamps);
    end_index = get_index(end_time, timestamps);

    timestamps = timestamps(start_index:end_index);
    frequency = data(start_index:end_index, 4);
end
