import npyscreen as ns

from packages.guiComponents import winForms
from packages.opencvController import cvWindowController as cwc, cvWindowObjects as wo, camera
from packages.ptuSerial.PTUController import PTUController


class App( ns.NPSAppManaged ):
    ''' Terminal gui controller for all of the windows used within the gui '''
    def onStart(self):
        self.addForm("MAIN", winForms.MainMenu, name="Main Menu")

        self.addForm("PTU", winForms.PTUDegMenu, name="Manual PTU Control (deg)").bind(
            "MAIN", bindings=[PTUController, CVController.get_set("")])

        self.addForm("CAM_INFO", winForms.CameraInfo, name="Camera Information").bind(
            "MAIN", bindings=[CAMpayload, CAMwide])

        self.addForm("PAYLOAD", winForms.PayloadMenu, name="Payload Vision").bind(
            "MAIN", bindings=[CVController.get_set("Payload")])

        self.addForm("WIDE", winForms.WideMenu, name="Wide Angle Vision").bind(
            "MAIN", bindings=[CVController.get_set("Wide Angle"), PTUController])

        self.addForm("CREDITS", winForms.Credits, name="Credits").bind(
            "MAIN")


if __name__ == "__main__":
    '''
        A graphical user interface for the control of the cameras and PTU
        * a wide number of functions can be performed
        * only used for debugging and testing
    '''
    # Let the user know that data is being collected
    print "*** Please wait while data is collected ... ***"

    # Create a serial object that can read/write to the PTU
    PTUController = PTUController("/dev/ttyS0", 9600)

    # Create a camera object for the payload camera
    CAMpayload = camera.Camera(0, "Payload")
    CAMpayload.connect_camera()

    # Create a camera object for the wide angle camera
    CAMwide = camera.Camera(1, "Wide Angle")
    CAMwide.connect_camera()

    # Create worker sets for each camera
    setPayload = cwc.cvWorkerSets(CAMpayload, [wo.DisplayFeed, wo.DisplayCrosshair])
    setWide = cwc.cvWorkerSets(CAMwide, [wo.DisplayFeedInverted, wo.MotionCalibration, wo.ThresholdingBasic, wo.DisplayMotionBasic])
    setPTU = cwc.cvWorkerSets(None, [wo.PTUDisplay])

    # Create controller for cvWorkerSets
    CVController = cwc.cvWindowController([setPayload, setWide, setPTU], frameDelay=10)
    CVController.start()

    # Launch the gui
    app = App().run()

    # Close the serial connection
    PTUController.close()

    # Close the camera object, freeing device
    CAMpayload.disconnect_camera()
    CAMwide.disconnect_camera()

    # Stop image display controller threads
    CVController.stop()

    # Let the user know that everything is complete
    print "*** Fireball tracking system successfully closed! ***"
    exit(0)
