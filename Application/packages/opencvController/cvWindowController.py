import threading
import cv2
from typing import List


__timeout__ = 3

# Responsible for running all cv operations for a single camera
class cvWorkerSets():

    def __init__(self, cam, funcs):
        self.cam = cam
        if cam is not None:
            self.name = cam.name
        else:
            self.name = ""
        self.cvObjs = []

        # Instantiate given cvFunctions
        if funcs is not None:
            for f in funcs:
                self.cvObjs.append(f(self.name))

    # Returns instantiated form of "classType" from within self.cvOjs
    def get_cv_func(self, classType):
        # type: (type) -> object
        ret = None
        for c in self.cvObjs:
            if isinstance(c, classType):
                ret = c
                break
        return ret


# Coordinator for all cvWorker threads
class cvWindowController():

    def __init__(self, sets, frameDelay=20):
        self.thread = None
        self.run = False
        self.sets = sets

        if sets is not None:
            # give the sets and frameDelay to the worker
            self.thread = cvWorker(self.sets, frameDelay)

    def get_set(self, name):
        for s in self.sets:
            if s.name == name:
                return s
        else:
            return None


    def get_set_id(self, name):
        for x in range(0, len(self.sets)):
            if self.sets[x].name == name:
                return x
        else:
                return None

    def start(self):
        self.run = True
        self.thread.enabled = True
        self.thread.start()

    def stop(self):
        self.run = False
        if self.thread is not None:
            print "Closing openCV thread"
            self.thread.enabled = False

            if self.thread.isAlive():
                self.thread.join(__timeout__)
            if self.thread.isAlive():
                print "\tThread failed to close"
            else:
                print "\tThread successfully closed"
        else:
            print "\tNo thread to close"

        # Destroy all cv2 windows
        cv2.destroyAllWindows()


class cvWorker(threading.Thread):

    def __init__(self, sets, frameDelay):
        super(cvWorker, self).__init__()
        self.enabled = False
        self.sets = sets
        self.frameDelay = frameDelay

    def run(self):
        succ = []

        # Determine what cameras are working
        for s in self.sets:
            if s.cam is not None:
                succ.append(s.cam.startCapture())
            else:
                succ.append(False)

        # While thread is active
        while self.enabled:
            # Iterate through each working camera to get frames. Else iterate through non camera events
            for i in range(0, len(succ)):
                if succ[i] is not False:
                    # iterate through all related cvObjs for a given frame
                    img = self.sets[i].cam.grab_numpy_image()
                    for o in self.sets[i].cvObjs:
                        o.run(img)
                        o.close()
                else:
                    for o in self.sets[i].cvObjs:
                        o.run(None)
                        o.close()

            cv2.waitKey(self.frameDelay)

