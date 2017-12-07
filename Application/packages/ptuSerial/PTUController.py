import time

from Transform import Tranform
from PTUSerial import PTUSerial
from .. other import Utilities as u


class PTUController:

    '''
        The controller is used to store all of the current parameters that have been
        passed to the PTUSerial object that controls motion

        This class provides a range of error checking inputs to ensure that user input
        is valid and not redundant
    '''

    def __init__(self, port, baudrate):
        # Serial object user for interfacing
        self.PTU = PTUSerial(port=port, baudrate=baudrate)
        self.transform = Tranform()

        # Ranges
        self.panRange = [-3081, 3081]
        self.panRangeDeg = [-158.00, 158.00]
        self.tiltRange = [-2324, 2324]
        self.tiltRangeDeg = [-50.00, 50.00]
        self.speedRange = [1, 4000]
        self.speedRangeDeg = [1, 400.00]

        # Current positions
        self.panPos = 0
        self.panPosDeg = 0.00
        self.tiltPos = 0
        self.tiltPosDeg = 0.00

        # Current speeds
        self.panSpeed = 1
        self.panSpeedDeg = 1
        self.tiltSpeed = 1
        self.tiltSpeedDeg = 1

        # Current Modes (NOT USED YET)
        self.panMode = "F"
        self.tiltMode = "F"

        # Perform start up queries
        self.setup()

    # Get all relevant parameters from the PTU
    def setup(self):
        self.get_pan_range()
        self.get_tilt_range()
        self.get_pan_range()
        self.get_tilt_speed()
        self.get_pan()
        self.get_tilt()
        self.get_pan_speed()
        self.get_tilt_speed()

    def close(self):
        if self.PTU.serialObj is not None:
            self.PTU.serialObj.close()


    def _input_check(self, inputString, source, rang, callback):
        ''' Generic user input tester for pan/tilt position/speed setting

            Params:
            *   inputString => desired input string for callback function
            *   source => destination for input if valid float is found
            *   range[] => range of valid input floats for the given command
            *   callback => the function to be called if inputString is valid

            Return:
            *   status =>   "Err" if invalid command
                            "OOR" if valid but out of range
                            "inputVal" if valid and in range
            *   source => the new source value if inputString is valid

            Function:
            * Takes in a user input string and determines if the input is valid for the
            callback function being used
            * Returns are either, "Err", "OOR" (out of range) or parsed float
        '''

        # Default return
        status = "Err"

        # Find float from input string
        inputFloat = u.float_from_string(inputString)

        # If float is found within input string
        if inputFloat is not None:
            # Check if value has changed (prevents redundant message sends)
            if source != inputFloat:

                # Check if the input is within the given range
                if rang is None or u.check_range(rang, inputFloat) is True:
                    # Write inputFloat to callback function and update
                    callback(inputFloat)
                    status = str(inputFloat)
                    source = inputFloat
                else:
                    # value was out of range
                    status = "OOR"
            else:
                # source and inputFloat are the same
                status = str(source)

        return status, source



    ''' Setters '''
    # return a string based on pan success
    def set_pan(self, count):
        string, self.panPos = self._input_check(str(count), self.panPos, self.panRange, self.PTU.set_pan)
        self.panPosDeg = self.pan_to_deg(self.panPos)
        return string

    # return a string based on pan success
    def set_pan_deg(self, deg):
        pan = u.float_from_string(str(deg))
        if pan is not None:
            pan = u.float_from_string(self.set_pan(self.deg_to_pan(pan)))
            if pan is not None:
                return str(u.round_float(self.pan_to_deg(pan)))
            else:
                return "Err"
        else:
            return "Err"

    # return a string based on tilt success
    def set_tilt(self, count):
        string, self.tiltPos = self._input_check(str(count), self.tiltPos, self.tiltRange, self.PTU.set_tilt)
        self.tiltPosDeg = self.tilt_to_deg(self.tiltPos)
        return string

    def set_tilt_deg(self, deg):
        tilt = u.float_from_string(str(deg))
        if tilt is not None:
            tilt = u.float_from_string(self.set_tilt(self.deg_to_tilt(tilt)))
            if tilt is not None:
                return str(u.round_float(self.tilt_to_deg(tilt)))
            else:
                return "Err"
        else:
            return "Err"

    # Return a string based on pan speed success
    def set_pan_speed(self, count):
        string, self.panSpeed = self._input_check(str(count), self.panSpeed, None, self.PTU.set_pan_speed)
        self.panSpeedDeg = self.PTU.pan_to_deg(self.panSpeed)
        return string

    def set_pan_speed_deg(self, deg):
        speed = u.float_from_string(str(deg))
        if speed is not None:
            speed = u.float_from_string(self.set_pan_speed(self.PTU.deg_to_pan(speed)))
            if speed is not None:
                return str(u.round_float(self.PTU.pan_to_deg(speed)))
            else:
                return "Err"
        else:
            return "Err"

    # return a string based on tilt speed success
    def set_tilt_speed(self, count):
        string, self.tiltSpeed = self._input_check(str(count), self.tiltSpeed, None, self.PTU.set_tilt_speed)
        self.tiltSpeedDeg = -1 * self.PTU.tilt_to_deg(self.tiltSpeed)
        return string

    def set_tilt_speed_deg(self, deg):
        # the negative ones are because speed and assumed rotation are backwards
        speed = u.float_from_string(str(deg))
        if speed is not None:
            speed = u.float_from_string(self.set_tilt_speed(self.PTU.deg_to_tilt(-1 * speed)))
            if speed is not None:
                return str(-1 * u.round_float(self.PTU.tilt_to_deg(speed)))
            else:
                return "Err"
        else:
            return "Err"

    def stop(self):
        self.PTU.stop()


    ''' Getters '''
    # Get all positions and instantaneous speed parameters (count)
    def get_pos_and_inst_speed(self):
        flList = self.PTU.get_pos_and_inst_speed()
        return tuple(flList)

    # Get all positions and instantaneous speed parameters (deg)
    def get_pos_and_inst_speed_deg(self):
        panc, tiltc, pSpeedc, tSpeedc = self.get_pos_and_inst_speed()
        pan = self.pan_to_deg(panc)
        tilt = self.tilt_to_deg(tiltc)
        pSpeed = self.pan_to_deg(pSpeedc)
        tSpeed = self.tilt_to_deg(tSpeedc)
        return pan, tilt, pSpeed, tSpeed

    # Get pan resolution (seconds arc per step)
    def get_pan_res(self):
        return self.PTU.panRes

    # Get tilt res (seconds arc per step)
    def get_tilt_res(self):
        return self.PTU.tiltRes

    # gets the pan range in counts
    def get_pan_range(self):
        # Get min pan
        retString = self.PTU.get_min_pan()
        minPan = u.int_from_string(retString)
        if minPan is None:
            minPan = self.panRange[0]

        # get max pan
        retString = self.PTU.get_max_pan()
        maxPan = u.int_from_string(retString)
        if maxPan is None:
            maxPan = self.panRange[1]

        # Set ranges in counts and degrees
        self.panRange = [minPan, maxPan]
        self.panRangeDeg = [self.pan_to_deg(minPan), self.pan_to_deg(maxPan)]
        return self.panRange

    # gets the pan range in degrees
    def get_pan_range_deg(self):
        self.get_pan_range()
        return self.panRangeDeg

    # gets the tilt range
    def get_tilt_range(self):
        # Get min pan range
        retString = self.PTU.get_min_tilt()
        minTilt = u.int_from_string(retString)
        if minTilt is None:
            minTilt = self.tiltRange[0]

        # get max pan range
        retString = self.PTU.get_max_tilt()
        maxTilt = u.int_from_string(retString)
        if maxTilt is None:
            maxTilt = self.tiltRange[1]

        self.tiltRange = [minTilt, maxTilt]
        self.tiltRangeDeg = [self.tilt_to_deg(maxTilt), self.tilt_to_deg(minTilt)]
        return self.tiltRange

    # gets the tilt range in degrees
    def get_tilt_range_deg(self):
        self.get_tilt_range()
        return self.tiltRangeDeg

    # gets pan position
    def get_pan(self):
        retString = self.PTU.get_pan()
        panPos = u.int_from_string(retString)
        if panPos is None:
            self.panPos = 0
            self.panPosDeg = 0
        else:
            self.panPos = panPos
            self.panPosDeg = self.pan_to_deg(panPos)
        return self.panPos

    # get pan position in degrees
    def get_pan_deg(self):
        self.get_pan()
        return self.panPosDeg

    # gets tilt position
    def get_tilt(self):
        retString = self.PTU.get_tilt()
        tiltPos = u.int_from_string(retString)
        if tiltPos is None:
            self.tiltPos = 0
            self.tiltPosDeg = 0
        else:
            self.tiltPos = tiltPos
            self.tiltPosDeg = self.tilt_to_deg(tiltPos)
        return self.tiltPos

    # get tilt position in degrees
    def get_tilt_deg(self):
        self.get_tilt()
        return self.tiltPosDeg

    # gets the pan speed
    def get_pan_speed(self):
        retString = self.PTU.get_pan_speed()
        panSpeed = u.int_from_string(retString)
        if panSpeed is None:
            self.panSpeed = 1
            self.panSpeedDeg = 1
        else:
            self.panSpeed = panSpeed
            self.panSpeedDeg = self.pan_to_deg(panSpeed)
        return self.panSpeed

    # get pan speed in degrees/s
    def get_pan_speed_deg(self):
        self.get_pan_speed()
        return self.panSpeedDeg

    # gets the tilt speed
    def get_tilt_speed(self):
        retString = self.PTU.get_tilt_speed()
        tiltSpeed = u.int_from_string(retString)
        if tiltSpeed is None:
            self.tiltSpeed = 1
            self.tiltSpeedDeg = 1
        else:
            self.tiltSpeed = tiltSpeed
            self.tiltSpeedDeg = self.tilt_to_deg(tiltSpeed)
        return self.tiltSpeed

    # get pan speed in degrees/s
    def get_tilt_speed_deg(self):
        self.get_tilt_speed()
        return self.tiltSpeedDeg

    ''' Other '''
    # Change operating mode (NOT IMPLEMENTED)
    def change_mode(self, panMode, tiltMode):
        s = ""
        if panMode is not None:
            newPanMode = u.toChar(panMode[0])
            if(newPanMode != self.panMode):
                self.panMode = newPanMode
                s += "Updating pan to " + str(newPanMode) + "."
                # Serial for changing tilt mode


        if tiltMode is not None:
            newTiltMode = u.toChar(tiltMode[0])
            if(newTiltMode != self.tiltMode):
                self.tiltMode = newTiltMode
                s += "\tUpdating tilt to " + str(newTiltMode) + "."
                # Serial for changing pan mode
        return s

    ''' Conversions '''
    def pan_to_deg(self, pan):
        return float(pan) * self.PTU.panRes / 3600

    def tilt_to_deg(self, tilt):
        return float(tilt) * self.PTU.tiltRes / -3600 + self.transform.__payloadTiltOffset__

    def deg_to_pan(self, panDeg):
        return int(3600 * float(panDeg) / self.PTU.panRes)

    def deg_to_tilt(self, tiltDeg):
        return int(-3600 * (float(tiltDeg) - self.transform.__payloadTiltOffset__) / self.PTU.tiltRes)

