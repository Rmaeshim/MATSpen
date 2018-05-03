close all
clear all

% sample_time = 0.1;
sample_time = 0.013;
opt = c2dOptions('Method', 'tustin', 'PrewarpFrequency', 6.0307);
s = tf('s');
kp = 10;
kd = 1;
ki = 1;
plant = 1 / (s^2 + s + 1);
pid_controller = kp + ki / s + kd * s;
pid_system = feedback(plant * pid_controller, 1);
disp('feedback system created')

pid_discrete = c2d(pid_system, sample_time, opt)
% pid_discrete = c2d(pid_system, sample_time);
disp('discrete computed')

[num, den] = tfdata(pid_discrete);
F = num{:}  % numerator of pid_discrete
B = den{:}  % denominator of pid_discrete
% A = [1];
%
% M = idpoly(A, {B, F}, 'NoiseVariance', sample_time);
% [poly_a, poly_b, poly_c, poly_d, poly_e] = polydata(M);

[step_Y, step_T, step_X] = step(pid_system);
disp('step response computed')
final_time = step_T(end);
X = ones(1, round(final_time / sample_time));
[Y, Zf] = filter(F, B, X); % runs the difference equation, A & B are the controller in discrete time domain, X is the input function
disp('difference equation run')

difference_equation_time = linspace(0, final_time, length(Y));

hold on
figure(1)
plot(difference_equation_time, Y, 'LineWidth', 4)
plot(step_T, step_Y, 'LineWidth', 2)
legend('difference', 'continuous')
