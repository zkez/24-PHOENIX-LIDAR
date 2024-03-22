from detect.detect import YoLov8TRT


class TrackDetector(object):
    def __init__(self, car_engine_file_path, armor_engine_file_path, frame):
        self.YOLOv8_car = YoLov8TRT(car_engine_file_path)
        self.YOLOv8_armor = YoLov8TRT(armor_engine_file_path)
        self.frame = frame

    def detect(self):
        car_image, car_use_time, car_boxes, car_classID, car_scores, car_location = (
            self.YOLOv8_car.infer([self.frame], flag='car'))
        for i in range(len(car_boxes)):
            box = car_boxes[i]
            img = self.frame[box[1]:box[3], box[0]:box[2]]
            armor_image, armor_use_time, armor_boxes, armor_classID, armor_scores, armor_location = (
                self.YOLOv8_armor.infer([img], flag='armor'))
            if len(armor_boxes) != 0:
                box[2] = box[2] - box[0]
                box[3] = box[3] - box[1]

