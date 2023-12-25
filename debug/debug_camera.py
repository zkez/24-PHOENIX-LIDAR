import cv2

from camera import mvsdk
from camera.camera import CameraThread, tune_exposure


if __name__ == "__main__":
    ht = CameraThread(0)
    tune_exposure(ht.cap, ht._date, high_reso=True)
    cv2.namedWindow("test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("test", 1280, 960)
    # mvsdk.CameraReadParameterFromFile(ht.cap.hCamera, '')
    while 1:
        ret, frame = ht.read()
        cv2.imshow('test', frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
    ht.release()
    cv2.destroyAllWindows()
