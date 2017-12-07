import serial
import re


class PTUSerial:
    '''
        This is a direct access object for the PTU
        This allows for writing of custom commands to the PTU or the use
        of existing formatted functions

        No error checking of input is done within this object and will do
        exactly as you tell it to
    '''

    def __init__(self, port, baudrate):
        # Serial object user for interfacing
        self.serialObj = serial.Serial(port=port, baudrate=baudrate)

        # Resolution
        self.panRes = self.get_pan_res()
        self.tiltRes = self.get_tilt_res()
    # Write message to PTU, return reflected message
    def write(self, msg):
        self.serialObj.write(msg)
        retString = ""

        # Read until \n found
        while 1:
            if self.serialObj.inWaiting() > 0:
                s = self.serialObj.read()
                retString += s
                if s == "\n":
                    return retString

    def stop(self):
        self.write("H ")

    def close(self):
        if self.serialObj is not None:
            self.serialObj.close()

    ''' Set position commands '''
    # return a string based on pan success
    def set_pan(self, pan):
        retString = self.write("pp" + str(int(pan)) + " ")
        return retString

    # return a string based on pan success
    def set_pan_deg(self, panDeg):
        retString = self.write("pp" + str(self.deg_to_pan(panDeg)) + " ")
        return retString

    # return a string based on tilt success
    def set_tilt(self, tilt):
        retString = self.write("tp" + str(int(tilt)) + " ")
        return retString

    def set_tilt_deg(self, tiltDeg):
        retString = self.write("tp" + str(self.deg_to_tilt(tiltDeg)) + " ")
        return retString


    ''' Set speed commands '''
    # Return a string based on pan speed success
    def set_pan_speed(self, speed):
        retString = self.write("ps" + str(int(speed)) + " ")
        return retString

    def set_pan_speed_deg(self, speedDeg):
        retString = self.write("ts" + str(self.deg_to_pan(speedDeg)) + " ")
        return retString

    # return a string based on tilt speed success
    def set_tilt_speed(self, speed):
        retString = self.write("ts" + str(int(speed)) + " ")
        return retString

    def set_tilt_speed_deg(self, speedDeg):
        retString = self.write("ts" + str(self.deg_to_tilt(speedDeg)) + " ")
        return retString

    ''' Resolution commands '''
    # Get pan resolution (seconds arc per step)
    def get_pan_res(self):
        retString = self.write("pr ")
        self.panRes = self.float_from_string(retString)
        return self.panRes

    # Get tilt res (seconds arc per step)
    def get_tilt_res(self):
        retString = self.write("tr ")
        self.tiltRes = self.float_from_string(retString)
        return self.tiltRes


    ''' Max/Min commands '''
    # Get min pan position in counts
    def get_min_pan(self):
        retString = self.write("pn ")
        return self.float_from_string(retString)

    # Get max pan position in counts
    def get_max_pan(self):
        retString = self.write("px ")
        return self.float_from_string(retString)

    # Get min tilt position in counts
    def get_min_tilt(self):
        retString = self.write("tn ")
        return self.float_from_string(retString)

    # Get max tilt position in counts
    def get_max_tilt(self):
        retString = self.write("tx ")
        return self.float_from_string(retString)

    # Get min pan position in degrees
    def get_min_pan_deg(self):
        return self.pan_to_deg(self.get_min_pan())

    # Get max pan position in degrees
    def get_max_pan_deg(self):
        return self.pan_to_deg(self.get_max_pan())

    # Get min tilt position in degrees
    def get_min_tilt_deg(self):
        return self.tilt_to_deg(self.get_min_tilt())

    # Get max tilt position in degrees
    def get_max_tilt_deg(self):
        return self.tilt_to_deg(self.get_max_tilt())


    ''' Get position commands '''
    # Get the current pan position in counts
    def get_pan(self):
        retString = self.write("pp ")
        return self.float_from_string(retString)

    # Get the current pan position in degrees
    def get_pan_deg(self):
        return self.pan_to_deg(self.get_pan())

    # Get the current tilt position in counts
    def get_tilt(self):
        retString = self.write("tp ")
        return self.float_from_string(retString)

    # Get the current tilt position in degrees
    def get_tilt_deg(self):
        return self.tilt_to_deg(self.get_tilt())


    ''' Get speed commands '''
    # Get pan speed in counts/s
    def get_pan_speed(self):
        retString = self.write("ps ")
        return self.float_from_string(retString)

    # Get pan speed in degrees/s
    def get_pan_speed_deg(self):
        return self.pan_to_deg(self.get_pan_speed())

    # Get tilt speed in counts/s
    def get_tilt_speed(self):
        retString = self.write("ts ")
        return self.float_from_string(retString)

    # Get tilt speed in degrees/s
    def get_tilt_speed_deg(self):
        return self.tilt_to_deg(self.get_tilt_speed())

    ''' Position and instantaneous speed'''
    # get the current positions and instantaneous speeds as a list
    def get_pos_and_inst_speed(self):
        retString = self.write("B ")
        fl = self.floats_from_string(retString)
        return fl


    ''' Mode change '''
    # Change the operating mode
    def change_pan_mode(self, mode, cspeed=500):
        self.set_pan_speed(cspeed)
        checkString = self.write("WP ")
        if str(mode) not in checkString:
            retString = self.write("WP" + str(mode) + " ")
            return retString
        return None

    def change_tilt_mode(self, mode, cspeed=500):
        self.set_tilt_speed(cspeed)
        checkString = self.write("WT ")
        if str(mode) not in checkString:
            retString = self.write("WT" + str(mode) + " ")
            return retString
        return None

    def calibrate(self, cspeed=1000):
        self.set_pan_speed(cspeed)
        self.set_tilt_speed(cspeed)
        self.write("R ")


    def pan_to_deg(self, pan):
        return float(pan) * self.panRes / 3600

    def tilt_to_deg(self, tilt):
        return float(tilt) * self.tiltRes / -3600

    def deg_to_pan(self, panDeg):
        return int(3600 * float(panDeg) / self.panRes)

    def deg_to_tilt(self, tiltDeg):
        return int(-3600 * float(tiltDeg) / self.tiltRes)

    def float_from_string(self, string):
        fl = self.floats_from_string(string)
        if len(fl) > 0:
            return float(fl[0])
        else:
            return None

    def floats_from_string(self, string):
        string = str(string)  # Ensure string
        fl = re.findall("[-+]?\d*\.\d+|[-+]?\d+", string)
        if len(fl) > 0:
            return fl
        else:
            return None
