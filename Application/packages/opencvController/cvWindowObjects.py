import cv2
import math
import cmath
import os
import copy
import time

from .. ptuSerial.PTUController import PTUController
from .. other import Utilities as u

__red__ = (0, 0, 255)
__green__ = (0, 255, 0)
__blue__ = (255, 0, 0)
__black__ = (0, 0, 0)
__white__ = (255, 255, 255)

def draw_line_from_angle(img, center, angle, length, color, width=2):
    x = int(center[0] + length * (math.cos(math.radians(angle))))
    y = int(center[1] + length * (math.sin(math.radians(angle))))
    cv2.line(img, center, (x, y), color, width)
    return (x, y)

def draw_arc(img, center, start, end, radius, color, width=2):
    cv2.ellipse(img, center, (radius, radius), 0, start, end, color, width)


class CVWindowEvent(object):
    '''
        This is the base class for any OpenCV operation that requires the need to be
        multi-threaded
        * assign is optional and only used if you need to pass objects to the event
        * enable allows the user to stop the process being run when used by a CVController
        * run is called any time the function should be run. Takes a single numpy image
    '''
    def __init__(self, winName="name"):
        self.enabled = False
        self.winName = winName

    def enable(self, bool):
        self.enabled = bool

    # A thread safe method to close functions
    def close(self):
        if self.enabled is False:
            cv2.destroyWindow(self.winName)

    def run(self, img):
        # type: (array) -> None
        pass

    def assign(self, args):
        # type: (array) -> None
        pass


