import ctypes
import os
import shutil
import cv2
from macro import PLUGIN_LIBRARY, car_engine_file_path, armor_engine_file_path
from detect.detect import YoLov8TRT, armor_post_process

if __name__ == "__main__":
    ctypes.CDLL(PLUGIN_LIBRARY)

    categories = ["B1", "B2", "B3", "B4", "B5", "B7", "R1", "R2", "R3", "R4", "R5", "R7"]
    if os.path.exists('output/'):
        shutil.rmtree('output/')
    os.makedirs('output/')

    YOLOv8_car = YoLov8TRT(car_engine_file_path)
    YOLOv8_armor = YoLov8TRT(armor_engine_file_path)

    try:
        video_path = "../detect/images/15.mp4"
        cap = cv2.VideoCapture(video_path)
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))

        armor_location_list = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            car_image, use_time_car, car_boxes, car_scores, car_classID, car_location \
                = YOLOv8_car.infer([frame])
            for i in range(len(car_boxes)):
                box = car_boxes[i]
                img = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                armor_image, use_time_armor, armor_boxes, armor_scores, armor_classID, armor_location \
                    = YOLOv8_armor.infer([img])

                armor_post_process(armor_location, box)

                armor_location_list.append(armor_location)

    finally:
        YOLOv8_car.destroy()
        YOLOv8_armor.destroy()
