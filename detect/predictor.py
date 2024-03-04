from network.RM_4_points_yolov5 import detect
import torch
import numpy as np
import cv2
from macro import debug


class Predictor:
    # hard code part
    view_img = True
    fp16 = True
    conf_thres = 0.5
    iou_thres = 0.5

    def __init__(self, weight, model_imgsz=(640, 640)):
        self.select_device()
        model = detect.load_model(weight, device=self.device)
        self.model = model.half() if self.fp16 else model
        self.img_sz = model_imgsz

    def infer(self, frame):
        im0 = frame.copy()
        pred, img_tensor = self.run(frame)
        location, show_im = self.post_processing(pred, img_tensor, im0)
        if location is None:
            return False, location, frame
        else:
            return True, np.float32(location), show_im

    def infer_bias(self, src_location, bias: tuple):
        bias_x, bias_y = bias[0], bias[1]
        src_location[:, 0] += bias_x
        src_location[:, 1] += bias_y
        src_location[:, 2] += bias_x
        src_location[:, 3] += bias_y
        src_location[:, 4] += bias_x
        src_location[:, 5] += bias_y
        src_location[:, 6] += bias_x
        src_location[:, 7] += bias_y

        src_location[:, 10] += bias_x
        src_location[:, 11] += bias_y
        src_location[:, 12] += bias_x
        src_location[:, 13] += bias_y

    def cated_infer(self, frame):
        frame_height, frame_width = frame.shape[0], frame.shape[1]
        first_frame = frame[0:frame_height, 0:frame_width]
        cated_frame = [first_frame]
        pred, img_tensor = self.com_run(first_frame)
        return self.com_post_process(pred, img_tensor, cated_frame)

    def com_run(self, first_frame):
        first_frame = detect.letterbox(first_frame, self.img_sz, auto=False)[0]

        img_tensor = self.com_shift(first_frame)
        pred = self.model(img_tensor)[0]
        pred = detect.non_max_suppression_face(pred, self.conf_thres, self.iou_thres)
        return pred, img_tensor

    def com_post_process(self, pred, img_tensor, im0):
        total_locations = []
        # 我们要首先保证pred是有长度的
        location, show_im = self.post_processing([pred[0]], img_tensor[0][None], im0[0])
        if not location is None:
            total_locations.append(location)

        total_im = show_im

        if len(total_locations):
            total_locations = torch.cat(total_locations, dim=0)
            return True, np.float32(total_locations), total_im
        else:
            return False, None, total_im

    # def composition_infer(self, frame):
    #     total_locations = []
    #     frame_height, frame_width = frame.shape[0], frame.shape[1]
    #
    #     # 第一个裁剪的图案
    #     first_frame = frame[0:frame_height // 2, 0:frame_width // 2]
    #     pred, img_tensor = self.run(first_frame)
    #     show_im_1 = first_frame
    #     if len(pred[0]):
    #         location_1, show_im_1 = self.post_processing(pred, img_tensor, first_frame)
    #         total_locations.append(location_1)
    #
    #     # 第二个裁剪的图案
    #     second_frame = frame[0:frame_height // 2, frame_width // 2:frame_width]
    #     pred, img_tensor = self.run(second_frame)
    #     show_im_2 = second_frame
    #     if len(pred[0]):
    #         location_2, show_im_2 = self.post_processing(pred, img_tensor, second_frame)
    #         self.infer_bias(location_2, (frame_width // 2, 0))
    #         total_locations.append(location_2)
    #
    #     # 第三个裁剪的图案
    #     third_frame = frame[frame_height // 2:frame_height, 0:frame_width // 2]
    #     pred, img_tensor = self.run(third_frame)
    #     show_im_3 = third_frame
    #     if len(pred[0]):
    #         location_3, show_im_3 = self.post_processing(pred, img_tensor, third_frame)
    #         self.infer_bias(location_3, (0, frame_height // 2))
    #         total_locations.append(location_3)
    #
    #     # 第四个裁剪的图案
    #     forth_frame = frame[frame_height // 2:frame_height, frame_width // 2:frame_width]
    #     pred, img_tensor = self.run(forth_frame)
    #     show_im_4 = forth_frame
    #     if len(pred[0]):
    #         location_4, show_im_4 = self.post_processing(pred, img_tensor, forth_frame)
    #         self.infer_bias(location_4, (frame_width // 2, frame_height // 2))
    #         total_locations.append(location_4)
    #
    #     if len(total_locations):
    #         total_locations = torch.cat(total_locations, dim=0)
    #         one_two = np.concatenate([show_im_1, show_im_2], axis=1)
    #         three_four = np.concatenate([show_im_3, show_im_4], axis=1)
    #         total_im = np.concatenate([one_two, three_four], axis=0)
    #         return True, np.float32(total_locations), total_im
    #     else:
    #         return False, None, frame

    def run(self, frame):
        img = detect.letterbox(frame, new_shape=self.img_sz, auto=False)[0]
        img_tensor = self.shift_2_torch_tensor(img)
        pred = self.model(img_tensor)[0]
        pred = detect.non_max_suppression_face(pred, self.conf_thres, self.iou_thres)
        return pred, img_tensor

    def post_processing(self, pred, img_tensor, im0):

        det = pred[0]  # 因为这里，在同一时刻，我们只会有一张图片被输入到模型当中， len(pred)==1
        if len(det):
            det[:, :4] = detect.scale_coords(img_tensor.shape[2:], det[:, :4], im0.shape).round()

            det[:, 5:13] = detect.scale_coords_landmarks(img_tensor.shape[2:], det[:, 5:13], im0.shape).round()

            cat_landmark = det[:, 5:13]
            cat_conf = det[:, 4].reshape(-1, 1)
            cat_class = det[:, 13].reshape(-1, 1)
            cat_xyxy = det[:, :4]
            new_det = torch.cat([cat_landmark, cat_conf, cat_class, cat_xyxy], dim=1)

            if debug:
                for j in range(det.size()[0]):
                    xyxy = det[j, :4].view(-1).tolist()
                    conf = det[j, 4].cpu().numpy()
                    landmarks = det[j, 5:13].view(-1).tolist()
                    class_num = det[j, 13].cpu().numpy()
                    im0 = detect.show_results(im0, xyxy, conf, landmarks, class_num)

        else:
            new_det = None
        # 如果检测到目标，就输出检测的结果，如果没有，就输出原图像。
        return new_det.cpu() if new_det != None else None, im0

    def com_shift(self, first_frame):
        first_frame = self.shift_2_torch_tensor(first_frame)

        return torch.cat([first_frame])

    def shift_2_torch_tensor(self, im):
        im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        im_input = np.ascontiguousarray(im)  # contiguous

        im_input = torch.from_numpy(im_input).to(self.device)
        im_input = im_input.half() if self.fp16 else im_input.float()  # uint8 to fp16/32
        im_input /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im_input.shape) == 3:
            im_input = im_input[None]  # expand for batch dim
        return im_input

    def select_device(self):
        if torch.cuda.is_available():
            self.device = f'cuda:0'
            return
        self.device = f'cpu'
