from . PTUController import PTUController
from typing import List

__low_speed__ = 1
__medium_speed__ = 5
__high_speed__ = 25
__very_high_speed__ = 100

class PTUKeyboad():

    def __init__(self, PTU, modeKey=225, left=81, right=83, up=82, down=84):
        ''' Pass in the desired control keyboard commands'''
        self.PTU = PTU # type: PTUController
        # self.PTU.PTU.write(" CV ")

        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.modeKey = modeKey

        self.prevHor = 0
        self.prevVer = 0

        self.speed = __high_speed__ # deg per second
        self.mode = 0

    def move(self, key):
        if key is not -1:
            print key

        if self.PTU is not None:
            # Horizontal control
            if key is self.left:
                if self.prevHor != self.speed:
                    self.PTU.PTU.write(" PO" + str(self.speed) + " ")
                    # self.PTU.set_pan_speed_deg(self.speed)
                    # self.prevHor = self.speed
            elif key is self.right:
                if self.prevHor != -1*self.speed:
                    self.PTU.PTU.write(" PO" + str(-1*self.speed) + " ")
                    # self.PTU.set_pan_speed_deg(-1*self.speed)
                    # self.prevHor = -1*self.speed
            else:
                if self.prevHor != 0:
                    # self.PTU.set_pan_speed_deg(0)
                    self.prevHor = 0

            # Vertical control
            if key is self.up:
                if self.prevVer != -1*self.speed:
                    self.PTU.PTU.write(" TO" + str(-2*self.speed) + " ")
                    # self.PTU.set_tilt_speed_deg(-1*self.speed)
                    # self.prevVer = -1*self.speed
            elif key is self.down:
                if self.prevVer != self.speed:
                    self.PTU.PTU.write(" TO" + str(2*self.speed) + " ")
                    # self.PTU.set_tilt_speed_deg(self.speed)
                    # self.prevVer = self.speed
            else:
                if self.prevVer != 0:
                    self.PTU.set_tilt_speed_deg(0)
                    self.prevVer = 0

            # Change modes
            if key is self.modeKey:
                print "mode change"
                self.mode += 1
                self.change_mode(self.mode)

            # Return current position
            return self.PTU.get_pos_and_inst_speed_deg()
        return None

    def change_mode(self, mode):
        if mode > 3:
            mode = 0
        elif mode < 0:
            mode = 3
        self.mode = mode

        if mode == 0:
            self.speed = __very_high_speed__
        elif mode == 1:
            self.speed = __high_speed__
        elif mode == 2:
            self.speed = __medium_speed__
        elif mode == 3:
            self.speed = __low_speed__


