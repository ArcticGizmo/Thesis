import cv2

__file_name__ = "achernarBase.avi"

if __name__ == "__main__":
    reader = cv2.VideoCapture(__file_name__)

    while reader.isOpened():
        ret, frame = reader.read()

        if frame is not None:
            cv2.circle(frame, (300,300), 1, (0,255,0), thickness=1)
            cv2.imshow("frame", frame)

        key = cv2.waitKey(10)
        if key & 0xFF == ord('z'):
            break

    reader.release()
    cv2.destroyAllWindows()