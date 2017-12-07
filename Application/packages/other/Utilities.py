import usb
import time
import re

def between(lower, val, upper):
    if lower < val < upper:
        return True
    else:
        return False

def within_pi(angle):
    angle = angle % 360

    if angle > 180:
        angle -= 360
    elif angle < -180:
        angle += 360
    return angle

def reset_connection():
    print "Restarting connections ..."
    i = 0
    dev = usb.core.find(find_all=True, idVendor=7696, idProduct=13056)
    if dev is not None:
        for d in dev:
            i += 1
            d.reset()
            time.sleep(1)
            print "\tdevice ", i, "reset"
    else:
        print "No devices found. This will be interesting"
    time.sleep(2)
    print "complete"


def toChar(v):
    if v == 0:
        s = "F"
    elif v == 1:
        s = "H"
    elif v == 2:
        s = "Q"
    elif v == 3:
        s = "E"
    else:
        s = "A"
    return s


def toInt(v):
    if v == "F":
        s = 0
    elif v == "H":
        s = 1
    elif v == "Q":
        s = 2
    elif v == "E":
        s = 3
    else:
        s = 4
    return s


def round_float(val):
    return float("{0:.2f}".format(val))

def round_float_array(array):
    ret = []
    if array is not None:
        for a in array:
            ret.append(round_float(a))
    return ret


def int_from_string(string):
    string = str(string) # Ensure string
    fl = re.findall("[-+]?\d+", string)
    if len(fl) > 0:
        return int(fl[0])
    else:
        return None


def float_from_string(string):
    string = str(string) # Ensure string
    fl = re.findall("[-+]?\d*\.\d+|[-+]?\d+", string)
    if len(fl) > 0:
        return float(fl[0])
    else:
        return None

# Determine if a value is within a range
def check_range(vRange, val):
    lower = int_from_string(str(vRange[0]))
    upper = int_from_string(str(vRange[1]))
    value = int_from_string(str(val))

    if lower is None or upper is None or value is None:
        return False
    else:
        if lower <= value <= upper:
            return True
        else:
            return False

