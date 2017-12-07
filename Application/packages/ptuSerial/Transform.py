import math
from .. other import Utilities as u


class Tranform():
    '''
        This is an object that controls transformations from wide angle lens coordinates
        to PTU coordinates in degrees

        Variables can be loaded from a config file (yet to be implemented but can be changed here)

        This allows for both static (single point) and dynamic (trajectory and motion)
        approximations for input points
    '''

    __markerFromPtu__ = 180.0           # marker position relative to pan unit 0
    __payloadTiltOffset__ = 45.0        # payload offset relative to tilt 0
    __payloadPanOffset__ = 90.0         # payload offset relative to pan 0
    __tiltC__ = 90.0                    # Tilt equation c coefficient
    __maxLensRadius__ = 195             # maximum radius of the lens

    __del_x__ = -0.29                   # x distance from camera to PTU
    __del_y__ = 0.09                    # y distance from camera to PTU
    __del_z__ = 0.11                    # z distance from camera to PTU
    __del_arm__ = 0.12                  # distance from center of camera to pivot
    __rho__ = 1.5                       # distance of expected object from camera

    __speed_delta_factor__ = 4.0        # Speed delta. Used in increase PTU speed when far away
    __max_pan_speed__ = 150.0
    __min_pan_speed__ = 5.0
    __max_tilt_speed__ = 60.0
    __min_tilt_speed__ = 1.0

    markerFromNormal = -136.63          # Angle of marker from image normal (x-axis) in degrres
    prevPt = None                       # Previous pt that was analysed dynamically
    curPt = None                        # Current pt being analysed dynamically
    staticPt = None                     # Current pt being analysed statically

    def __init__(self):
        # Calculate straight distance between wide angle and PTU
        self.__del_rho__ = math.hypot(self.__del_x__, self.__del_y__)
        # Calculate angle between PTU and payload
        self.__delta__ = math.degrees(math.atan2(self.__del_y__, self.__del_x__))
        self.prevInstPos = None

    def load_settings(self):
        ''' Call to read in user settings from transform.txt '''
        pass

    def calculate_pan_tilt(self, alpha, radius):
        ''' Calculates pan and tilt angles for PTU based on raw image position and radius from center'''
        # Get target point as A(rho, theta, phi)
        rho = self.__rho__
        theta = self.camera_alpha_to_theta(alpha)
        phi = self.camera_radius_to_phi(radius)
        CO = (rho, theta, phi)

        # Calculate Cartesian of CO -> (x, y, z)
        COx, COy, COz = self.sphere_to_cart(rho, theta, phi)

        # Find cartesian coordinate of PO (PTU to object)
        POx = COx - self.__del_x__
        POy = COy - self.__del_y__
        POz = COz - self.__del_z__

        # Convert cartesian PO to spherical
        POrho, POtheta, POphi = self.cart_to_sphere(POx, POy, POz)


        pan = POtheta + self.__markerFromPtu__ - self.__payloadPanOffset__
        pan = u.within_pi(pan)

        # tilt part -- takes into account ptu is from x up not z down
        tilt = u.within_pi(90.0 - POphi)
        return pan, tilt

    ''' Coordinate correlations '''
    def camera_alpha_to_theta(self, alpha):
        ''' Takes in an alpha and outputs theta from the camera +-180'''
        theta = alpha - self.markerFromNormal
        return u.within_pi(theta)

    def camera_theta_to_alpha(self, theta):
        alpha = theta + self.markerFromNormal
        return u.within_pi(alpha)

    def camera_radius_to_phi(self, radius):
        ''' Takes in the radius from center of the wide angle and gives phi from z-axis as 0'''
        # This is a function based on testing and not spherical coordinates
        phi = 0.4647 * radius
        return u.within_pi(phi)

    def camera_phi_to_radius(self, phi):
        ''' This is not accurate and only an approximation'''
        radius = phi / 0.492
        return radius

    ''' Coordinate transforms '''
    def cart_to_sphere(self, x, y, z):
        ''' Takes in cartesian coordinates and outputs spherical in degrees'''
        rho = math.sqrt(x*x + y*y + z*z)
        theta = math.degrees(math.atan2(y, x))
        phi = math.degrees(math.acos(z / rho))
        return rho, theta, phi

    def sphere_to_cart(self, rho, theta, phi):
        ''' Takes in spherical in degrees and outputs cartesian'''
        theta = math.radians(theta)
        phi = math.radians(phi)
        x = rho * math.cos(theta) * math.sin(phi)
        y = rho * math.sin(theta) * math.sin(phi)
        z = rho * math.cos(phi)
        return x, y, z

    def polar_to_cart_img(self, radius, theta, center):
        x = radius * math.cos(math.radians(theta)) + center[0]
        y = -1.0 * radius * math.sin(math.radians(theta)) + center[1]
        return int(x), int(y)


    ''' Static Equations '''
    def angle_to_pan_deg(self, alpha):
        ''' Converts normal wide angle angle to pan coord in degrees +-180'''

        # delta is the angle from the marker
        delta = self.alpha_to_delta(alpha)
        x = self.__rho__ * math.cos(math.radians(delta)) - self.__del_x__
        y = self.__rho__ * math.sin(math.radians(delta)) - self.__del_y__

        # normal PTU is the angle from the marker at the PTU
        rho = math.degrees(math.atan2(y, x))

        # pan is the coordinates needed by the PTU
        pan = rho + self.__markerFromPtu__ - self.__payloadPanOffset__
        pan = u.within_pi(pan)
        return pan

    def alpha_to_delta(self, alpha):
        ''' Converts a raw alpha angle to an angle from the marker +-180'''
        delta = alpha - self.markerFromNormal
        delta = u.within_pi(delta)
        return delta

    def pan_deg_to_angle(self, pan):
        ''' Converts pan coord to wide angle coordinates in deg +-180'''
        rho = pan - self.__markerFromPtu__ + self.__payloadPanOffset__
        num = self.__del_rho__ * math.sin(math.radians(rho + 180.0 - self.__delta__))
        den = self.__rho__
        delta = rho + math.degrees(math.asin(float(num)/float(den)))
        alpha = u.within_pi(delta + self.markerFromNormal)
        return alpha

    def radius_to_tilt_deg(self, radius):
        ''' Converts radius to tilt coord in degrees '''
        tilt = -0.464 * float(radius) + 90.351
        return float(tilt)

    def tilt_deg_to_radius(self, tilt):
        ''' Converts tilt coord to wide angle radius '''
        radius = -2.151 * float(tilt) + 194.43
        return float(radius)

    ''' Dynamic equations '''
    def predict_pos_from_point(self, angle, radius, curPan, curTilt):
        '''
        :param radius: (float) radius from center of wide angle
        :param angle: (float) angle from positive x-axis in degrees
        :param curPan: (float) angle of pan
        :return: pan (float), tilt (float), pSpeed (float), tSpeed (float) in degrees
        '''
        '''
            Predict the next point for approximately linear motion
            returns: (pan_pos, tilt_pos, pan_speed, tilt_speed) in degrees
        '''
        targetPos = None
        # Get the instantaneous position of the target pt
        instPos = self.calculate_pan_tilt(angle, radius)

        # Calculate the predicted position
        if self.prevInstPos is not None:
            targetPos = self.tuple_subtract(self.tuple_multi(instPos, 2.0), self.prevInstPos)
        else:
            targetPos = instPos

        pan = targetPos[0]
        tilt = targetPos[1]

        # Calculate the desired speed
        targetSpeed = self.tuple_multi(self.tuple_subtract(targetPos, (curPan, curTilt)), self.__speed_delta_factor__)
        panSpeed = math.fabs(targetSpeed[0])
        tiltSpeed = math.fabs(targetSpeed[1])

        # Ensure range for pan speed
        if panSpeed > self.__max_pan_speed__:
            panSpeed = self.__max_pan_speed__
        if panSpeed < self.__min_pan_speed__:
            panSpeed = self.__min_pan_speed__

        # Ensure range for tilt speed
        if tiltSpeed > self.__max_tilt_speed__:
            tiltSpeed = self.__max_tilt_speed__
        if tiltSpeed < self.__min_tilt_speed__:
            tiltSpeed = self.__min_tilt_speed__

        self.prevInstPos = instPos

        return pan, tilt, panSpeed, tiltSpeed


    ''' Other functions '''
    def tuple_subtract(self, t1, t2):
        return (t1[0] - t2[0], t1[1] - t2[1])

    def tuple_multi(self, t1, a):
        return (t1[0] * a, t1[1] * a)

    def tuple_divide(self, t1, a):
        if a is not 0:
            return (float(t1[0] * a), float(t1[1] * a))
        else:
            return None