class MotionTracking(CVWindowEvent):
    '''
        Implementation of the predictive position and adaptive velocity controller
        * utilises the transform class
        * variables before the __init__ may be changed if desired
    '''

    __wait__ = 0            # Number of seconds to wait before polling PTU
    __high__ = 255          # binary value of full intensity
    __low__ = 0             # binary value of no intensity
    __intensity__ = 20      # Minimum light intensity to track
    minArea = 2             # Minimum trackable area
    maxArea = 1500          # maximum trackable area
    threshold = 5           # minimum frame delta accepted as motion
    tillNextBg = 300        # Number of seconds until next background image is taken

    def __init__(self, ownerName):
        super(MotionTracking, self).__init__(ownerName + ": Motion Tracking")
        # Motion detection vars
        self.bg = None
        self.setNewBg = False
        self.mask = None
        self.prevPoll = 0


        # Motion tracking vars
        self.PTU = None # type: PTUController
        self.targetPos = None
        self.targetPt = None
        self.curPos = None
        self.curPt = None
        self.marker = (175, 415)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.curTime = 0
        self.newbgTime = None


    def run(self, img):
        isTracking = False
        if img is not None and self.PTU is not None and self.enabled is True:
            img = cv2.flip(img, 0)
            if self.bg is None or self.setNewBg is True:
                # Save a background image
                self.bg = img
                self.setNewBg = False
                self.newbgTime = time.time() + self.tillNextBg
            else:
                # Apply mask
                img = self._apply_mask(img)

                # Convert image to color (for display only)
                imgCol = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

                # Get motion delta
                frameDelta = self._get_motion_delta(img, self.bg)

                # Get contours of motion
                contours = self._get_contours(frameDelta)

                # Process contours to get target pixels point
                self.targetPt = self._get_target_pt(img, contours, self.targetPt)

                # Get image parameters
                dims = img.shape                        # width and height of image
                center = (dims[0] / 2, dims[1] / 2)     # center of the image

                imgCol = self._draw_ptu_limits(imgCol, center)

                # Get current PTU coordinates (Pan, tilt, pSpeed, tSpeed)
                pp = 0
                tp = 0
                if time.time() - self.prevPoll > self.__wait__:
                    self.prevPoll = time.time()
                    pp, tp, ps, ts = self.PTU.get_pos_and_inst_speed_deg()
                    self.curPos = (pp, tp)

                curAngle = self.PTU.transform.pan_deg_to_angle(pp)
                curRad = self.PTU.transform.tilt_deg_to_radius(tp)

                curX, curY = self.PTU.transform.polar_to_cart_img(curRad, curAngle, center)
                self.curPt = (int(curX), int(curY))

                # Draw PTU position point
                cv2.circle(imgCol, self.curPt, 1, __green__, thickness=2)

                # Move to target if one is present
                if self.targetPt is not None:

                    # calculate angle and radius within the wide angle (standard angle about center from x-pos)
                    angle = self.calculate_angle(self.targetPt, center)
                    radius = self.calculate_radius(self.targetPt, center)


                    # Get desired pan, tilt, pSpeed and tSpeed from prediction algorithm
                    pan, tilt, pSpeed, tSpeed = self.PTU.transform.predict_pos_from_point(angle, radius, pp, tp)
                    self.targetPos = (pan, tilt)

                    # Draw target point
                    cv2.circle(imgCol, self.targetPt, 1, __red__, thickness=3)

                    # Apply positions and speeds to PTU
                    self.PTU.set_pan_speed_deg(pSpeed)
                    self.PTU.set_tilt_speed_deg(tSpeed)
                    self.PTU.set_pan_deg(self.targetPos[0])
                    self.PTU.set_tilt_deg(self.targetPos[1])

                    # Draw points
                    #imgCol = self._draw_points(imgCol)

                    # Draw to image
                    string = "Angle: {}    Radius: {}".format(u.round_float(angle), u.round_float(radius))
                    string2 = "Pan: {}    Tilt: {}".format(pan, tilt)
                    string3 = "PS: {}   TS: {}".format(u.round_float(pSpeed), u.round_float(tSpeed))
                    string4 = "Prev: Pan {}  Tilt {} ".format(u.round_float(pp), u.round_float(tp))

                    cv2.putText(imgCol, "Point Data:", (10, dims[1] - 90), self.font, 0.5, __green__)
                    cv2.putText(imgCol, string, (10, dims[1] - 70), self.font, 0.5, __green__, 1)
                    cv2.putText(imgCol, string4, (10, dims[1] - 50), self.font, 0.5, __green__, 1)
                    cv2.putText(imgCol, string2, (10, dims[1] - 30), self.font, 0.5, __green__, 1)
                    cv2.putText(imgCol, string3, (10, dims[1] - 10), self.font, 0.5, __green__, 1)
                else:
                    self.targetPos = None


                # Display image
                cv2.imshow(self.winName, imgCol)

                # Update background to previous frame
                #self.bg = img

                # Determine if the system is currently tracking

                if self.targetPos is not None:
                    isTracking = True

                if isTracking is False and self.newbgTime < time.time():
                    self.setNewBg = True

                return imgCol, isTracking

        return None, isTracking


    def set_thresh_bound(self, val):
        if u.between(self.lowValue, val, self.highValue):
            self.threshold = int(val)

    def assign(self, args):
        if args is not None:
            self.PTU = args[0]

    def set_mask(self, mask):
        self.mask = cv2.bitwise_not(mask)

    def _apply_mask(self, img):
        if self.mask is not None:
           return cv2.subtract(img, self.mask)
        return img

    # Return the frame delta
    def _get_motion_delta(self, cur, prev):
        # Apply Gaussian blur
        #cv2.GaussianBlur(cur, (21, 21), 0)

        # Get frame delta for positive gradient (dark to light events)
        frameDelta = cv2.subtract(cur, prev)

        # Create a binary threshold image
        ret, thresh = cv2.threshold(frameDelta, self.threshold, self.__high__, self.__low__)

        return thresh

    # get motion contours for a thresholded image
    def _get_contours(self, thresh):
        # Get contours of the image
        temp, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        return contours

    # Determine the point of motion with highest intensity
    def _get_target_pt(self, img, contours, prevTarget):
        target = None
        if contours is not None:
            for c in contours:
                largestArea = 0
                # Check the area is greater than acceptable
                area = cv2.contourArea(c)
                if self.minArea < area < self.maxArea:
                    M = cv2.moments(c)
                    if M["m00"] is not 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])

                        # Get the largest area found
                        # Will add closest instead later to prevent movement
                        if area > largestArea:
                            if img[cY, cX] > self.__intensity__:
                                self.largestArea = area
                                target = (cX, cY)
            if target is None:
                #target = prevTarget
                target = None
        else:
            target = None
        return target

    # Draw PTU limits on image (this is only to convey information to the user
    def _draw_ptu_limits(self, imgCol, center):
        maxRadius = self.PTU.transform.camera_phi_to_radius(90.0 - self.PTU.tiltRangeDeg[0])
        angleRange = self.PTU.panRangeDeg[:]
        minAngle = angleRange[
                       0] - self.PTU.transform.markerFromNormal + self.PTU.transform.__payloadPanOffset__
        maxAngle = angleRange[
                       1] - self.PTU.transform.markerFromNormal + self.PTU.transform.__payloadPanOffset__

        draw_line_from_angle(imgCol, center, minAngle, maxRadius, __red__, width=1)
        draw_line_from_angle(imgCol, center, maxAngle, maxRadius, __red__, width=1)
        draw_arc(imgCol, center, minAngle, maxAngle, int(maxRadius), __red__)

        # Draw marker line as coordinate origin (the transforms are taken from this)
        (x, y) = draw_line_from_angle(imgCol, center, -1.0 * self.PTU.transform.markerFromNormal,
                                      maxRadius, __green__, width=1)
        cv2.circle(imgCol, (x, y), 3, __red__, 2)

        return imgCol

    # Calculate radius from two points
    def calculate_radius(self, pt, center):
        '''
        :param pt:  (x, y) target point in pixels
        :param center: (x, y) center in pixels
        :return: (float) radius from center to point
        '''
        diff = (pt[0] - center[0], pt[1] - center[1])
        return math.hypot(diff[1], diff[0])

    # calculate the angle about center to point
    def calculate_angle(self, pt, center):
        '''
        :param pt:  (x, y) target point in pixels
        :param center: (x, y) center in pixels
        :return: (float) angle about center to point from x-axis as positive in deg
        '''
        diff = (pt[0] - center[0], pt[1] - center[1])
        # The negative is needed due to how pixels have y down as positive
        return -1.0 * math.degrees(math.atan2(diff[1], diff[0]))



    def _write_on_image(self, imgCol, angle,):
        ''' Writes information about the current variables onto the screen '''
        # Display information on image


