import npyscreen as ns
import PyCapture2

from .. other import Utilities as u
from .. opencvController import  cvWindowController as wc, cvWindowObjects as wo
import winButtonSets as bs


# base class that allows instantiation of un instantiated windows
class winFormBase():

    # give a return form id for on_ok and a group of bindings that can be used by the window
    def bind(self, ret_form_id, bindings=None):
        pass


# Opening menu for the terminal
class MainMenu(ns.ActionFormMinimal):
    def create(self):
        self.add(ns.TitleText, name="Welcome to sentry mode", editable=False)
        self.nextrely += 1

        # camera settings window
        self.butCamera = self.add(ns.ButtonPress, name="Camera Settings")
        self.butCamera.whenPressed = self.on_cameraSettings

        # PTU settings window
        self.butManual = self.add(ns.ButtonPress, name="PTU Control")
        self.butManual.whenPressed = self.on_PTU

        # Payload operations
        self.butPayload = self.add(ns.ButtonPress, name="Payload Control")
        self.butPayload.whenPressed = self.on_payload

        # Wide angle lens operations
        self.butWideAngle = self.add(ns.ButtonPress, name="Wide Angle Control")
        self.butWideAngle.whenPressed = self.on_wideAngle

        # Credits
        self.nextrely += 1
        self.butCredits = self.add(ns.ButtonPress, name="Credits")
        self.butCredits.whenPressed = self.on_credits

    def on_cameraSettings(self):
        self.parentApp.switchForm("CAM_INFO")

    def on_PTU(self):
        self.parentApp.switchForm("PTU")

    def on_payload(self):
        self.parentApp.switchForm("PAYLOAD")

    def on_wideAngle(self):
        self.parentApp.switchForm("WIDE")
        pass

    def on_credits(self):
        self.parentApp.switchForm("CREDITS")

    # Predefined function for when "ok" is pressed
    def on_ok(self):
        self.parentApp.setNextForm(None)


# All controls for the camera information
class CameraInfo(ns.ActionFormMinimal, winFormBase):

    def bind(self, ret_form_id, bindings=None):
        self.CAMpayload = bindings[0]
        self.CAMwide = bindings[1]
        self.ret_form_id = ret_form_id
        self.info = []

        # Buttons
        self.butPayload = bs.add_button(self, self.CAMpayload.name, self.on_displayPayload)
        self.butWide = bs.add_button(self, self.CAMwide.name, self.on_displayWide, prevButton=self.butPayload)

        # Payload Camera Info
        self.camInfoPayload = bs.add_text_mult(self, "Camera Information", rows=8)
        self.on_displayPayload()

        # Py Capture version
        libVer = PyCapture2.getLibraryVersion()
        self.pyCaptureInfo = "PyCapture2 library version " + str(libVer[0]) + "." + str(libVer[1]) + "." + str(
            libVer[3])

        self.pyCaptureInfoDisp = bs.add_text(self, "Py Capture Information", value=self.pyCaptureInfo)

    # Display payload information
    def on_displayPayload(self):
        temp = self.CAMpayload.get_camera_info()[:]
        temp.insert(0, "Payload Camera")
        self.info = temp
        self.displayInfo()

    # Display wide angle information
    def on_displayWide(self):
        temp = self.CAMwide.get_camera_info()[:]
        temp.insert(0, "Wide Angle")
        self.info = temp
        self.displayInfo()

    # Display camera informaiton
    def displayInfo(self):
        self.camInfoPayload.values = self.info
        self.display()

    # Called when the window is closed
    def on_ok(self):
        self.parentApp.setNextForm(self.ret_form_id)


# Contains the credits of the project
class Credits(ns.ActionFormMinimal, winFormBase):

    def bind(self, ret_form_id, bindings=None):
        self.ret_from_id = ret_form_id
        self.title = self.add(ns.TitleText, name="Credits", editable=False)

        self.title.value = "Jonathan Howell 2017 Thesis Project"

    # Called when the window is closed
    def on_ok(self):
        self.parentApp.setNextForm(self.ret_from_id)


