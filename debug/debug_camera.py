import cv2
import os
from camera import mvsdk
from camera.camera import CameraThread, tune_exposure


if __name__ == "__main__":
    ht = CameraThread(0)
    tune_exposure(ht.cap, ht._date, high_reso=True)
    cv2.namedWindow("test", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("test", 1280, 960)

    count = 0
    save_folder = '../save_stuff/photos/'
    while 1:
        ret, frame = ht.read()
        cv2.imshow('test', frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        if key == ord('s'):
            filename = os.path.join(save_folder, f'save_{count}.jpg')
            cv2.imwrite(filename, frame)
            count += 1
    ht.release()
    cv2.destroyAllWindows()
