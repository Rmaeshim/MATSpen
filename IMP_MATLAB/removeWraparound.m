%removes angle wraparound for z data

function zNew = removeWraparound(zOld)
    zNew = zeros(size(zOld));
    for i = 1:length(zOld)
        if (zNew(i)>pi)
            zNew(i) = zNew(i) - 2*pi;
        end
    end
end