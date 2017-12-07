import cv2
import os
import numpy as np

from packages.opencvController.camera import Camera

__loc__ = __cur_path__ = os.path.dirname(os.path.realpath(__file__)) + "/"
__filename__ = "mask.png"
__frame_wait__ = 10
__enter__ = 10


class Mask:
    ''' Allows the user to generate a mask for an input image source
    Usage:  LMB     -> place a point
            RMB     -> remove previous point
            r       -> reset all points
            enter   -> export image
    '''

    __red__ = (0, 0, 255)
    __green__ = (0, 255, 0)
    __blue__ = (255, 0, 0)
    __black__ = (0, 0, 0)
    __white__ = (255, 255, 255)

    def __init__(self, exportPath, name="Mask"):
        self.name = name
        self.exportPath = exportPath
        self.pts = []
        self.imgSize = None
        cv2.namedWindow(self.name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.name, self._on_click)

    def display(self, img):
        imgCol = None
        if img is not None:
            self.imgSize = img.shape
            imgCol = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            if len(self.pts) > 0:
                for i in range(len(self.pts)):
                    if i != 0:
                        cv2.line(imgCol, self.pts[i-1], self.pts[i], self.__red__, 2)
                    else:
                        cv2.line(imgCol, self.pts[i], self.pts[len(self.pts) - 1], self.__red__, 2)
                    cv2.circle(imgCol, self.pts[i], 2, self.__blue__, 3)
            cv2.
        return imgCol


    def export(self):
        print "Exporting mask as \"" + self.exportPath + "\""
        if self.imgSize is not None and len(self.pts) > 0:
            # Create black background
            img = np.zeros(self.imgSize, np.uint8)

            # Create polygon
            points = np.array(self.pts)
            points = points.reshape((-1, 1, 2))
            cv2.fillPoly(img, [points], self.__white__)

            # Export image
            cv2.imwrite(self.exportPath, img)

    def _on_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            self.pts.append( (x, y) )
        if event == cv2.EVENT_RBUTTONUP:
            if len(self.pts) > 0:
                self.pts.pop()

    def clear_pts(self):
        self.pts = []



if __name__ == "__main__":
    # Create image source
    cam = Camera(1, "Wide")
    cam.connect_camera()
    cam.startCapture()

    # Create masking object
    mask = Mask(__loc__ + __filename__)

    # Capture images
    while 1:
        img = cam.grab_numpy_image()
        img = cv2.flip(img, 0)

        imgCol = mask.display(img)

        if imgCol is not None:
            cv2.imshow(mask.name, imgCol)

            key = cv2.waitKey(__frame_wait__)
            if key == ord('z'):
                break
            elif key == __enter__:
                mask.export()
            elif key == ord('r'):
                mask.clear_pts()

    # Release
    cam.disconnect_camera()
    cv2.destroyAllWindows()
