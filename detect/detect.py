import threading
import time
import cv2
import numpy as np
import pycuda.autoinit
import pycuda.driver as cuda
import tensorrt as trt
from macro import CONF_THRESH_CAR, IOU_THRESHOLD, categories, armor_locations, CONF_THRESH_ARMOR
from common.common import armor_post_process


class YoLov8TRT(object):
    def __init__(self, engine_file_path):
        self.ctx = cuda.Device(0).make_context()
        stream = cuda.Stream()
        TRT_LOGGER = trt.Logger(trt.Logger.INFO)
        runtime = trt.Runtime(TRT_LOGGER)

        with open(engine_file_path, "rb") as f:
            engine = runtime.deserialize_cuda_engine(f.read())
        context = engine.create_execution_context()

        host_inputs = []
        cuda_inputs = []
        host_outputs = []
        cuda_outputs = []
        bindings = []

        for binding in engine:
            size = trt.volume(engine.get_binding_shape(binding)) * engine.max_batch_size
            dtype = trt.nptype(engine.get_binding_dtype(binding))
            host_mem = cuda.pagelocked_empty(size, dtype)
            cuda_mem = cuda.mem_alloc(host_mem.nbytes)
            bindings.append(int(cuda_mem))
            if engine.binding_is_input(binding):
                self.input_w = engine.get_binding_shape(binding)[-1]
                self.input_h = engine.get_binding_shape(binding)[-2]
                host_inputs.append(host_mem)
                cuda_inputs.append(cuda_mem)
            else:
                host_outputs.append(host_mem)
                cuda_outputs.append(cuda_mem)

        self.stream = stream
        self.context = context
        self.engine = engine
        self.host_inputs = host_inputs
        self.cuda_inputs = cuda_inputs
        self.host_outputs = host_outputs
        self.cuda_outputs = cuda_outputs
        self.bindings = bindings
        self.batch_size = engine.max_batch_size

    def infer(self, raw_image_generator, flag):
        threading.Thread.__init__(self)
        self.ctx.push()
        stream = self.stream
        context = self.context
        engine = self.engine
        host_inputs = self.host_inputs
        cuda_inputs = self.cuda_inputs
        host_outputs = self.host_outputs
        cuda_outputs = self.cuda_outputs
        bindings = self.bindings

        batch_image_raw = []
        batch_origin_h = []
        batch_origin_w = []
        batch_input_image = np.empty(shape=[self.batch_size, 3, self.input_h, self.input_w])
        for i, image_raw in enumerate(raw_image_generator):
            input_image, image_raw, origin_h, origin_w = self.preprocess_image(image_raw)
            batch_image_raw.append(image_raw)
            batch_origin_h.append(origin_h)
            batch_origin_w.append(origin_w)
            np.copyto(batch_input_image[i], input_image)
        batch_input_image = np.ascontiguousarray(batch_input_image)

        np.copyto(host_inputs[0], batch_input_image.ravel())
        start = time.time()
        cuda.memcpy_htod_async(cuda_inputs[0], host_inputs[0], stream)
        context.execute_async(batch_size=self.batch_size, bindings=bindings, stream_handle=stream.handle)
        cuda.memcpy_dtoh_async(host_outputs[0], cuda_outputs[0], stream)
        stream.synchronize()
        end = time.time()

        self.ctx.pop()

        output = host_outputs[0]
        result_boxes = []
        result_scores = []
        result_classID = []
        for i in range(self.batch_size):
            result_boxes, result_scores, result_classID, det = self.post_process(
                output[i * 38001: (i + 1) * 38001], batch_origin_h[i], batch_origin_w[i], flag
            )

        return batch_image_raw, end - start, result_boxes, result_scores, result_classID, det

    def destroy(self):
        self.ctx.pop()

    def get_raw_image(self, image_path_batch):
        for img_path in image_path_batch:
            yield cv2.imread(img_path)

    def get_raw_image_zeros(self, image_path_batch=None):
        for _ in range(self.batch_size):
            yield np.zeros([self.input_h, self.input_w, 3], dtype=np.uint8)

    def preprocess_image(self, raw_bgr_image):
        """
        description: Convert BGR image to RGB,
                     resize and pad it to target size, normalize to [0,1],
                     transform to NCHW format.
        param:
            input_image_path: str, image path
        return:
            image:  the processed image
            image_raw: the original image
            h: original height
            w: original width
        """
        image_raw = raw_bgr_image
        h, w, c = image_raw.shape
        image = cv2.cvtColor(image_raw, cv2.COLOR_BGR2RGB)
        r_w = self.input_w / w
        r_h = self.input_h / h
        if r_h > r_w:
            tw = self.input_w
            th = int(r_w * h)
            tx1 = tx2 = 0
            ty1 = int((self.input_h - th) / 2)
            ty2 = self.input_h - th - ty1
        else:
            tw = int(r_h * w)
            th = self.input_h
            tx1 = int((self.input_w - tw) / 2)
            tx2 = self.input_w - tw - tx1
            ty1 = ty2 = 0
        image = cv2.resize(image, (tw, th))
        image = cv2.copyMakeBorder(
            image, ty1, ty2, tx1, tx2, cv2.BORDER_CONSTANT, None, (128, 128, 128)
        )
        image = image.astype(np.float32)
        image /= 255.0
        image = np.transpose(image, [2, 0, 1])
        image = np.expand_dims(image, axis=0)
        image = np.ascontiguousarray(image)
        return image, image_raw, h, w

    def xywh2xyxy(self, origin_h, origin_w, x):
        """
        description:    Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
        param:
            origin_h:   height of original image
            origin_w:   width of original image
            x:          A boxes numpy, each row is a box [center_x, center_y, w, h]
        return:
            y:          A boxes numpy, each row is a box [x1, y1, x2, y2]
        """
        y = np.zeros_like(x)
        r_w = self.input_w / origin_w
        r_h = self.input_h / origin_h
        if r_h > r_w:
            y[:, 0] = x[:, 0]
            y[:, 2] = x[:, 2]
            y[:, 1] = x[:, 1] - (self.input_h - r_w * origin_h) / 2
            y[:, 3] = x[:, 3] - (self.input_h - r_w * origin_h) / 2
            y /= r_w
        else:
            y[:, 0] = x[:, 0] - (self.input_w - r_h * origin_w) / 2
            y[:, 2] = x[:, 2] - (self.input_w - r_h * origin_w) / 2
            y[:, 1] = x[:, 1]
            y[:, 3] = x[:, 3]
            y /= r_h

        return y

    def xyxy4xyxy(self, y):
        """
        description:    Convert nx4 boxes from [x1, y1, x2, y2] to [x3, y3, x4, y4, x5, y5, x6, y6]
                    where xy3=top-left, xy4=bottom-left, xy5=bottom-right, xy6=top-right(Counterclockwise)
        param:
            origin_h:   height of original image
            origin_w:   width of original image
            y:          A boxes numpy, each row is a box [x1, y1, x2, y2]
        return:
            z:          A boxes numpy, each row is a box [x3, y3, x4, y4, x5, y5, x6, y6]
        """
        z = np.zeros((y.shape[0], 8))
        z[:, 0] = y[:, 0]
        z[:, 1] = y[:, 1]
        z[:, 2] = y[:, 0]
        z[:, 3] = y[:, 3]
        z[:, 4] = y[:, 2]
        z[:, 5] = y[:, 3]
        z[:, 6] = y[:, 2]
        z[:, 7] = y[:, 1]

        return z

    def post_process(self, output, origin_h, origin_w, flag):
        """
        description: postprocess the prediction
        param:
            output:     A numpy likes [num_boxes,cx,cy,w,h,conf,cls_id, cx,cy,w,h,conf,cls_id, ...]
            origin_h:   height of original image
            origin_w:   width of original image
        return:
            result_boxes: finally boxes, a boxes numpy, each row is a box [x1, y1, x2, y2]
            result_scores: finally scores, a numpy, each element is the score correspoing to box
            result_classID: finally classID, a numpy, each element is the classID correspoing to box
        """
        num = int(output[0])
        pred = np.reshape(output[1:], (-1, 38))[:num, :]
        if flag == 'car':
            boxes = self.non_max_suppression(pred, origin_h, origin_w, conf_thresh=CONF_THRESH_CAR, nms_thresh=IOU_THRESHOLD)
        elif flag == 'armor':
            boxes = self.non_max_suppression(pred, origin_h, origin_w, conf_thresh=CONF_THRESH_ARMOR, nms_thresh=IOU_THRESHOLD)
        result_boxes = boxes[:, :4] if len(boxes) else np.array([])
        result_scores = boxes[:, 4] if len(boxes) else np.array([])
        result_classID = boxes[:, 5] if len(boxes) else np.array([])
        result_4xyxy = self.xyxy4xyxy(result_boxes) if len(result_boxes) else np.array([])

        r_boxes = np.array(result_boxes).reshape(-1, 4)
        r_scores = np.array(result_scores).reshape(-1, 1)
        r_classID = np.array(result_classID).reshape(-1, 1)
        r_4xyxy = np.array(result_4xyxy).reshape(-1, 8)

        det = np.concatenate((r_4xyxy, r_scores, r_classID, r_boxes), axis=1)
        # xyxy -> xywh
        det[:, 12] = det[:, 12] - det[:, 10]
        det[:, 13] = det[:, 13] - det[:, 11]
        return result_boxes, result_scores, result_classID, det

    def bbox_iou(self, box1, box2, x1y1x2y2=True):
        """
        description: compute the IoU of two bounding boxes
        param:
            box1: A box coordinate (can be (x1, y1, x2, y2) or (x, y, w, h))
            box2: A box coordinate (can be (x1, y1, x2, y2) or (x, y, w, h))
            x1y1x2y2: select the coordinate format
        return:
            iou: computed iou
        """
        if not x1y1x2y2:
            b1_x1, b1_x2 = box1[:, 0] - box1[:, 2] / 2, box1[:, 0] + box1[:, 2] / 2
            b1_y1, b1_y2 = box1[:, 1] - box1[:, 3] / 2, box1[:, 1] + box1[:, 3] / 2
            b2_x1, b2_x2 = box2[:, 0] - box2[:, 2] / 2, box2[:, 0] + box2[:, 2] / 2
            b2_y1, b2_y2 = box2[:, 1] - box2[:, 3] / 2, box2[:, 1] + box2[:, 3] / 2
        else:
            b1_x1, b1_y1, b1_x2, b1_y2 = box1[:, 0], box1[:, 1], box1[:, 2], box1[:, 3]
            b2_x1, b2_y1, b2_x2, b2_y2 = box2[:, 0], box2[:, 1], box2[:, 2], box2[:, 3]

        inter_rect_x1 = np.maximum(b1_x1, b2_x1)
        inter_rect_y1 = np.maximum(b1_y1, b2_y1)
        inter_rect_x2 = np.minimum(b1_x2, b2_x2)
        inter_rect_y2 = np.minimum(b1_y2, b2_y2)

        inter_area = np.clip(inter_rect_x2 - inter_rect_x1 + 1, 0, None) * \
                     np.clip(inter_rect_y2 - inter_rect_y1 + 1, 0, None)

        b1_area = (b1_x2 - b1_x1 + 1) * (b1_y2 - b1_y1 + 1)
        b2_area = (b2_x2 - b2_x1 + 1) * (b2_y2 - b2_y1 + 1)

        iou = inter_area / (b1_area + b2_area - inter_area + 1e-16)

        return iou

    def non_max_suppression(self, prediction, origin_h, origin_w, conf_thresh=0.5, nms_thresh=0.4):
        """
        description: Removes detections with lower object confidence score than 'conf_thresh' and performs
        Non-Maximum Suppression to further filter detections.
        param:
            prediction: detections, (x1, y1, x2, y2, conf, cls_id)
            origin_h: original image height
            origin_w: original image width
            conf_thresh: a confidence threshold to filter detections
            nms_thresh: an iou threshold to filter detections
        return:
            boxes: output after nms with the shape (x1, y1, x2, y2, conf, cls_id)
        """
        boxes = prediction[prediction[:, 4] >= conf_thresh]
        boxes[:, :4] = self.xywh2xyxy(origin_h, origin_w, boxes[:, :4])

        boxes[:, 0] = np.clip(boxes[:, 0], 0, origin_w - 1)
        boxes[:, 2] = np.clip(boxes[:, 2], 0, origin_w - 1)
        boxes[:, 1] = np.clip(boxes[:, 1], 0, origin_h - 1)
        boxes[:, 3] = np.clip(boxes[:, 3], 0, origin_h - 1)

        confs = boxes[:, 4]

        boxes = boxes[np.argsort(-confs)]

        keep_boxes = []
        while boxes.shape[0]:
            large_overlap = self.bbox_iou(np.expand_dims(boxes[0, :4], 0), boxes[:, :4]) > nms_thresh
            label_match = boxes[0, -1] == boxes[:, -1]
            invalid = large_overlap & label_match
            keep_boxes += [boxes[0]]
            boxes = boxes[~invalid]
        boxes = np.stack(keep_boxes, 0) if len(keep_boxes) else np.array([])
        return boxes


