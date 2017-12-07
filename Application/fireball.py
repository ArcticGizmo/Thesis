import time
import cv2
import os

from packages.opencvController.camera import Camera
from packages.ptuSerial.PTUController import PTUController
from packages.opencvController.cvWindowObjects import MotionTracking, DisplayFeed

__cur_path__ = os.path.dirname(os.path.realpath(__file__))
__export__ = __cur_path__ + "/fireballVids/"                # location of saved videos
__extension__ = ".avi"                                      # video format type
__fps__ = 1000                                              # do not change
__frame_wait__ = int(1000.0 / __fps__)                      # ms / fps
__save_tracking__ = True                                    # should the payload data be saved to disk
__accepted_delay__ = 5.0                                    # additional record length after event ends

def write_vid(imgList, start, end, useColor=False):
    '''
        Saves captured video pairs to /tracking
        * name : Ymd-HMS.avi
        * automatically calculates the frame rate
    '''
    if imgList is not None and len(imgList) > 0:
        # Generate fourcc codec
        fourcc = cv2.VideoWriter_fourcc(*'X264')

        # Create an output video writer
        out = cv2.VideoWriter()  # type: cv2.VideoWriter()

        # Determine the sequential file name starting from 1
        num = 1
        while 1:
            #path = __export__ + "fb" + str(num).zfill(6) + __extension__
            path = __export__ + str(time.strftime("%Y%m%d-%H%M%S", time.localtime(start)))+ __extension__

            if os.path.exists(path) is False:
                break
            num += 1

        # Determine the frame rate
        frameRate = float(len(imgList)) / float((end - start))
        print frameRate

        # Get image size from the first frame
        width, height = imgList[0].shape[:2]

        # Create writing object and write frames
        out.open(path, fourcc, frameRate, (int(width), int(height)), useColor)
        for img in imgList:
            out.write(img)
        print "Saved to ", path
        out.release()


if __name__ == "__main__":
    '''
        Core application for the tracking of fireballs
            * Requires : connected BFLY cameras and serial PTU
        Functions:
            * tracks moving light sources
            * records events with a buffer after motion has stopped
            * saves to /fireballVid with a filename reflecting datetime
    '''
    # Create PTU control object
    PTU = PTUController("/dev/ttyS0", 9600)
    PTU.PTU.write(" FT ")   # enable terse mode
    PTU.PTU.change_tilt_mode("H")   # Set pan and tilt mode to half stepping
    PTU.PTU.change_pan_mode("H")

    # Set the initial speeds of the ptu
    PTU.set_pan_speed(500)
    PTU.set_tilt_speed(500)

    # Create camera devices
    cam = Camera(1, "Wide")
    payload = Camera(0, "Payload")

    # Connect cameras
    cam.connect_camera()
    payload.connect_camera()

    # Start capture
    cam.startCapture()
    payload.startCapture()

    # Create motion tracking object
    motionTracking = MotionTracking("Wide")
    motionTracking.assign([PTU])

    # Apply mask to motion tracking (see maskGenerator to create your own)
    mask = cv2.imread("mask.png", 0)    # 0 is grayscale
    motionTracking.set_mask(mask)

    # Create payload display object
    disp = DisplayFeed("Payload")

    # Enable CVEvents
    motionTracking.enable(True)
    disp.enable(True)

    # image storage
    payloadImgs = []

    startTime = None
    residual = None
    while 1:
        # Get images from capture devices
        wideRaw = cam.grab_numpy_image()
        payloadRaw = payload.grab_numpy_image()

        # Process images
        wideImg, isTracking = motionTracking.run(wideRaw)
        payloadImg = disp.run(payloadRaw)

        # Determine if a video should still be recorded
        if isTracking is True:
            if startTime is None:
                startTime = time.time()
            residual = time.time() + __accepted_delay__

        # Save video if required
        if residual is not None and residual > time.time():
            if len(payloadImgs) < 1:
                print "Recording start"
            payloadImgs.append(payloadImg)
        elif residual is not None and __save_tracking__ is True:
            # Motion has decade and residual time passed
            residual = None
            endTime = time.time()
            write_vid(payloadImgs, startTime, endTime)
            payloadImgs = []
            startTime = None

        # Wait for user to end. This could be replaced with optional time restraint like 5am or something
        key = cv2.waitKey(__frame_wait__)
        if key == ord('z'):
            break


    # safety speed set
    PTU.stop()
    PTU.set_pan_speed(500)
    PTU.set_tilt_speed(500)

    # Release objects
    PTU.close()
    cam.disconnect_camera()
    payload.disconnect_camera()
