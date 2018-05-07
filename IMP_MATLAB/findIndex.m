%Iterates through Data
%returns the index of the first value in Data >= Target
%Assume Data's value is increasing 
%Ideally working with Time
function I = findIndex(Data,Target)
    for i = 1:length(Data)
            if Data(i) >= Target
                I = i;
                break;
            end
    end
    