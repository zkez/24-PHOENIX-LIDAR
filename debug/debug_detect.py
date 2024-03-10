import ctypes
import os
import shutil
import time
import cv2
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from macro import PLUGIN_LIBRARY, car_engine_file_path, armor_engine_file_path
from detect.detect import YoLov8TRT
from detect.detect_common import armor_post_process
from camera.camera import HTCamera, CameraThread

if __name__ == "__main__":
    ctypes.CDLL(PLUGIN_LIBRARY)

    categories = ["B1", "B2", "B3", "B4", "B5", "B7", "R1", "R2", "R3", "R4", "R5", "R7"]
    if os.path.exists('output/'):
        shutil.rmtree('output/')
    os.makedirs('output/')

    YOLOv8_car = YoLov8TRT(car_engine_file_path)
    YOLOv8_armor = YoLov8TRT(armor_engine_file_path)
    cap = CameraThread(0)
    for i in range(10):
        car_batch_image_raw, use_time_car, *a_car = YOLOv8_car.infer(YOLOv8_car.get_raw_image_zeros())
        armor_batch_image_raw, use_time_armor, *a_armor = YOLOv8_armor.infer(YOLOv8_armor.get_raw_image_zeros())

    try:
        while True:
            ret, frame = cap.read()
            if ret:
                car_image, use_time_car, car_boxes, car_scores, car_classID, car_location \
                    = YOLOv8_car.infer([frame])
                for i in range(len(car_boxes)):
                    box = car_boxes[i]
                    img = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                    armor_image, use_time_armor, armor_boxes, armor_scores, armor_classID, armor_location \
                        = YOLOv8_armor.infer([img])
                    armor_post_process(armor_location, box)
                    print(armor_location)
                    for j in range(len(armor_boxes)):
                        cv2.rectangle(frame, (int(armor_location[j][10]), int(armor_location[j][11])),
                                              (int(armor_location[j][12]), int(armor_location[j][13])), (0, 255, 0), 2)
                        cv2.putText(frame, categories[int(armor_location[j][9])], (int(armor_location[j][10]),
                                                                              int(armor_location[j][11])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        cv2.imwrite('output/{}.jpg'.format(time.time()), frame)

                    print('time->{:.2f}ms, fps->{}'.format((use_time_car + use_time_armor) * 1000,
                                                                      1 / (use_time_car + use_time_armor)))
            else:
                break

    finally:
        YOLOv8_car.destroy()
        YOLOv8_armor.destroy()
