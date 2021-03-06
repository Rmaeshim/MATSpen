close all
clear all

% sample_time = 0.1;
sample_time = 0.013;
freq1 = 5.0;
opt = c2dOptions('Method', 'tustin', 'PrewarpFrequency', freq1);
s = tf('s');

% generated by analyzing root locus output plot from simulink model
C_w1 = s + 0.1 + 2*pi * freq1 * 1i;
C = (C_w1) * conj(C_w1) / (s^2 + (2*pi * freq1)^2);

controller_discrete = c2d(C, sample_time, opt)
[num, den] = tfdata(controller_discrete);
A = num{:}  % numerator of pid_discrete
B = den{:}  % denominator of pid_discrete

final_time = 10;
input_time = 0:sample_time:final_time;
X = sin(0.5 * freq1 * input_time);
[Y, Zf] = filter(A, B, X); % runs the difference equation, A & B are the controller in discrete time domain, X is the input function

% a(1) = 1.0013, a(2) = -1.8960, a(3) = 0.9987
% b(1) = 1.0000, b(2) = -1.8960, b(3) = 1.0000
% a(1)*y(n) = b(1)*x(n) + b(2)*x(n-1) + ... + b(nb+1)*x(n-nb)
%                           - a(2)*y(n-1) - ... - a(na+1)*y(n-na)
% y(n) = b(1) / a(1) * x(n) + b(2) / a(1) * x(n - 1) + b(3) / a(1) * x(n - 2)
%                           - a(2) / a(1) * y(n - 1) - a(3) / a(1) * y(n - 2)

hold on
figure(1)
plot(input_time, Y, 'LineWidth', 4)
plot(input_time, X, 'LineWidth', 2)
