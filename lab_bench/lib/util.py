from enum import Enum

class RoundMode(Enum):
    UP = "up"
    DOWN = "down"
    NEAREST = "nearest"

def find_closest(array,value,round_mode):
    sel_value = None
    if round_mode == RoundMode.NEAREST:
        dist,sel_value = min(map(lambda cv: (abs(cv-value),cv), array), \
                             key=lambda pair:pair[0])


    elif round_mode == RoundMode.UP:
        s_array = sorted(array)
        for curr_val in array:
            if curr_val >= value and sel_value is None:
                sel_value = curr_val
        dist = abs(value-sel_value)

    elif round_mode == RoundMode.DOWN:
        s_array = sorted(array,reverse=True)
        for curr_val in array:
            if curr_val >= value and sel_value is None:
                sel_value = curr_val
        dist = abs(value-sel_value)

    return dist,sel_value

