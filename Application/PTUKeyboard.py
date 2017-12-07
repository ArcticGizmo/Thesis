import cv2
import time

from packages.ptuSerial.PTUController import PTUController
from packages.ptuSerial.PTUkeyboard import PTUKeyboad
from packages.opencvController.camera import Camera

# Key codes
__up__ = 82
__left__ = 81
__down__ = 84
__right__ = 83
__l_shift__ = 226
__enter__ = 10

# Colours
__red__ = (0, 0, 255)
__green__ = (0, 255, 0)
__blue__ = (255, 0, 0)
__black__ = (0, 0, 0)
__white__ = (255, 255, 255)

# Text
__FONT__ = cv2.FONT_HERSHEY_SIMPLEX

__frame_wait__ = 10



def add_crosshair(img):
    imgCol = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    dims = img.shape
    cv2.circle(imgCol, (dims[0] / 2, dims[1] / 2), 1, __red__, 1)
    return imgCol


if __name__ == "__main__":
    # Create camera
    cam = Camera(0, "Payload")
    cam.connect_camera()
    cam.startCapture()

    # Create PTU control
    ptu = PTUController("/dev/ttyS0", 9600)
    pan = 0
    tilt = 0

    # Create keyboard controller for PTU
    keyboard = PTUKeyboad(ptu, modeKey=__l_shift__, left=__left__, right=__right__, up=__up__, down=__down__)
    showData = True

    # Create CV window and attach intercept
    cv2.namedWindow("Payload", cv2.WINDOW_NORMAL)

    # Processing Loop -- z to exit
    while 1:
        # Grab image from camera
        img = cam.grab_numpy_image()

        if img is not None:
            # Draw cross hairs on it
            imgCol = add_crosshair(img)

            # Draw position info
            if showData is True:
                string = "PP: " + str(pan) + "     " + "TP:" + str(tilt)
                dims = img.shape
                cv2.putText(imgCol, "Shift -> mode change | arrows for direction", (10, dims[1] - 50), __FONT__, 0.5, __green__, 1)
                cv2.putText(imgCol, str(keyboard.mode), (10, dims[1] - 30), __FONT__, 0.5, __green__, 1)
                cv2.putText(imgCol, string, (10, dims[1] - 10), __FONT__, 0.5, __green__, 1)

            # Display image
            cv2.imshow("Payload", imgCol)


        # Two wait statements to avoid increasing speed when button held down
        key = cv2.waitKey(1)
        cv2.waitKey(__frame_wait__)
        if key == ord('z'):
            break
        else:
            pan, tilt, pSpeed, tSpeed = keyboard.move(key)

            if key == __enter__:
                showData = not showData

    ptu.PTU.write(" CI ")  # set in positional control

    # Release
    cam.disconnect_camera()
    ptu.close()



