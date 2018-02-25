function Storage = Parkinson_euler(A,k,b,h,step,t_final)
% This function solve a system of differential equations for a model of
% Parkinson's disease without DBS using euler's method
% A is the amplitude of the "pulse"
% k Represents the gain, the connectivity of the neurons in the network and
% must be greater than 800 and smaller than 1600
% b is the frequency of the resulting oscillations
% h is the level of Dopamine
% step is the time step of the simulation
% t_final is the final time of the simulation
% The output is an array in which values of the system are stored

%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------
%% error detection
%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------


% for the number of input
if nargin==0 | nargin==-1 | nargin==-2 | nargin==-3 | nargin==-4 
    error('Not enough input arguments.');
elseif nargin < -5
    error('Too many intput arguments.');
    
% for parameter's value
elseif k <= 800 | k >= 1600
    error('Represents the connectivity of the neurons in the network and must be between 800 and 1600.');
elseif b <= 8*pi | b >= 12*pi
    error('Frequency must be greater than 8*pi and smaller than 12*pi.');
elseif h <= 0 | h >= 1
    error('Level of Dopamine must be between 0 and 1.');
elseif step <= 0
    error('Step time must be greater than 0.');
elseif t_final <= 0
    error('Final time must be greater than 0.');
end


%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------
%% Initialisation
%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------


t = [0:step:t_final];   % to get the size of Storage
time = 0;               % init time

Y = [0.01; 0.01];                       % initial conditions for x and y
Storage = zeros(length(t),5);           % creation array to store the result
Storage(1,:) = [time Y(1) Y(2) 0 0];    % init first column of the result (initial conditions)


%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------
%% Euler algorithm
%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------


for i = 2:(length(t))

% updating x
Storage(i,2) = Storage(i-1,2) + step*(Storage(i-1,3)-((Storage(i-1,2)*2*b)-((2/pi)*k*atan(Storage(i-1,2)/h))));
% updating y
Storage(i,3) = Storage(i-1,3) + step*((-b*b*Storage(i-1,2))+A);
% updating time
Storage(i,1) = Storage(i-1,1) + step;
% A = 0;  % A is just a "pulse"
end


%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------
%% Calculation x_dot and y_dot using for loop
%-----------------------------------------------------------------------------------
%------------------------------------------------------------------------
%------------------------------------------------------------------------

for i = 1:length((t))
    
    % Caluclate x_dot
    x_dot = Storage(i, 3) - ((2*b*Storage(i, 2)) - ((2/pi)*k*atan(Storage(i,2)/h)));
    Storage(i,4) = x_dot;   % x_dot stored in Storage(i,4)
    
    % Calculate y_dot
    y_dot = (-b*b*Storage(i,2)) + A;
    Storage(i,5) = y_dot;   % y_dot stored in Storage(i,5)
    
end