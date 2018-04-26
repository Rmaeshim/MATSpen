clear all
close all
clc

% ----------

sensor_file_path = 'data/2018_Apr_15/constant, 6.4Hz 20_52_03 2018_Apr_15-BNO055.csv';
motor_file_path = 'data/2018_Apr_15/constant, 6.4Hz 20_52_03 2018_Apr_15-TB6612.csv';

% [start_time, end_time] = find_times(motor_file_path)
start_time = 9.0415;
end_time = 18.8848;

[const_timestamps, const_ang_vel, const_input_torque, const_sample_time] = data_pruning(sensor_file_path, motor_file_path, start_time, end_time, 'x');

% ----------

sensor_file_path = 'data/2018_Apr_15/chirp, 3.0-6.4Hz 20_51_15 2018_Apr_15-BNO055.csv';
motor_file_path = 'data/2018_Apr_15/chirp, 3.0-6.4Hz 20_51_15 2018_Apr_15-TB6612.csv';

% [start_time, end_time] = find_times(motor_file_path)
start_time = 7.7506;
end_time = 40.9303;

[chirp_timestamps, chirp_ang_vel, chirp_input_torque, chirp_sample_time] = data_pruning(sensor_file_path, motor_file_path, start_time, end_time, 'x');

% ----------

sensor_file_path = 'data/2018_Apr_15/random, 0-6.4Hz 20_50_28 2018_Apr_15-BNO055.csv';
motor_file_path = 'data/2018_Apr_15/random, 0-6.4Hz 20_50_28 2018_Apr_15-TB6612.csv';

% [start_time, end_time] = find_times(motor_file_path)
start_time = 11.2759;
end_time = 40.1008;

[random_timestamps, random_ang_vel, random_input_torque, random_sample_time] = data_pruning(sensor_file_path, motor_file_path, start_time, end_time, 'x');