class Detect(object):
    frameCount = 0
    previous_boxes = None

    @staticmethod
    def car_armor_infer(carNet, armorNet, frame):
        locations = []
        image_raw, use_time_car, car_boxes, car_scores, car_classID, car_location \
            = carNet.infer([frame], flag='car')

        for j in range(len(car_boxes)):
            box = car_boxes[j]
            img = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
            img_raw, use_time_armor, armor_boxes, armor_scores, armor_classID, armor_location \
                = armorNet.infer([img], flag='armor')

            armor_post_process(armor_location, box)
            locations.append(armor_location)
            array_locations = np.concatenate(locations, axis=0)

            for i in range(len(armor_location)):
                cv2.rectangle(image_raw[0], (int(armor_location[i][10]), int(armor_location[i][11])),
                              (int(armor_location[i][12]+armor_location[i][10]), int(armor_location[i][13]+armor_location[i][11])), (0, 255, 0), 2)
                cv2.putText(image_raw[0], "{}".format(categories[int(armor_location[i][9])]),
                            (int(armor_location[i][10]), int(armor_location[i][11])), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0), 2)

        if len(locations) > 0:
            locations.pop()
            return True, array_locations.reshape(-1, 14), image_raw[0]
        else:
            return False, None, frame

    def run(self, YOLOv8_car, YOLOv8_armor, frame):
        if self.frameCount == 0:
            r, locations, img = self.car_armor_infer(YOLOv8_car, YOLOv8_armor, frame)
            self.previous_boxes = locations
            self.frameCount += 1
            if locations is not None:
                return True, locations, img
            else:
                return False, None, img
        else:
            locations = []
            image_raw, use_time_car, car_boxes, car_scores, car_classID, car_location \
                = YOLOv8_car.infer([frame], flag='car')

            for j in range(len(car_boxes)):
                box = car_boxes[j]
                img = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                img_raw, use_time_armor, armor_boxes, armor_scores, armor_classID, armor_location \
                    = YOLOv8_armor.infer([img], flag='armor')

                armor_post_process(armor_location, box)
                if armor_location is None and self.previous_boxes is not None:
                    armor_location = self.match_boxes(box, self.previous_boxes)

                locations.append(armor_location)
                array_locations = np.concatenate(locations, axis=0)

                for i in range(len(armor_location)):
                    cv2.rectangle(image_raw[0], (int(armor_location[i][10]), int(armor_location[i][11])),
                                  (int(armor_location[i][12]+armor_location[i][10]), int(armor_location[i][13]+armor_location[i][11])), (0, 255, 0), 2)
                    cv2.putText(image_raw[0], "{}".format(categories[int(armor_location[i][9])]),
                                (int(armor_location[i][10]), int(armor_location[i][11])), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 0), 2)

            if len(locations) > 0:
                locations.pop()
                self.previous_boxes = array_locations.reshape(-1, 14)
                return True, array_locations.reshape(-1, 14), image_raw[0]
            else:
                return False, None, frame

    def match_boxes(self, current_boxes, previous_boxes, threshold=0.3):
        again_armor_location = []
        current_armor_box = [0, 0, 0, 0]
        current_armor_box[0] = current_boxes[0] + 1 / 3 * (current_boxes[2] - current_boxes[0])
        current_armor_box[1] = current_boxes[1] + 3 / 5 * (current_boxes[3] - current_boxes[1])
        current_armor_box[2] = current_boxes[2] - 1 / 3 * (current_boxes[2] - current_boxes[0])
        current_armor_box[3] = current_boxes[3] - 1 / 5 * (current_boxes[3] - current_boxes[1])

        previous_boxes = previous_boxes.reshape(-1, 14)
        for i in range(len(previous_boxes)):
            if self.calculate_iou(current_armor_box, previous_boxes[i][10:]) > threshold:
                again_armor_location = previous_boxes[i]

        if len(again_armor_location) == 0:
            return None
        else:
            return again_armor_location

    @staticmethod
    def calculate_iou(box1, box2):
        inter_x1 = max(box1[0], box2[0])
        inter_y1 = max(box1[1], box2[1])
        inter_x2 = min(box1[2], box2[2])
        inter_y2 = min(box1[3], box2[3])
        inter_area = max(0, inter_x2 - inter_x1 + 1) * max(0, inter_y2 - inter_y1 + 1)

        box1_area = (box1[2] - box1[0] + 1) * (box1[3] - box1[1] + 1)
        box2_area = (box2[2] - box2[0] + 1) * (box2[3] - box2[1] + 1)

        iou = inter_area / float(box1_area + box2_area - inter_area)
        return iou