# Allows for mode changing (YET TO BE COMPLETE)
class ModeChangeMenu(ns.SplitForm):
    def create(self):
        return

    def assign(self, serialLink):
        self.PTU = serialLink
        self.show_aty = 5
        self.show_atx = 15

        self.panModes = self.add(ns.TitleSelectOne, name="Pan Modes", scroll_exit=True,
                                 values=['F', 'H', 'Q', 'E', 'A'], check_value_change=True,
                                 begin_entry_at=10, field_width=18, max_height=6,
                                 value=u.toInt(self.PTU.panMode))
        self.nextrelx = 30
        self.nextrely = 2

        self.tiltModes = self.add(ns.TitleSelectOne, name="Tilt Modes", scroll_exit=True,
                                  values=['F', 'H', 'Q', 'E', 'A'], check_value_change=True,
                                  begin_entry_at=10, field_width=18, max_height=6,
                                  value=u.toInt(self.PTU.tiltMode))
        self.nextrelx = 0
        self.updateBut = self.add(ns.ButtonPress, name="Update")
        self.updateBut.whenPressed = self.on_update

        self.draw_line_at = self.nextrely
        self.nextrely += 1
        self.nextrelx += 2
        self.status = self.add(ns.TitleText, name="Status:", editable=False, begin_entry_at=10)

    def on_update(self):
        s = self.PTU.change_mode(self.panModes.value, self.tiltModes.value)
        if s is not None:
            self.status.value = s
            self.display()

    def afterEditing(self):
        self.parentApp.setNextForm("MAIN")


# All control for the payload camera
class PayloadMenu(ns.ActionFormMinimal, ns.SplitForm, winFormBase):

    def bind(self, ret_form_id, bindings=None):
        self.set = bindings[0]
        self.ret_form_id = ret_form_id

        # control positioning for form
        self.show_atx = 0
        self.show_aty = 0

        # Create status bar
        self.status = bs.createStatusBar(self)

        # Create button sets
        bs.buttsetBasicOpenClose(self, self.set.get_cv_func(wo.DisplayFeed), statusBar=self.status)
        self.nextrely += 1
        bs.buttsetBasicOpenClose(self, self.set.get_cv_func(wo.DisplayCrosshair), statusBar=self.status)

    # Called when the window is closed
    def on_ok(self):
        self.status.value = ""
        self.parentApp.setNextForm(self.ret_form_id)


