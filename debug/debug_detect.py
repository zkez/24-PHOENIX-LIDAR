import ctypes
import os
import shutil
from queue import Queue
from macro import PLUGIN_LIBRARY, car_engine_file_path, armor_engine_file_path, categories
from detect.detect import YoLov8TRT, ImageDisplayThread, WarmUpThread, InferCameraThread

if __name__ == "__main__":
    ctypes.CDLL(PLUGIN_LIBRARY)

    categories = ["B1", "B2", "B3", "B4", "B5", "B7", "R1", "R2", "R3", "R4", "R5", "R7"]
    if os.path.exists('output/'):
        shutil.rmtree('output/')
    os.makedirs('output/')
    # a YoLov8TRT instance
    yolov8_wrapper_car = YoLov8TRT(car_engine_file_path)
    yolov8_wrapper_armor = YoLov8TRT(armor_engine_file_path)

    try:
        print('batch size is', yolov8_wrapper_car.batch_size)

        for i in range(10):
            thread1 = WarmUpThread(yolov8_wrapper_car)
            thread1.start()
            thread1.join()

        image_queue = Queue()
        thread2 = ImageDisplayThread(image_queue)
        thread2.start()
        video_path = "../detect/images/15.mp4"
        # thread1 = InferVideoThread(yolov8_wrapper_car, yolov8_wrapper_armor, video_path)
        thread1 = InferCameraThread(yolov8_wrapper_car, yolov8_wrapper_armor, image_queue)
        thread1.start()
        thread1.join()

    finally:
        yolov8_wrapper_car.destroy()
        yolov8_wrapper_armor.destroy()
