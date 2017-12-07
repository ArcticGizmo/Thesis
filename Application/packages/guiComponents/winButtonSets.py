import npyscreen as ns
from typing import List

from .. other import Utilities as u


# Used to create a status bar at the bottom of the screen
def createStatusBar(actionForm, name="Status", space=4):
    oldY = actionForm.nextrely
    actionForm.nextrely = actionForm.lines - space
    actionForm.draw_line_at = actionForm.nextrely
    actionForm.nextrely += 1
    actionForm.nextrelx = 2
    status = actionForm.add(ns.TitleText, name=name, editable=False, begin_entry_at=10)
    actionForm.nextrely = oldY
    return status


# Used to create a general button at next widget position
def add_button(actionForm, name, callback, column=2, prevButton=None, horOffset=4, verOffset=0):
    if prevButton is not None:
        actionForm.nextrely += -1
        actionForm.nextrelx += int(len(prevButton.name)) + horOffset
    else:
        actionForm.nextrelx = column
    if verOffset > 0:
        actionForm.nextrely += verOffset

    button = actionForm.add(ns.ButtonPress, name=name)
    button.whenPressed = callback
    return button


# Used to create a general title text widget
def add_text(actionForm, name, value=None, editable=False, prevWidget=None, horOffset=4):
    if prevWidget is not None:
        actionForm.nextrely += -1
        actionForm.nextrelx += int(len(prevWidget.name)) + horOffset
    text = actionForm.add(ns.TitleText, name=name, editable=editable)
    if value is not None:
        text.value = str(value)
    return text


# used to create a multiline title text
def add_text_mult(actionForm, name, values=None, rows=1, editable=False, colstart=2):
    if colstart > 0:
        actionForm.nextrelx = colstart

    oldY = actionForm.nextrely
    text = actionForm.add(ns.TitleMultiLine, name=name, editable=editable)
    if values is not None:
        text.values = values
        actionForm.nextrely = oldY + len(values) + 1
    elif rows > 0:
        actionForm.nextrely = oldY + rows + 1

    return text


# A set of classes used to define button layouts
class buttsetBasicOpenClose():

    def __init__(self, actionForm, cvFunc, statusBar=None, column=2, horOffset=4):
        # type: (ns.ActionFormMinimal, cvWorkerSet, ns.TitleText) -> None
        self.form = actionForm
        self.cvFunc = cvFunc
        self.status = statusBar
        self.horOffset = horOffset
        self.column = column
        self.create()

    def create(self):
        self.form.nextrelx = self.column
        self.dispText = self.form.add(ns.TitleText, name=self.cvFunc.winName, editable=False)
        # Open window
        if len(self.dispText.name) > 14:
            self.form.nextrely -= 1

        # Create buttons
        self.open = add_button(self.form, "Open", self._on_open)
        self.close = add_button(self.form, "Close", self._on_close, prevButton=self.open)



    def _on_open(self):
        if self.status is not None:
            self.status.value = "Opening " + str(self.cvFunc.winName) + " ..."
            self.cvFunc.enable(True)
            self.form.display()

    def _on_close(self):
        if self.status is not None:
            self.status.value = "Closing " + str(self.cvFunc.winName) + " ..."
        self.cvFunc.enable(False)
        self.form.display()

# Class for the angle tracker
class targettingButtonSet():

    def __init__(self, actionForm, cvFunc, ptu, statusBar=None, column=2, horOffset=4):
        # type: (ns.ActionFormMinimal, cvObj, ns.TitleText) -> None
        self.PTU = ptu
        self.form = actionForm
        self.cvFunc = cvFunc
        self.status = statusBar
        self.horOffset = horOffset
        self.column = column
        self.create()

    def create(self):
        self.form.nextrelx = self.column
        self.dispText = self.form.add(ns.TitleText, name=self.cvFunc.winName, editable=False)
        if len(self.dispText.name) > 14:
            self.form.nextrely -= 1

        # Buttons
        self.open = add_button(self.form, "Open", self._on_open)
        self.close = add_button(self.form, "Close", self._on_close, prevButton=self.open)
        self.target = add_button(self.form, "Target", self._on_target, prevButton=self.close)

    def _on_open(self):
        if self.status is not None:
            self.status.value = "Opening " + str(self.cvFunc.winName) + " ..."
            self.cvFunc.enable(True)
            self.form.display()

    def _on_close(self):
        if self.status is not None:
            self.status.value = "Closing " + str(self.cvFunc.winName) + " ..."
        self.cvFunc.enable(False)
        self.form.display()

    def _on_target(self):
        if self.cvFunc.targetPos is not None:
            self.PTU.set_pan_deg(self.cvFunc.targetPos[0])
            self.PTU.set_tilt_deg(self.cvFunc.targetPos[1])


