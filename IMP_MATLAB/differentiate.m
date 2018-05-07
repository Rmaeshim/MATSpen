function data_return = differentiate(data, time, mmNum)

    data_return = movmean(diff(data),mmNum) ./ diff(time);

    % don't forget to later adjust time domain size!

end