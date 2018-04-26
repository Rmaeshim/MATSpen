function T_hand = torquein(alpha, boltfreq, beta, theta)
    % alpha is motor shaft position
    % boltfreq is frequency of motor rotations
    % beta is angular offset of encoder with plane of hand rotation
    % theta is angular offset of bolt from vertical in plane of hand rotation

    omega = boltfreq*2*pi; %angular velocity of bolt

    r = 0.0454; %length of bolt, m
    L = 0.03; %distane from center of bolt rotation to hand
    m = 0.0368544;
    g = 9.81; %gravitational acceleration, might need to change signs

    phi = alpha + beta;
    Fc = m*omega.^2*(r/2); %centripetal force around center of bolt
    F = Fc.*cos(phi); %component of Fc in plane of hand rotation
    Fg = m*g.*sin(theta); %component of weight that contributes to torque
    T_hand = (F + Fg)*L; %torque around hand (input to controller)
end
