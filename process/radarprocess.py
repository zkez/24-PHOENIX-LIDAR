import glob
import numpy as np
from camera.camera import CameraThread
from camera.common import read_yaml
from lidar.Lidar import Radar
from detect.prediction_handler import Bbox_Handler
from Calibration.location_alarmer import LocationAlarmer
from detect.predictor import Predictor
import time
import cv2
from macro import MAP_PATH, enemy, home_test, map_size, img_sz, NET_PATH, model_imgsz\
    , VIDEO_SAVE_DIR, debug
from Calibration.location import locate_record, locate_pick
from detect.common import armor_filter
from panel import Dashboard
from debug import Debugger
from referee_system.static_uart import Static_UART


class radar_process:
    def __init__(self):
        self.panel = Dashboard(img_sz, map_size, self)
        self.map = cv2.imread(MAP_PATH)
        self.cap = CameraThread(0)
        self.stop_flag = False
        self._cap1 = self.cap
        if self.cap.is_open():
            self.panel.update_text("[INFO] Camera {0} Starting.".format(0))
        else:
            self.panel.update_text("[INFO] Camera {0} Failed, try to open.".format(0), is_warning=True)

        _, K_0, C_0, E_0, imgsz = read_yaml(0)
        save_order = self.increment_path(VIDEO_SAVE_DIR)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.vi_saver = cv2.VideoWriter(f'{VIDEO_SAVE_DIR}/{save_order}.mp4', fourcc, 6, imgsz)
        self.resume_flag = 0

        # 初始化处理边界框和地图的类
        self.bbox_handler = Bbox_Handler()
        self._scene = [self.bbox_handler]
        self.location_alarmor = LocationAlarmer(False, True)

        self.net = Predictor(NET_PATH, model_imgsz)
        # weights/detail_best.pt

        self.position_flag = False
        self._position_flag = np.array([self.position_flag])

        self.radar = Radar(K_0, C_0, E_0, queue_size=20, imgsz=img_sz)
        Radar.start()
        self.radar_init = False

        self.debugger = Debugger(self.panel)
        self.uart_ids = {1: 101, 2: 102, 3: 103, 4: 104, 5: 105, 0: 107, 10: 1, 11: 2, 12: 3, 13: 4, 14: 5, 9: 7}

    def get_position_using_last(self):
        """
        使用保存的位姿
        """
        if self._position_flag.all():  # 全部位姿已估计完成
            self.panel.update_text("feedback", "camera pose already init")
            return
        if not self._position_flag[0]:
            flag, rvec1, tvec1 = locate_record(0, enemy)
            if flag:
                self._position_flag[0] = True
                # myshow.set_text("feedback", "Camera 0 pose init")
                self.panel.update_text("[INFO] Camera 0 pose init")
                # 将位姿存入反投影预警类
                T, cp = self._scene[0].push_T_and_inver(rvec1, tvec1)
                # 将位姿存入位置预警类
                self.location_alarmor.push_T(T, cp, 0)
            else:
                # myshow.set_text("feedback", "Camera 0 pose init error")
                self.panel.update_text("[INFO] Camera 0 pose init meet error", is_warning=True)

    def get_position_new(self):
        """
        using huge range object to get position, which is simple but perfect
        """
        if self._position_flag.all():
            print("feedback", "camera pose already init")
            return

        if not self._position_flag[0]:
            flag = False
            if self._cap1.is_open():
                flag, rvec1, tvec1 = locate_pick(self._cap1, enemy, 0, home_size=home_test, panel=self.panel)
            if flag:
                self._position_flag[0] = True
                self.panel.update_text("[INFO] Camera 0 pose init")
                locate_record(0, enemy, True, rvec1, tvec1)  # 保存
                T, cp = self._scene[0].push_T_and_inver(rvec1, tvec1)
                self.location_alarmor.push_T(T, cp, 0)
            else:
                self.panel.update_text("Camera 0 pose init meet error", is_warning=True)
                self.panel.update_text("[INFO] Camera 0 pose init error", is_warning=True)

    def increment_path(self, up_dir):
        if up_dir[-1] != '/':
            up_dir = up_dir + '/'
        file_name_list = glob.glob(f'{up_dir}*.mp4')
        start_num = 1
        if len(file_name_list) != 0:
            for i in file_name_list:
                current_num = int(i.split('/')[-1].split('.')[0])
                if current_num > start_num:
                    start_num = current_num
        else:
            return start_num
        return start_num + 1

    def update_postion(self):
        flag = False
        if self._cap1.is_open():
            flag, rvec1, tvec1 = locate_pick(self._cap1, enemy, 0, home_size=home_test, panel=self.panel)
        if flag:
            print("[INFO] Camera 0 pose UPDATED")
            locate_record(0, enemy, True, rvec1, tvec1)  # 保存
            T, cp = self._scene[0].push_T_and_inver(rvec1, tvec1)
            self.location_alarmor.push_T(T, cp, 0)
        else:
            print("[WARNING] Camera 0 pose updated error")

    def change_id_2_uart(self, pred_loc):
        # 这里必须要确保pred_loc不是None或者之类的异常变量
        for row in pred_loc:
            row[0] = self.uart_ids[row[0]] if row[0] in self.uart_ids.keys() else row[0]

    def spin_once(self):
        if self.radar.check_radar_init():
            self.radar_init = True
        # 2.6226043701171875e-05
        # 对打开失败的相机，尝试再次打开
        if not self.cap.is_open():
            self.cap.open()
        flag, frame = self.cap.read()
        # self.panel.update_cam_pic(frame)
        if not flag:
            self.panel.update_text('The camera could NOT be opened')
            time.sleep(0.05)
            return

        ret, locations, show_im = self.net.cated_infer(frame)
        locations = armor_filter(locations)
        self.panel.update_cam_pic(show_im)

        pred_loc = None

        if ret:

            pred_loc = self.location_alarmor.refine_cood(locations, self.radar)

            if len(pred_loc):
                pred_loc = np.array(pred_loc, dtype=np.float32)
                if len(pred_loc.shape) == 1: pred_loc = pred_loc[None]

            if isinstance(pred_loc, np.ndarray):
                self.debugger.pred_loc_debugger(pred_loc)
                self.change_id_2_uart(pred_loc)
                Static_UART.push_loc(pred_loc)
                Static_UART.push_alarm(pred_loc)

        if debug:
            self.panel.update_map_mood(self.bbox_handler.draw_on_map(pred_loc, self.map.copy()))

        if self.resume_flag:
            self.vi_saver.write(frame)

    def stop_and_release(self):
        self.cap.release()
        # self.uart_proce.terminate()
        Static_UART.stop_flag = True
        self.vi_saver.release()
        self.radar.__del__()