class WarmUpThread(threading.Thread):
    def __init__(self, yolov8_wrapper):
        threading.Thread.__init__(self)
        self.yolov8_wrapper = yolov8_wrapper

    def run(self):
        batch_image_raw, use_time, *a = self.yolov8_wrapper.infer(self.yolov8_wrapper.get_raw_image_zeros())
        print('warm_up->{}, time->{:.2f}ms'.format(batch_image_raw[0].shape, use_time * 1000))


class InferVideoThread(threading.Thread):
    def __init__(self, YoLov8_wrapper_car, YoLov8_wrapper_armor, video_path):
        threading.Thread.__init__(self)
        self.yolov8_wrapper_car = YoLov8_wrapper_car
        self.yolov8_wrapper_armor = YoLov8_wrapper_armor
        self.video_path = video_path

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))

        out = cv2.VideoWriter('output/output_video.mp4', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10,
                              (frame_width, frame_height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            image_raw, use_time_car, car_boxes, car_scores, car_classid, car_location \
                = self.yolov8_wrapper_car.infer([frame])
            for j in range(len(car_boxes)):
                box = car_boxes[j]
                img = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                img_raw, use_time_armor, armor_boxes, armor_scores, armor_classid, armor_location \
                    = self.yolov8_wrapper_armor.infer([img])

                armor_post_process(armor_location, box)

                print('input->{}, time->{:.2f}ms, fps->{}'.format(frame.shape, (use_time_car + use_time_armor) * 1000,
                                                                  1 / (use_time_car + use_time_armor)))
                for i in range(len(armor_boxes)):
                    cv2.rectangle(image_raw[0], (int(armor_location[i][10]), int(armor_location[i][11])),
                                  (int(armor_location[i][12]), int(armor_location[i][13])), (0, 255, 0), 2)
            out.write(image_raw[0])

        cap.release()
        out.release()


class InferCameraThread(threading.Thread):
    def __init__(self, yolov8_wrapper_car, yolov8_wrapper_armor, frame):
        threading.Thread.__init__(self)
        self.yolov8_wrapper_car = yolov8_wrapper_car
        self.yolov8_wrapper_armor = yolov8_wrapper_armor
        self.frame = frame

    def run(self):
        image_raw, use_time_car, car_boxes, car_scores, car_classid, car_location \
            = self.yolov8_wrapper_car.infer([self.frame])

        for j in range(len(car_boxes)):
            box = car_boxes[j]
            img = self.frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
            img_raw, use_time_armor, armor_boxes, armor_scores, armor_classid, armor_location \
                = self.yolov8_wrapper_armor.infer([img])

            armor_post_process(armor_location, box)
            armor_locations.append(armor_location)

            for i in range(len(armor_boxes)):
                cv2.rectangle(self.frame, (int(armor_location[i][10]), int(armor_location[i][11])),
                                (int(armor_location[i][12]), int(armor_location[i][13])), (0, 255, 0), 2)
                cv2.putText(self.frame, "{}".format(categories[int(armor_location[i][9])]),
                            (int(armor_location[i][10]), int(armor_location[i][11])), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0), 2)