class DisplayFeed(CVWindowEvent):
    ''' Displays an image '''
    def __init__(self, ownerName):
        super(DisplayFeed, self).__init__(ownerName + ": Live feed")
        cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)

    def run(self, img):
        if img is not None and self.enabled is True:
            mg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            cv2.imshow(self.winName, img)
            return img


class DisplayFeedInverted(CVWindowEvent):
    ''' Displays a reflected version of the passed image '''
    def __init__(self, ownerName):
        super(DisplayFeedInverted, self).__init__(ownerName + ": Inverted Live Feed")
        cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)

    def run(self, img):
        if img is not None and self.enabled is True:
            img = cv2.flip(img, 0)
            cv2.imshow(self.winName, img)


class DisplayCrosshair(CVWindowEvent):
    ''' displays an image with a crosshair at the center of the image '''
    def __init__(self, ownerName):
        super(DisplayCrosshair, self).__init__(ownerName + ": Live feed -+-")
        cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)

    def run(self, img):
        if img is not None and self.enabled is True:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            dims = img.shape
            cv2.circle(img, (dims[0] / 2, dims[1] / 2), 1, __blue__, 1)
            cv2.imshow(self.winName, img)
            return img


# Determine the length and angle for a point on the screen to center
class Angles(CVWindowEvent):
    def __init__(self, ownerName):
        super(Angles, self).__init__(ownerName + ": Set Points")
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.offset = 0
        self.base = (0, 0)
        self.pt = None

    def run(self, img):

        if img is not None and self.enabled is True:

            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)
            cv2.setMouseCallback(self.winName, self._click_set_point)

            # Get image parameters
            dims = img.shape
            center = (dims[0] / 2, dims[1] / 2)

            # Get base reference angle
            self.offset = math.degrees(math.atan2(self.base[1] - center[1], self.base[0] - center[0]))

            # Draw base line
            x = int(center[0] * (1 + math.cos(math.radians(self.offset))))
            y = int(center[1] * (1 + math.sin(math.radians(self.offset))))
            cv2.line(img, center, (x, y), __red__, 2)
            cv2.circle(img, (x, y), 3, __red__, 2)

            # Complete specific point calculations
            if self.pt is not None:
                # Determine radius
                diff = (self.pt[0] - center[0], self.pt[1] - center[1])
                rad = math.hypot(diff[1], diff[0])
                rad = u.round_float(rad)

                # Determine the angle from the center including offset
                angle = math.degrees(math.atan2(diff[1], diff[0])) - self.offset
                if angle > 180:
                    angle -= 360
                elif angle < -180:
                    angle += 360
                angle = u.round_float(angle)

                # Draw custom point
                cv2.circle(img, center, 2, __blue__, 3)
                cv2.circle(img, self.pt, 2, __blue__, 3)
                cv2.line(img, self.pt, center, __blue__, 2)

                # Display information
                string = "Angle: {}    Radius: {}".format(angle, rad)
                cv2.putText(img, string, (10, dims[1] - 10), self.font, 0.5, __green__, 1)

            cv2.imshow(self.winName, img)

    # adds a point to the list each left click. Removes each right click
    def _click_set_point(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pt = (x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.base = (x, y)


# A graphical display of where the PTU is currently positioned for PAN and TILT
class PTUDisplay(CVWindowEvent):

    panLength = 200
    panCamLength = 100
    tiltCamLength = 200
    maxRadius = 275
    baseWidth = 50

    def __init__(self, ownerName):
        super(PTUDisplay, self).__init__("PTU Display")
        cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)
        path = os.path.dirname(os.path.realpath(__file__)) + "/ptuGraphic.png"
        self.img = cv2.imread(path, cv2.IMREAD_COLOR)
        self.tiltCenter = (900, 300)
        self.panCenter = (300, 300)
        self.PTUQueue = [] # A thread safe list for PTU actions takes (func, [args])
        self.PTU = None # type: PTUController

    def run(self, img):
        if self.img is not None and self.PTU is not None and self.enabled is True:
            img = copy.copy(self.img)

            # Draw on the pan area
            self.draw_pan_area(img)

            # draw on the tilt area
            self.draw_tilt_area(img)


            # Display image
            cv2.imshow(self.winName, img)

    def draw_pan_area(self, img):
        # Get pan angle
        angle = -1.0 * self.PTU.panPosDeg

        # Draw Limits
        angleRange = self.PTU.panRangeDeg[:]
        minAngle = self.PTU.transform.__markerFromPtu__ + angleRange[0]
        minAngle = u.within_pi(minAngle)
        maxAngle = self.PTU.transform.__markerFromPtu__ + angleRange[1]
        maxAngle = u.within_pi(maxAngle)


        draw_line_from_angle(img, self.panCenter, minAngle, self.maxRadius, __black__)
        draw_line_from_angle(img, self.panCenter, maxAngle, self.maxRadius, __black__)
        draw_arc(img, self.panCenter, minAngle, maxAngle, self.maxRadius, __black__)

        # Draw base
        x, y = draw_line_from_angle(img, self.panCenter, angle + self.PTU.transform.__markerFromPtu__, self.panLength, __black__, width=7)

        # Draw Camera
        draw_line_from_angle(img, (x, y), angle + self.PTU.transform.__markerFromPtu__ - self.PTU.transform.__payloadPanOffset__, self.panCamLength,  __red__, width=7)

    def draw_tilt_area(self, img):
        # Get camera incline angle
        angle = -self.PTU.tiltPosDeg

        # Draw limits
        angleRange = self.PTU.tiltRangeDeg[:]
        minAngle = -angleRange[0]
        maxAngle = -angleRange[1]

        draw_line_from_angle(img, self.tiltCenter, minAngle, self.maxRadius, __black__)
        draw_line_from_angle(img, self.tiltCenter, maxAngle, self.maxRadius, __black__)
        draw_arc(img, self.tiltCenter, minAngle, maxAngle, self.maxRadius, __black__)

        # Draw base
        draw_line_from_angle(img, self.tiltCenter, angle + self.PTU.transform.__payloadTiltOffset__, self.baseWidth, __black__, width=7)
        draw_line_from_angle(img, self.tiltCenter, angle + self.PTU.transform.__payloadTiltOffset__ + 180, self.baseWidth, __black__, width=7)

        # Draw camera
        draw_line_from_angle(img, self.tiltCenter, angle, self.tiltCamLength, __red__, width=7)

    def assign(self, args):
        if args is not None:
            self.PTU = args[0]


# Basic thresholding of an image
class ThresholdingBasic(CVWindowEvent):

    highValue = 255
    lowValue = 0

    def __init__(self, ownerName):
        super(ThresholdingBasic, self).__init__(ownerName + ": Thresholding")
        cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)
        self.threshold = 127
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def run(self, img):
        if img is not None:
            # Get properties of the image
            dims = img.shape

            # Threshold the image
            ret, imgThresh = cv2.threshold(img, self.threshold, self.highValue, self.lowValue)
            imgCol = cv2.cvtColor(imgThresh, cv2.COLOR_GRAY2RGB)

            # Write threshold value at the bottom
            string = "Threshold @ " + str(self.threshold)
            cv2.putText(imgCol, string, (10, dims[1] - 10), self.font, 0.5, __green__)

            cv2.imshow(self.winName, imgCol)


    def set_threshold(self, thresh):
        if u.between(self.lowValue, thresh, self.highValue):
            self.threshold = int(thresh)