# Class for the threshold buttonset
class thresholdButtonSet():

    def __init__(self, actionForm, cvFunc, statusBar=None, column=2, horOffset=4):
        self.form = actionForm
        self.cvFunc = cvFunc
        self.status = statusBar
        self.horOffset = horOffset
        self.column = column
        self.create()

    def create(self):
        self.form.nextrelx =  self.column
        self.text = self.form.add(ns.TitleText, name=self.cvFunc.winName, editable=False)
        if len(self.text.name) > 14:
            self.form.nextrely -= 1

        self.open = add_button(self.form, "Open", self._on_open)
        self.close = add_button(self.form, "Close", self._on_close, prevButton=self.open)
        self.update = add_button(self.form, "Update", self._on_update, prevButton=self.close)
        self.threshDisp = add_text(self.form, "Thresh:", value=self.cvFunc.threshold, editable=True, prevWidget=self.update)


    def _on_open(self):
        if self.status is not None:
            self.status.value = "Opening " + str(self.cvFunc.winName) + " ..."
            self.cvFunc.enable(True)
            self.form.display()

    def _on_close(self):
        if self.status is not None:
            self.status.value = "Closing " + str(self.cvFunc.winName) + " ..."
            self.cvFunc.enable(False)
            self.form.display()

    def _on_update(self):
        if self.status is not None:
            checkedVal = u.intFromString(self.threshDisp.value)
            if checkedVal is not None:
                if u.between(0, checkedVal, 255):
                    self.status.value = "Threshold update to " + str(checkedVal)
                    self.cvFunc.threshold = checkedVal
                else:
                    self.status.value = "Error: Threshold out of range"
            else:
                self.status.value = "Error: No int found in set threshold value"
        self.form.display()


class motionButtonSetBasic():

    def __init__(self, actionForm, cvFunc, statusBar=None, column=2, horOffset=4):
        self.form = actionForm
        self.cvFunc = cvFunc
        self.status = statusBar
        self.horOffset = horOffset
        self.column = column
        self.create()

    def create(self):
        self.form.nextrelx = self.column
        self.text = self.form.add(ns.TitleText, name=self.cvFunc.winName, editable=False)
        if len(self.text.name) > 14:
            self.form.nextrely -= 1

        self.open = add_button(self.form, "Open", self._on_open)
        self.close = add_button(self.form, "Close", self._on_close, prevButton=self.open)
        self.update = add_button(self.form, "Update", self._on_update, prevButton=self.close)
        self.threshDisp = add_text(self.form, "Thresh:", value=self.cvFunc.threshold, editable=True, prevWidget=self.update)


    def _on_open(self):
        if self.status is not None:
            self.status.value = "Opening " + str(self.cvFunc.winName) + " ..."
            self.cvFunc.enable(True)
            self.form.display()

    def _on_close(self):
        if self.status is not None:
            self.status.value = "Closing " + str(self.cvFunc.winName) + " ..."
            self.cvFunc.enable(False)
            self.form.display()

    def _on_update(self):
        if self.status is not None:
            checkedVal = u.intFromString(self.threshDisp.value)
            if checkedVal is not None:
                if u.between(0, checkedVal, 255):
                    self.status.value = "Threshold update to " + str(checkedVal)
                    self.cvFunc.threshold = checkedVal
                else:
                    self.status.value = "Error: Threshold out of range"
            else:
                self.status.value = "Error: No int found in set threshold value"
        self.form.display()
