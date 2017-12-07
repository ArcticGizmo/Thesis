import numpy as np
import PyCapture2
from typing import List


class Camera:

    def __init__(self, index, name):
        self.index = index
        self.name = name
        self.cam = None
        self.numCams = 0
        self.camInfo = []
        self.pyCaptureInfo = []

    # start return true if able to start, else false
    def startCapture(self):
        if self.cam is not None:
            self.cam.startCapture()
            return True
        else:
            return False

    # Stop the capture of given device
    def stopCapture(self):
        if self.cam is not None:
            self.cam.stopCapture()

            # Connect the camera to the first found

    # Connect to first available camera
    def connect_camera(self):

        # Get bycapture information
        #libVer = PyCapture2.getLibraryVersion()
        #self.pyCaptureInfo.append("PyCapture2 library version " + str(libVer[0]) + "." + str(libVer[1]) + "." + str(libVer[3]) )


        # Check if there are sufficient cameras
        bus = PyCapture2.BusManager()
        self.numCams = bus.getNumOfCameras()

        if self.index < self.numCams:
            # Connect camera
            self.cam = PyCapture2.Camera()
            uid = bus.getCameraFromIndex(self.index)  # This could be used to select multiple cameras
            self.cam.connect(uid)
            #self.enable_embedded_timestamp(True)

            if self.cam is not None:
                camInfo = self.cam.getCameraInfo()
                self.camInfo.append("Serial number      - " + str(camInfo.serialNumber))
                self.camInfo.append("Camera model       - " + str(camInfo.modelName))
                self.camInfo.append("Camera vendor      - " + str(camInfo.vendorName))
                self.camInfo.append("Sensor             - " + str(camInfo.sensorInfo))
                self.camInfo.append("Resolution         - " + str(camInfo.sensorResolution))
                self.camInfo.append("Firmware version   - " + str(camInfo.firmwareVersion))
                self.camInfo.append("Firmware build time- " + str(camInfo.firmwareBuildTime))
        else:
            self.camInfo.append("No Camera information to display")

    # Disconnect the camera. freeing it
    def disconnect_camera(self):
        if self.cam is not None:
            try:
                self.cam.disconnect()
            except:
                pass
            self.cam = None

    # Returns string of camera information
    def get_camera_info(self):
        return self.camInfo

    # Allow the use of timestamps
    def enable_embedded_timestamp(self, enable):
        embeddedInfo = self.cam.getEmbeddedImageInfo()
        if embeddedInfo.available.timestamp:
            self.cam.setEmbeddedImageInfo(timestamp=enable)

    # Returns an image as an opencv compatible numpy array
    def grab_numpy_image(self):
        if self.cam is not None:
            try:
                rawImage = self.cam.retrieveBuffer()
                cvImage = np.array(rawImage.getData(), dtype="uint8").reshape(
                    (rawImage.getRows(), rawImage.getCols()) )
                cvImage[0] = 0
                return cvImage
            except:
                return None
        else:
            return None