# Basic motion tracking
class DisplayMotionBasic(CVWindowEvent):

    highValue = 255
    lowValue = 0

    def __init__(self, ownerName):
        super(DisplayMotionBasic, self).__init__(ownerName + ": Basic Motion")
        self.mask = None
        self.bg = None
        self.setNewBg = False
        self.threshold = 15
        self.minArea = 2
        self.clearPts = False
        self.largestArea = None
        self.pt = None

    def run(self, img):
        if img is not None and self.enabled is True:
            if self.bg is None or self.setNewBg:
                # Save a background image
                self.bg = img
                self.setNewBg = False
            else:
                # Apply mask
                if self.mask is not None:
                    img = cv2.subtract(img, self.mask)

                # Convert image to color (for display only)
                imgCol = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

                # Apply Gaussian blur (this is probably too slow)
                cv2.GaussianBlur(img, (21, 21), 0)

                # Get frame delta
                frameDelta = cv2.subtract(img, self.bg)

                # Create a binary image (this may not be needed
                ret, thresh = cv2.threshold(frameDelta, self.threshold, 255, 0)

                # Get contours of the image
                temp, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                # Process contours
                if contours is not None:
                    for c in contours:
                        self.largestArea = 0
                        # Check that they are not too small
                        area = cv2.contourArea(c)
                        if area > self.minArea:
                            M = cv2.moments(c)
                            if M["m00"] is not 0:
                                cX = int(M["m10"] / M["m00"])
                                cY = int(M["m01"] / M["m00"])

                                cv2.drawContours(imgCol, [c], -1, __red__, 2)

                                if area > self.largestArea:
                                    self.largestArea = area
                                    self.pt = (cX, cY)
                else:
                    self.pt = None

                # draw point
                if self.pt is not None:
                    cv2.circle(imgCol, self.pt, 2, (255, 0, 0), thickness=2)

                # Display image
                cv2.imshow(self.winName, imgCol)

                # Update background to previous frame
                self.bg = img

                return imgCol
        return img

    def set_thresh_bound(self, val):
        if u.between(self.lowValue, val, self.highValue):
            self.threshold = int(val)

    def set_mask(self, mask):
        self.mask = mask

