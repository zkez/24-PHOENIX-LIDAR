import ctypes
import os
import time
import cv2
import sys
from tqdm import trange

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from macro import PLUGIN_LIBRARY, car_engine_file_path, armor_engine_file_path
from detect.detect import YoLov8TRT, Detect, DetectArmor, SortDetect
from common.common import armor_filter
from camera.camera import CameraThread


if __name__ == "__main__":
    ctypes.CDLL(PLUGIN_LIBRARY)

    categories = ["B1", "B2", "B3", "B4", "B5", "B7", "R1", "R2", "R3", "R4", "R5", "R7"]

    YOLOv8_car = YoLov8TRT(car_engine_file_path)
    YOLOv8_armor = YoLov8TRT(armor_engine_file_path)
    for i in trange(10, desc='warm up'):
        car_batch_image_raw, use_time_car, *a_car = YOLOv8_car.infer(YOLOv8_car.get_raw_image_zeros(), flag='car')
        armor_batch_image_raw, use_time_armor, *a_armor = YOLOv8_armor.infer(YOLOv8_armor.get_raw_image_zeros(), flag='armor')

    # cap = CameraThread(0)
    video_path = "../save_stuff/15.mp4"
    cap = cv2.VideoCapture(video_path)
    try:
        detect = Detect()
        armor = DetectArmor()
        sort = SortDetect()
        while True:
            t1 = time.time()
            ret, frame = cap.read()
            if ret:
                r, results, img = detect.run(YOLOv8_car, YOLOv8_armor, frame)
                results = armor_filter(results)
                print(results)
                # car_locations, img = sort.Sort_infer(YOLOv8_car, YOLOv8_armor, frame)
                # print(car_locations)
            else:
                break
            cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
            cv2.imshow('frame', img)
            cv2.waitKey(1)
            print('fps->{:.2f}'.format(1 / (time.time() - t1)))

    finally:
        YOLOv8_car.destroy()
        YOLOv8_armor.destroy()