# Allows for the control of the PTU unit in degs
class PTUDegMenu( ns.SplitForm, winFormBase):

    # Used to assign a PTU controller to the window
    def bind(self, ret_form_id, bindings=None):
        # save input
        self.PTU = bindings[0]
        self.set = bindings[1]  # Allows for ptu display graphic
        self.set.get_cv_func(wo.PTUDisplay).assign([self.PTU])
        self.ret_form_id = ret_form_id

        # Status output
        self.status = bs.createStatusBar(self)

        # Pan range
        panRange = u.round_float_array(self.PTU.panRangeDeg[:])
        self.panRange = bs.add_text(self, "Pan Range:", value=panRange)

        # Tilt range
        tiltRange = u.round_float_array(self.PTU.tiltRangeDeg[:])
        self.tiltRange = bs.add_text(self, "Tilt Range:", value=tiltRange)

        # pan and tilt speed
        self.nextrely += 1
        self.panSpeed = bs.add_text(self, "Pan speed:", value=u.round_float(self.PTU.panSpeedDeg), editable=True)
        self.tiltSpeed = bs.add_text(self, "Tilt speed:", value=u.round_float(self.PTU.tiltSpeedDeg), editable=True)

        # update speed button
        self.updateSpeed = bs.add_button(self, "Update Speed", self.on_update_speed)

        # pan and tilt position
        self.nextrely += 1
        self.panPos = bs.add_text(self, "Pan Pos:", value=u.round_float(self.PTU.panPosDeg), editable=True)
        self.tiltPos = bs.add_text(self, "Tilt Pos:", value=u.round_float(self.PTU.tiltPosDeg), editable=True)

        self.updatePos = bs.add_button(self, "Update Pos", self.on_update_pos, verOffset=1)

        self.getPos = bs.add_button(self, "Get Position", self.on_get_pos, verOffset=1)
        self.reset = bs.add_button(self, "Reset", self.on_reset, prevButton=self.getPos)
        self.stop = bs.add_button(self, "Stop", self.on_stop, prevButton=self.reset)

        self.nextrely += 1
        bs.buttsetBasicOpenClose(self, self.set.get_cv_func(wo.PTUDisplay), statusBar=self.status)



    # This is called to update all displayed inputs
    def update(self):
        self.panPos.value = str(u.round_float(self.PTU.panPosDeg))
        self.tiltPos.value = str(u.round_float(self.PTU.tiltPosDeg))
        self.panSpeed.value = str(u.round_float(self.PTU.panSpeedDeg))
        self.tiltSpeed.value = str(u.round_float(self.PTU.tiltSpeedDeg))
        self.display()

    def on_stop(self):
        self.PTU.write("H ")
        self.status.value = "STOP!"
        self.display()

    def on_update_pos(self):
        s = "POS ("
        s += self.PTU.set_pan_deg(self.panPos.value)
        s += ", "
        s += self.PTU.set_tilt_deg(self.tiltPos.value)
        s += ")"
        self.status.value = s
        self.update()

    def on_update_speed(self):
        s = "SPD: ("
        s += self.PTU.set_pan_speed_deg(self.panSpeed.value)
        s += ", "
        s += self.PTU.set_tilt_speed_deg(self.tiltSpeed.value)
        s += ")"
        self.status.value = s
        self.update()

    def on_get_pos(self):
        self.PTU.get_pan()
        self.PTU.get_tilt()
        s = "Cur: ("
        s += str(u.round_float(self.PTU.panPosDeg))
        s += ", "
        s += str(u.round_float(self.PTU.tiltPosDeg))
        s += ")"

        self.status.value = s
        self.display()

    def on_reset(self):
        self.PTU.set_pan(0)
        self.PTU.set_tilt(0)
        self.panPos.value = "0"
        self.tiltPos.value = str(self.PTU.tiltPosDeg)
        self.status.value = "Reset"
        self.display()

    def afterEditing(self):
        self.status.value = ""
        self.parentApp.setNextForm(self.ret_form_id)


