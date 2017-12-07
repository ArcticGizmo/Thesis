import csv
from datetime import datetime
from Thesis.Application.packages.ptuSerial.PTUController import PTUController
from Thesis.Application.packages.other import Utilities as u
import math
from Thesis.Application.packages.opencvController.camera import Camera
import cv2
import os

def az_to_pan(az):
    az = u.within_pi(az)
    pan = -0.9923*az - 0.3099
    return u.within_pi(pan)

def alt_to_tilt(alt):
    alt = u.within_pi(alt)
    tilt = 0.9937 * alt + 2.0829
    return u.within_pi(tilt)

def generate_list(filename):
    inList = []
    firstRowCOmplete = False
    with open(filename) as fin:
        reader = csv.reader(fin, delimiter=',', quotechar='|')

        for row in reader:
            # ignore first row as this has headers
            if firstRowCOmplete is False:
                firstRowCOmplete = True
                continue
            inList.append(row)

    return inList



def generate_track_data(raw_data):
    track_data = []
    prevPan = 0
    prevTilt = 0
    prevTime = datetime.now()
    first = True

    for raw in raw_data:
        # Convert date and time to datetime
        dt = datetime.strptime(raw[0] + raw[1], "%Y-%m-%d%H:%M:%S")
        # Convert az to pan
        pan = az_to_pan(float(raw[2]))
        # Convert alt to tilt
        tilt = alt_to_tilt(float(raw[3]))
        # Velocities
        print dt
        timeDelta = (dt - prevTime).total_seconds()
        if timeDelta < 1:
            timeDelta = 1

        # Pan speed
        pSpeed = math.fabs(pan - prevPan) / timeDelta
        if pSpeed > __max_speed__:
            pSpeed = __max_speed__

        # Tilt speed
        tSpeed = math.fabs(tilt - prevTilt) / timeDelta
        if tSpeed > __max_speed__:
            tSpeed = __max_speed__
        prevPan = pan
        prevTilt = tilt
        prevTime = dt

        if first is True:
            # set to faster speed to ensure it is waiting at the correct pos
            first = False
            pSpeed = __max_speed__
            tSpeed = __max_speed__

        track_data.append([dt, pan, tilt, pSpeed, tSpeed])
    return track_data


def set_ptu_params(track_data_row, PTU):
    print "Waiting for " + str(track_data_row[0])
    print "\t" + str(track_data_row)
    pSpeed = track_data_row[3]
    if pSpeed < __min_speed__:
        pSpeed = __min_speed__
    tSpeed = track_data_row[4]
    if tSpeed < __min_speed__:
        tSpeed = __min_speed__

    PTU.set_pan_speed_deg(pSpeed)
    PTU.set_tilt_speed_deg(tSpeed)
    PTU.set_pan_deg(track_data_row[1])
    PTU.set_tilt_deg(track_data_row[2])

def track(track_data, PTU, camera=None, vidName = "vid", size=(600,600), frameRate=40.0):
    '''
        Iterates through the track_data and sets the PTU accordingly.
        Also creates a video if a camera is passed to it
    '''

    first = True

    if camera is not None:
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        out = cv2.VideoWriter()
        path = os.path.dirname(os.path.realpath(__file__)) + "/vids" + str(vidName) + ".avi"
        print path
        out.open(path, fourcc, frameRate, size)

    for t in track_data:
        # Update PTU parameters
        set_ptu_params(t, PTU)

        # wait for next timestamp to pass
        while datetime.now() < t[0]:
            if camera is not None and first is False:
                img = camera.grab_numpy_image()
                imgCol = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                if imgCol is not None:
                    out.write(imgCol)
        first = False
    if out is not None:
        out.release()


__input__ = "trajectory.csv"
__max_speed__ = 15.0
__min_speed__ = 0.01
savedFramerate = 10.0
vidName = "AchernarBase2"

if __name__ == "__main__":
    '''
        Program to track any given target based on the formatted trajectory.csv
        * automatically generates the PTU specific controls
        * if the position is within the deadzone there may be control issues
        * trajectory.csv can be set by a user or through using the starFormatter.py program to get
            data straight from stellarium
    '''
    # Connect PTU
    PTU = PTUController("/dev/ttyS0", 9600)
    PTU.PTU.change_pan_mode("E")
    PTU.PTU.change_tilt_mode("E")

    # connect payload camera
    payload = Camera(0, "payload")
    payload.connect_camera()
    payload.startCapture()

    # Generate raw data from csv
    raw_data = generate_list(__input__)

    # Convert to useable PTU data
    track_data = generate_track_data(raw_data)
    print "Tracking ...."

    # Activate tracking protocol
    #track(track_data, PTU, frameRate=float(savedFramerate), vidName=vidName, camera=payload)
    PTU.stop()

    print ".... Tracking complete"

    # Release
    PTU.close()
    payload.disconnect_camera()





















































