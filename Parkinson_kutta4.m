function Storage = Parkinson_kutta4(A,k,b,h,step,t_final)
% This function solve a system of differential equations for a model of
% Parkinson's disease without DBS by runge kutta 4th order
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
if nargin==0 | nargin==-1 | nargin==-2 | nargin==-3 | nargin==-4 | nargin==-5 
    error('Not enough input arguments.');
elseif nargin < -6
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

Y = [0.01; 0.01];                       % initial conditions of x and y
Storage = zeros(length(t),5);           % creation array to store the result
Storage(1,:) = [time Y(1) Y(2) 0 0];    % init first column of the result (initial conditions)  


%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------
%% Runge Kutta 4th order algorithm
%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------


for i = 1:(length(t)-1)
    
  % evaluate k1 using z    
  k1 = step*[Y(2)-((2*b*Y(1))-((2/pi)*k*atan(Y(1)/h))); -((b*b*Y(1))+A)];
      Z = Y + (0.5*k1); % updating intermediate z
  % evaluate k2 using z      
  k2 = step*[Z(2)-((2*b*Z(1))-((2/pi)*k*atan(Z(1)/h))); -((b*b*Z(1))+A)];
      Z = Y + (0.5*k2); % update intermediate z 
  % evaluate k3 using z    
  k3 = step*[Z(2)-((2*b*Z(1))-((2/pi)*k*atan(Z(1)/h))); -((b*b*Z(1))+A)];
      Z = Y + (step*k3); % update intermediate z
  % evaluate k4 using z      
  k4 = step*[Z(2)-((2*b*Z(1))-((2/pi)*k*atan(Z(1)/h))); -((b*b*Z(1))+A)];
  
    % final approximation of the Y vector
    Y = Y + ((step/6)*(k1+(2*k2)+(2*k3)+k4));
  
    time = time + step;                     % updating time, using old step
    Storage(i+1,:) = [time Y(1) Y(2) 0 0];  % updating y, using old y
    
%     A = 0; % A is just a "pulse"
    
end


%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------
%% Calculation x_dot and y_dot using for loop
%-----------------------------------------------------------------------------------
%-----------------------------------------------------------------------------------


for i = 1:length(t)
    
    % Caluclate x_dot
    x_dot = Storage(i,3) - ((2*b*Storage(i,2)) - ((2/pi)*k*atan(Storage(i,2)/h)));
    Storage(i,4) = x_dot;   % x_dot stored in Storage(i,4)
    
    % Calculate y_dot
    y_dot = (-b*b*Storage(i,2)) + A;
    Storage(i,5) = y_dot;   % y_dot stored in Storage(i,5)
    
end