# Allows for the control of the PTU unit in counts (legacy)
class PTUMenu(ns.SplitForm, winFormBase):

    def bind(self, ret_form_id, bindings=None):
        self.PTU = bindings[0]
        self.ret_form_id = ret_form_id

        # Control centering of form
        self.show_atx = 12
        self.show_aty = 2

        # Pan and tilt ranges
        self.panRange = bs.add_text(self, "Pan Range:", value=self.PTU.panRange)
        self.tiltRange = bs.add_text(self, "Tilt Range:", value=self.PTU.tiltRange)

        # pan and tilt speed
        self.nextrely += 1
        self.panSpeed = bs.add_text(self, "Pan speed:", value=self.PTU.panSpeed, editable=True)
        self.tiltSpeed = bs.add_text(self, "Tilt speed:", value=self.PTU.tiltSpeed, editable=True)

        # update speed button
        self.nextrely += 1
        self.updateSpeed = bs.add_button(self, "Update Speed", self.on_update_speed)

        # pan and tilt position
        self.nextrely += 1

        self.panPos = self.add(ns.TitleText, name="Pan Pos:")
        self.panPos.value = str(self.PTU.panPos)
        self.tiltPos = self.add(ns.TitleText, name="Tilt Pos:")
        self.tiltPos.value = str(self.PTU.tiltPos)

        # Update pos button
        self.nextrely += 1
        self.updatePos = self.add(ns.ButtonPress, name="Update Pos")
        self.updatePos.whenPressed = self.on_update_pos

        # Get current position
        self.nextrely += 1
        self.getPos = self.add(ns.ButtonPress, name="Get Position")
        self.getPos.whenPressed = self.on_getPos

        # Reset to default
        self.nextrely += -1
        self.nextrelx += int(len(self.getPos.name)) + 4
        self.reset = self.add(ns.ButtonPress, name="Reset")
        self.reset.whenPressed = self.on_reset

        # stop button
        self.nextrely += -1
        self.nextrelx += int(len(self.reset.name)) + 4
        self.stop = self.add(ns.ButtonPress, name="Stop")
        self.stop.whenPressed = self.on_stop

        # Status output
        self.draw_line_at = self.nextrely
        self.nextrelx = 2
        self.nextrely += 1
        self.status = self.add(ns.TitleText, name="Status:", editable=False, begin_entry_at=10)

    # This is called to update all displayed values
    def update(self):
        self.panPos.value = str(self.PTU.panPos)
        self.tiltPos.value = str(self.PTU.tiltPos)
        self.panSpeed.value = str(self.PTU.panSpeed)
        self.tiltSpeed.value = str(self.PTU.tiltSpeed)
        self.display()

    def on_stop(self):
        self.PTU.write("H ")
        self.status.value = "STOP!"
        self.display()

    def on_update_pos(self):
        s = "POS ("
        s += self.PTU.set_pan(self.panPos.value)
        s += ", "
        s += self.PTU.set_tilt(self.tiltPos.value)
        s += ")"
        self.status.value = s
        self.update()

    def on_update_speed(self):
        s = "SPD: ("
        s += self.PTU.set_pan_speed(self.panSpeed.value)
        s += ", "
        s += self.PTU.set_tilt_speed(self.tiltSpeed.value)
        s += ")"
        self.status.value = s
        self.update()

    def on_getPos(self):
        self.PTU.get_pan()
        self.PTU.get_tilt()
        s = "Cur: ("
        s += str(self.PTU.panPos)
        s += ", "
        s += str(self.PTU.tiltPos)
        s += ")"

        self.status.value = s
        self.display()

    def on_reset(self):
        self.PTU.set_pan(0)
        self.PTU.set_tilt(0)
        self.panPos.value = "0"
        self.tiltPos.value = "0"
        self.status.value = "Reset"
        self.display()

    def afterEditing(self):
        self.status.value = ""
        self.parentApp.setNextForm(self.ret_form_id)


# All controls for the wide angle camera
class WideMenu(ns.ActionFormMinimal, ns.SplitForm, winFormBase):

    def bind(self, ret_form_id, bindings=None):
        self.set = bindings[0]
        self.PTU = bindings[1]
        self.set.get_cv_func(wo.MotionCalibration).assign([self.PTU])

        self.ret_form_id = ret_form_id

        # control positioning of form
        self.show_atx = 0
        self.show_aty = 0

        # Create status bar
        self.status = bs.createStatusBar(self)

        # Create button sets
        bs.buttsetBasicOpenClose(self, self.set.get_cv_func(wo.DisplayFeedInverted), statusBar=self.status)
        bs.targettingButtonSet(self, self.set.get_cv_func(wo.MotionCalibration), self.PTU, statusBar=self.status)
        bs.thresholdButtonSet(self, self.set.get_cv_func(wo.ThresholdingBasic), statusBar=self.status)
        bs.motionButtonSetBasic(self, self.set.get_cv_func(wo.DisplayMotionBasic), statusBar=self.status)

    # Called when the window is closed
    def on_ok(self):
        self.status.value = ""
        self.parentApp.setNextForm(self.ret_form_id)