# A more complex motion tracking program (illustrates points)
class PlotMotion(CVWindowEvent):
    def __init__(self, ownerName):
        super(PlotMotion, self).__init__(ownerName + ":Motion")
        self.pts = []
        self.bg = None
        self.setNewBg = False
        self.threshBound = 40
        self.minArea = 10
        self.clearPts = False

    def close(self):
        if self.enabled is False:
            cv2.destroyWindow(self.winName)
            self.pts = []

    def run(self, img):
        if img is not None:
            if self.bg is None or self.setNewBg:
                # Save a background image
                self.bg = img
                self.setNewBg = False
            else:
                # Convert image to color (for display only)
                imgCol = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

                # Apply Gaussian blur
                cv2.GaussianBlur(img, (21, 21), 0)

                # Get frame delta
                frameDelta = cv2.absdiff(self.bg, img)
                # frameDelta = cv2.max(self.bg, img)

                # Create a binary image (this may not be needed
                ret, thresh = cv2.threshold(frameDelta, self.threshBound, 255, 0)

                # Dilate to remove some noise. This may not be needed
                # thresh = cv2.dilate(thresh, None, iterations=2)

                # Get contours of the image
                temp, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                # Process contours
                if contours is not None:
                    for c in contours:
                        # Check that they are not too small
                        # (This will need to change)
                        if cv2.contourArea(c) > self.minArea:
                            M = cv2.moments(c)
                            if M["m00"] is not 0:
                                cX = int(M["m10"] / M["m00"])
                                cY = int(M["m01"] / M["m00"])
                                self.pts.append((cX, cY))

                                # Draw contour
                                cv2.drawContours(imgCol, [c], -1, __red__, 2)

                # Draw points and lines
                if self.pts is not None:
                    for i in range(len(self.pts)):
                        if i != 0:
                            cv2.line(imgCol, self.pts[i - 1], self.pts[i], __red__, 2)
                        cv2.circle(imgCol, self.pts[i], 2, __blue__, 3)

                # Display image
                cv2.imshow(self.winName, imgCol)

                # Set previous frame
                # self.bg = img

                if self.clearPts is True:
                    self.clearPts = False
                    self.pts = []

    def set_thresh_bound(self, val):
        if 0 <= val <= 255:
            self.threshBound = val

    def clear_pts(self):
        self.clearPts = True


