% MATS
% Internal Model Principle (IMP)

clear all; close all; clc;

%% Tremor Input
% Constant: 6.4 Hz
sensor3 = csvread('constant, 6.4Hz 20_52_03 2018_Apr_15-BNO055.csv');
t3_start = 9.2; %sec
t3_end = 18.8; %sec
%find Indices of corresponding start and end times in motor & sensor data
is3s = findIndex(sensor3(:,2),t3_start);
is3e = findIndex(sensor3(:,2),t3_end);
%trim data to desired rangeio
sensor3 = sensor3(is3s:is3e, :);

sensorTime = sensor3(:,2);
sensorTime = sensorTime - sensorTime(1); %make the time start at 0; 
sensorEndTime = sensorTime(end);

sensorTremor_pos_X = sensor3(:,3);
sensorTremor_pos_Y = sensor3(:,4);
sensorTremor_pos_Z = sensor3(:,5);
% remove z angle wraparounds
sensorTremor_pos_Z = removeWraparound(sensorTremor_pos_Z);

% differentiate to get angular velocity
mmNum = 4;
sensorTremor_vel_Y = differentiate(sensorTremor_pos_Y,sensorTime, mmNum);

% adjust size of time vector to match velocity vector
sensorTime = sensorTime(1:end-1);

tremorIn = zeros(length(sensorTime), 2);
tremorIn(:,1) = sensorTime;
tremorIn(:,2) = sensorTremor_vel_Y;

%% Determine Frequency of Tremor
% https://www.mathworks.com/help/matlab/ref/fft.html

T = mean(diff(sensorTime)); %Sampling Time
Fs = 1/T;                   % Sampling frequency  
L = length(sensorTime);     % Length of signal
t = (0:L-1)*T;              % Time vector

f = Fs*(0:(L/2))/L;
Y = fft(sensorTremor_vel_Y);
P2 = abs(Y/L);
P1 = P2(1:L/2+1);
P1(2:end-1) = 2*P1(2:end-1);

figure();
plot(f,P1);
title('Single-Sided Amplitude Spectrum of Sensor Tremor');
xlabel('f (Hz)'); ylabel('|P1(f)|');

smallw_offset = 20;
[m, Index] = max(P1(smallw_offset:end));

freq1 = f(Index + smallw_offset);
freq2 = 5.5;

%freq1 = 5;
%% Define Plant and Controller

% Simplify Plant as a
% % Mass-Spring-Damper System
% m = 0.3; 
% b = 0.1; 
% k = 2;
% G = tf(1, [m b k]);

s = tf('s');

%G = (0.08848*s - 11.55)/(s+2.27);% * exp(-0.114*s);
%G = (-0.02518*s^4 + 1.035*s^3 - 2.916*s^2 + 24.37*s + 17.81)/(s^4 + 10.8*s^3 + 17.96*s^2 + 9.374*s + 1.896);
%G = (-0.5197*s - 0.7341 ) / (s^2 + 1.403*s + 0.2266);
%G = (3.038*s + 8.818)/ (s^3 + 3.975*s^2 + 3.487*s + 0.7679);
%G = (8.239*s + 23.91) / (s^3 + 3.974*s^2 + 3.486*s + 0.7674); %TF2
%G = exp(-0.119*s)* (4.891*s + 17.09)/(s^3 + 4.67*s^2 + 4.312*s + 2.542); %TF1
%G = (1.835*s - 26.99)/(s^2 + 0.1042*s + 1390);
random_3p2z = (95.93*s^2 + 410*s + 8.408e04) / (s^3 + 58.88*s^2 + 1941*s + 8.086e04);
random1615_3p2z = (-97.28*s^2 - 1.97e04*s - 3.097e05) / (s^3 + 228.6*s^2 + 566.5*s + 4.957e04);
G = random_3p2z;
%G = random1615_3p2z;
[z, p, k] = zpkdata(G);

%%%%%%%%%C1 = (s+8+2*pi*freq1*1i)* conj(s+8+2*pi*freq1*1i)/(s^2+(2*pi*freq1)^2);

C_w1 = s+2+2*pi*freq1*1i;
C1 = (C_w1)* conj(C_w1)/(s^2+(2*pi*freq1)^2);
C2 = 1; %(s+3+2*pi*freq2*1i)*conj(s+3+2*pi*freq2*1i)/(s^2+(2*pi*freq2)^2);
C3 = 1; %(s+60)/(s+80);
C = C1*C2*C3;

sample_time = 0.0001; %0.013;
freq1 = 4.0;
opt = c2dOptions('Method', 'tustin', 'PrewarpFrequency', freq1);
controller_discrete = c2d(C, sample_time, opt);
controller_continuous = d2c(controller_discrete);
C = controller_continuous;

%http://ctms.engin.umich.edu/CTMS/index.php?example=MotorSpeed&section=SystemModeling
m_bolt = 0.0368544;
L_bolt = 0.0454;
i_motor = 0.360; %current
torque_motor = 0.064; %stall torque
V_motor = 0.2831; %back emf voltage
J = m_bolt*((L_bolt/2)^2); %rotor moment of inertia
b = 0.1; %motor viscous friction constant
K = torque_motor/i_motor; %electromotive force constant/motor torque constant
R = 16.667; %electric resistance
L = 0.5; %electric inductance
s = tf('s');
M = K/((J*s+b)*(L*s+R)+K^2);
%M = 1;

% figure();
% rlocus(C);
figure();
rlocus(C*G);
figure();
rlocus(C*G*M);
% TO TUNE
K = 2; %0.53; %37.1; %297; %2.15*10^3; %3.44*10^4;

%% Run Simulink
sim('IMP2');

%% Plot
figure();
subplot(3,1,1)
plot(simTime, yOut);
xlabel('Time (s)'); ylabel('yOut');
subplot(3,1,2)
plot(simTime, tremorSim);
xlabel('Time (s)'); ylabel('TremorSim');
subplot(3,1,3)
plot(simTime, yRef-yOut);
xlabel('Time (s)'); ylabel('Error');

figure();
plot(simTime, command);
xlabel('Time (s)'); ylabel('command');
title('Controller Command');

figure();
plot(simTime, plantOut);
xlabel('Time (s)'); ylabel('plantOut');
title('plantOutput');

%fft_plot()

figure();
plot(simTime, controllerIn, simTime, command);
legend('Controller Input', 'Controller Output');