'''
    allows the clibration of the wide angle lens
    This object accesses a calibration object that is used by multiple instances
    * has coordinate transforms
    * as well as speed transforms for dynamic inputs
    Using the transformation objects, the PTU can be controlled
    WARN: Do not use static and dynamic tracking at the same time as this will cause conflicts of input
'''
class MotionCalibration(CVWindowEvent):


    def __init__(self, ownerName):
        super(MotionCalibration, self).__init__(ownerName + ": Set points")
        self.PTU = None # type: PTUController
        self.targetPos = None

        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.base = (175, 415)  # Marker position (the actual numbers do not matter as they are set with right click)
        self.pt = None

    def run(self, img):

        if img is not None and self.PTU is not None and self.enabled is True:
            img = cv2.flip(img, 0)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

            cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)
            cv2.setMouseCallback(self.winName, self._click_set_point)

            # Get image parameters
            dims = img.shape # width and height
            center = (dims[0] / 2, dims[1] / 2)

            # Get base reference angle from the normal (right x axis as 0 deg)
            self.PTU.transform.markerFromNormal = -1.0 * math.degrees(math.atan2(self.base[1] - center[1],
                                                                               self.base[0] - center[0]))

            # Draw limits
            maxRadius = self.PTU.transform.camera_phi_to_radius(90.0 - self.PTU.tiltRangeDeg[0])
            angleRange = self.PTU.panRangeDeg[:]
            minAngle = angleRange[0] - self.PTU.transform.markerFromNormal + self.PTU.transform.__payloadPanOffset__
            maxAngle = angleRange[1] - self.PTU.transform.markerFromNormal + self.PTU.transform.__payloadPanOffset__

            draw_line_from_angle(img, center, minAngle, maxRadius, __blue__, width=1)
            draw_line_from_angle(img, center, maxAngle, maxRadius, __red__, width=1)
            draw_arc(img, center, minAngle, maxAngle, int(maxRadius), __red__)

            # Draw base line
            (x, y) = draw_line_from_angle(img, center, -1.0 * self.PTU.transform.markerFromNormal,
                                          maxRadius, __green__, width=1)
            cv2.circle(img, (x, y), 3, __red__, 2)

            # Complete specific point calculations
            if self.pt is not None:
                # Determine radius
                diff = (self.pt[0] - center[0], self.pt[1] - center[1])
                radius = math.hypot(diff[1], diff[0])
                radius = u.round_float(radius)

                # Determine the angle of selected point in normal coordinate (right x axis zero)
                angle = -1.0 * math.degrees(math.atan2(diff[1], diff[0]))
                angle = u.within_pi(angle)


                # Draw selected point
                cv2.circle(img, center, 1, __blue__, 1)
                cv2.circle(img, self.pt, 1, __blue__, 1)
                cv2.line(img, self.pt, center, __blue__, 1)

                # Perform calculation
                pan, tilt = self.PTU.transform.calculate_pan_tilt(angle, radius)
                self.targetPos = (pan, tilt)
                self.PTU.set_pan_deg(pan)
                self.PTU.set_tilt_deg(tilt)

                # Display information
                string = "Angle: {}    Radius: {}".format(angle, radius)
                string2 = "Pan: {}    Tilt: {}".format(pan, tilt)

                cv2.putText(img, "Point Data:", (10, dims[1] - 50), self.font, 0.5, __green__)
                cv2.putText(img, string, (10, dims[1] - 30), self.font, 0.5, __green__, 1)
                cv2.putText(img, string2, (10, dims[1] - 10), self.font, 0.5, __green__, 1)

            cv2.imshow(self.winName, img)

    # move to selected point
    def _click_set_point(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pt = (x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.base = (x, y)

    def assign(self, args):
        if args is not None:
            self.PTU = args[0]


'''
    This is the basis for line tracking between two points
    This is not straight line tracking unless the update rate is very fast
'''
class SpeedControlledMotion(CVWindowEvent):

    __wait__ = 0

    def __init__(self, ownerName):
        super(SpeedControlledMotion, self).__init__(ownerName + ": Speed control")
        self.PTU = None # type: PTUController

        self.curPt = None       # current pos in pixels
        self.targetPt = None    # target pos in pixel

        self.curPos = None      # current position in deg
        self.targetPos = None   # target position in deg

        self.curTime = 0.0

        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.marker = (175, 415)  # Marker position (the actual numbers do not matter as they are set with right click)

    def run(self, img):

        if img is not None and self.PTU is not None and self.enabled is True:
            img = cv2.flip(img, 0)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

            cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)
            cv2.setMouseCallback(self.winName, self._click_set_point)

            # Get image parameters
            dims = img.shape    # width and height
            center = (dims[0] / 2, dims[1] / 2) # center of the image

            # Get base reference angle from the normal (right x axis as 0 deg)
            self.PTU.transform.markerFromNormal = -1.0 * math.degrees(math.atan2(self.marker[1] - center[1],
                                                                               self.marker[0] - center[0]))
            # Draw viewing limits
            maxRadius = self.PTU.transform.tilt_deg_to_radius(self.PTU.tiltRangeDeg[0])
            angleRange = self.PTU.panRangeDeg[:]
            minAngle = angleRange[0] - self.PTU.transform.markerFromNormal + self.PTU.transform.__payloadPanOffset__
            maxAngle = angleRange[1] - self.PTU.transform.markerFromNormal + self.PTU.transform.__payloadPanOffset__

            draw_line_from_angle(img, center, minAngle, maxRadius, __red__, width=1)
            draw_line_from_angle(img, center, maxAngle, maxRadius, __red__, width=1)
            draw_arc(img, center, minAngle, maxAngle, int(maxRadius), __red__)

            # Draw marker line as coordinate origin (the transforms are taken from this)
            (x, y) = draw_line_from_angle(img, center, -1.0 * self.PTU.transform.markerFromNormal,
                                          maxRadius, __green__, width=1)
            cv2.circle(img, (x, y), 3, __red__, 2)


            # Perform velocity calculations if there is a target point
            if self.targetPt is not None:

                # Determine radius (for tilt)
                diff = (self.targetPt[0] - center[0], self.targetPt[1] - center[1])
                radius = math.hypot(diff[1], diff[0])
                radius = u.round_float(radius)

                # Determine the angle of selected point in normal coordinate (right x axis zero)
                angle = -1.0 * math.degrees(math.atan2(diff[1], diff[0]))
                angle = u.within_pi(angle)

                # Perform calculation to get pan and tilt coords
                pan = self.PTU.transform.angle_to_pan_deg(angle)
                pan = u.within_pi(pan)
                tilt = self.PTU.transform.radius_to_tilt_deg(radius)
                tilt = u.round_float(tilt)

                # Store target and current positions
                self.targetPos = (pan, tilt)

                # Every "wait" seconds, get the PTU coordinates
                if time.time() - self.curTime > self.__wait__:
                    self.curTime = time.time()
                    self.curPos = (self.PTU.get_pan_deg(), self.PTU.get_tilt_deg())
                    # The negative 1 is used because y axis in normal math is up and in images is down
                    comp = cmath.rect(self.PTU.transform.tilt_deg_to_radius(self.curPos[1]),
                                      -1.0 * math.radians(self.PTU.transform.pan_deg_to_angle(self.curPos[0])))
                    self.curPt = (int(comp.real) + center[0], int(comp.imag) + center[1])

                # Determine velocity vector
                vel = [self.targetPos[0] - self.curPos[0], self.targetPos[1] - self.curPos[1]]
                # Update speed
                self.PTU.set_pan_speed_deg(vel[0])
                self.PTU.set_tilt_speed_deg(-1.0 * vel[1]) # this is negative as speed and position in tilt are opposite

                # Draw target point
                cv2.circle(img, center, 1, __blue__, 1)
                cv2.circle(img, self.targetPt, 1, __blue__, 1)
                cv2.line(img, self.targetPt, center, __blue__, 1)

                # Draw current point
                cv2.circle(img, self.curPt, 1, __green__, 1)


                # Display information on image
                string = "Angle: {}    Radius: {}".format(angle, radius)
                string2 = "Pan: {}    Tilt: {}".format(pan, tilt)

                cv2.putText(img, "Point Data:", (10, dims[1] - 50), self.font, 0.5, __green__)
                cv2.putText(img, string, (10, dims[1] - 30), self.font, 0.5, __green__, 1)
                cv2.putText(img, string2, (10, dims[1] - 10), self.font, 0.5, __green__, 1)

            cv2.imshow(self.winName, img)

    # mouse intercepts
    def _click_set_point(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # Set target position
            self.targetPt = (x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Set marker position
            self.base = (x, y)

    def assign(self, args):
        if args is not None:
            self.PTU = args[0]



'''
    Not get implemented
'''
class SequenceCapture(CVWindowEvent):

    def __init__(self, ownerName):
        super(SequenceCapture, self).__init__(ownerName + ": Sequence Capture")
        self.PTU = None # type: PTUController


    def run(self, img):

        if img is not None and self.PTU is not None and self.enabled is True:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)



            cv2.imshow(self.winName, img)


    def assign(self, args):
        if args is not None:
            self.PTU = args[0]



# -----  legacy ----

class SetPoints(CVWindowEvent):
    def __init__(self, ownerName):
        super(SetPoints, self).__init__(ownerName + ": Set Points")
        self.pts = []

    def close(self):
        if self.enabled is False:
            cv2.destroyWindow(self.winName)
            self.pts = []

    def run(self, img):
        if img is not None and self.enabled is True:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            lPts = self.pts
            cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)
            cv2.setMouseCallback(self.winName, self._click_add_points)
            if lPts is not None:
                for i in range(len(lPts)):
                    if i != 0:
                        cv2.line(img, lPts[i-1], lPts[i], __red__, 2)
                    cv2.circle(img, lPts[i], 2, __blue__, 3)
            cv2.imshow(self.winName, img)

    # adds a point to the list each left click. Removes each right click
    def _click_add_points(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pts.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN:
            if len(self.pts) is not 0:
                self.pts.pop()


class CenterLight(CVWindowEvent):
    def __init__(self, ownerName):
        super(CenterLight, self).__init__(ownerName + ": Find Light")
        self.pt = None
        self.threshBound = 30
        self.minArea = 6

    def close(self):
        if self.enabled is False:
            cv2.destroyWindow(self.winName)
            self.pt = None

    def run(self, img):
        if img is not None and self.enabled is True:
            self.contour(img)

    def contour(self, img):
        # Threshold image
        ret, thresh = cv2.threshold(img, self.threshBound, 255, 0)

        # Convert image to color
        imgCol = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        # Get contours of the image
        temp, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Process contours
        if contours is not None:
            prevArea = self.minArea
            found1 = False
            for c in contours:
                # check for largest area point
                cArea = cv2.contourArea(c)
                if cArea > prevArea:
                    prevArea = cArea
                    found1 = True
                    M = cv2.moments(c)
                    if M["m00"] is not 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        self.pt = (cX, cY)
            if found1 is False:
                self.pt = (0, 0)
        else:
            self.pt = (0, 0)

        if self.pt is not (0, 0):
            # Draw contour and point for largest area
            # cv2.drawContours(imgCol, [c], -1, __red__, 2)
            cv2.circle(imgCol, self.pt, 1, __blue__, 6)

        cv2.imshow(self.winName, imgCol)

    def max(self, img):
        temp, temp, temp, pos = cv2.minMaxLoc(img)
        imgCol = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        cv2.circle(imgCol, pos, 5, __red__, 4)
        cv2.imshow(self.winName, imgCol)

    def set_thresh_bound(self, val):
        if 0 <= val <= 255:

            self.threshBound = val



class TargetPosition(CVWindowEvent):
    def __init__(self, ownerName):
        super(TargetPosition, self).__init__(ownerName + ": Target Mode")
        self.pt = None

    def close(self):
        if self.enabled is False:
            cv2.destroyWindow(self.winName)
            self.clicked = False
            self.pt = None
            self.pan = 0
            self.tilt = 0

    def run(self, img):
        if img is not None and self.enabled is True:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            cv2.namedWindow(self.winName, cv2.WINDOW_NORMAL)
            cv2.setMouseCallback(self.winName, self._click_add_points)
            if self.pt is not None:
                cv2.circle(img, self.pt, 2, __blue__, 3)

            cv2.imshow(self.winName, img)

    # adds a point to the list each left click. Removes each right click
    def _click_add_points(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pt = (x, y)
            self.clicked = True
