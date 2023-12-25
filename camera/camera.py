import cv2
import numpy as np
from datetime import datetime

from camera import mvsdk
from macro import CACHE_CONFIG_SAVE_DIR, preview_location


class CameraThread:
    def __init__(self, camera_type, load_path: str = None, strict_mode=False):
        self._camera_type = camera_type
        self._date = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        self._open = False
        self._cap = None
        self._load_path = load_path
        self.strict_mode = strict_mode
        self.open()

    def open(self):
        if not self._open:
            self._open, self.cap = self.open_cam(self._camera_type, self._date)

    def is_open(self):
        """
        check the camera opening state
        """
        return self._open

    def read(self):
        if self._open:
            r, frame = self.cap.read()
            if not r:
                self.cap.release()  # release the failed camera
                self._open = False
            return r, frame
        else:
            return False, None

    def open_cam(self, camera_type, date):
        cap = None
        init_flag = False
        try:
            cap = HTCamera(camera_type, date, self.strict_mode)
            r, frame = cap.read()  # read once to examine whether the cap is working
            assert r, "[INFO] Camera not init"  # 读取失败则报错
            r, frame = cap.read()
            # 建立预览窗口
            cv2.namedWindow("preview of {0}".format(camera_type),
                            cv2.WINDOW_NORMAL)
            cv2.resizeWindow("preview of {0}".format(camera_type), 840, 640)
            cv2.setWindowProperty("preview of {0}".format(camera_type),
                                  cv2.WND_PROP_TOPMOST, 1)
            win_loc = 0
            # 移动至合适位置
            cv2.moveWindow("preview of {0}".format(camera_type),
                           *preview_location[win_loc])
            cv2.imshow("preview of {0}".format(camera_type), frame)
            key = cv2.waitKey(0)
            cv2.destroyWindow("preview of {0}".format(camera_type))
            # 按其他键则不调参使用默认参数，按t键则进入调参窗口，可调曝光和模拟增益
            if key == ord('t') & 0xFF:
                tune_exposure(cap, date, high_reso=False)

            init_flag = True
        except Exception as e:
            print("[ERROR] {0}".format(e))
        return init_flag, cap

    def release(self):
        if self._open:
            self.cap.release()
            self._open = False

    def __del__(self):
        if self._open:
            self.cap.release()
            self._open = False


class HTCamera:
    def __init__(self, camera_type=0, path=None, strict_mode=False):
        """
        相机驱动类
        :param camera_type:相机编号
        :param is_init: 相机是否已经启动过一次，若是则使用path所指向的参数文件
        :param path: 初次启动保存的参数文件路径名称（无需后缀，实际使用时即为创建时间）
        """
        DevList = mvsdk.CameraEnumerateDevice()
        camera_match_list = []
        if strict_mode:
            # 枚举相机
            # 得到存在相机序列号
            existing_camera_name = [dev.GetSn() for dev in DevList]

            if not camera_match_list[camera_type] in existing_camera_name:
                # 所求相机不存在
                self.hCamera = -1
                return

            camera_no = existing_camera_name.index(
                camera_match_list[camera_type])  # 所求相机在枚举列表中编号
            DevInfo = DevList[camera_no]
            print("{} {}".format(DevInfo.GetFriendlyName(), DevInfo.GetPortType()))
            print(DevInfo)

            self.camera_type = camera_type
        else:
            DevInfo = DevList[0]
            self.camera_type = camera_type

        # 打开相机
        try:
            self.hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            self.hCamera = -1
            print("CameraInit Failed({}): {}".format(e.error_code, e.message))
            return

        # 获取相机特性描述
        cap = mvsdk.CameraGetCapability(self.hCamera)

        # 判断是黑白相机还是彩色相机
        monoCamera = (cap.sIspCapacity.bMonoSensor != 0)

        # 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(self.hCamera,
                                        mvsdk.CAMERA_MEDIA_TYPE_MONO8)
        else:
            mvsdk.CameraSetIspOutFormat(self.hCamera,
                                        mvsdk.CAMERA_MEDIA_TYPE_BGR8)

        # 相机模式切换成连续采集
        mvsdk.CameraSetTriggerMode(self.hCamera, 0)

        mvsdk.CameraSetAeState(self.hCamera, 0)

        print(
            f"[INFO] camera exposure time {mvsdk.CameraGetExposureTime(self.hCamera) / 1000:0.03f}ms"
        )
        print(
            f"[INFO] camera gain {mvsdk.CameraGetAnalogGain(self.hCamera):0.03f}"
        )

        # 让SDK内部取图线程开始工作
        mvsdk.CameraPlay(self.hCamera)

        # 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (
            1 if monoCamera else 3)

        # 分配RGB buffer，用来存放ISP输出的图像
        # 备注：从相机传输到PC端的是RAW数据，在PC端通过软件ISP转为RGB数据（如果是黑白相机就不需要转换格式，但是ISP还有其它处理，所以也需要分配这个buffer）
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

    def read(self):
        if self.hCamera == -1:
            return False, None
        try:
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
            mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer,
                                     FrameHead)
            mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

            # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
            # 把pFrameBuffer转换成opencv的图像格式以进行后续算法处理
            frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(
                self.pFrameBuffer)
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth,
                                   1 if FrameHead.uiMediaType
                                        == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
            return True, frame
        except mvsdk.CameraException as e:
            print(e)
            return False, None

    def setExposureTime(self, ex=30):
        if self.hCamera == -1:
            return
        mvsdk.CameraSetExposureTime(self.hCamera, ex)

    def setGain(self, gain):
        if self.hCamera == -1:
            return
        mvsdk.CameraSetAnalogGain(self.hCamera, gain)

    def saveParam(self, path):
        if self.hCamera == -1:
            return
        param_path = "{0}/camera_{1}_of_{2}.Config".format(
            CACHE_CONFIG_SAVE_DIR, self.camera_type, path)
        mvsdk.CameraSaveParameterToFile(self.hCamera, param_path)
        return param_path

    def NoautoEx(self):
        """
        设置不自动曝光
        """
        if self.hCamera == -1:
            return
        mvsdk.CameraSetAeState(self.hCamera, 0)

    def getExposureTime(self):
        if self.hCamera == -1:
            return -1
        return int(mvsdk.CameraGetExposureTime(self.hCamera) / 1000)

    def getAnalogGain(self):
        if self.hCamera == -1:
            return -1
        return int(mvsdk.CameraGetAnalogGain(self.hCamera))

    def release(self):
        if self.hCamera == -1:
            return
        # 关闭相机
        mvsdk.CameraUnInit(self.hCamera)
        # 释放帧缓存
        mvsdk.CameraAlignFree(self.pFrameBuffer)


def tune_exposure(cap: HTCamera, date, high_reso=False):
    """
    :param cap: camera target
    :param high_reso: 采用微秒/毫秒为单位调整曝光时间
    """
    cv2.namedWindow("exposure press q to exit", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("exposure press q to exit", 1280, 960)
    cv2.moveWindow("exposure press q to exit", 300, 300)
    cv2.setWindowProperty("exposure press q to exit", cv2.WND_PROP_TOPMOST, 1)
    if high_reso:
        cv2.createTrackbar("ex", "exposure press q to exit", 0, 1,
                           lambda x: None)
        cv2.setTrackbarMax("ex", "exposure press q to exit", 30000)
        cv2.setTrackbarMin("ex", "exposure press q to exit", 0)
        cv2.setTrackbarPos("ex", "exposure press q to exit",
                           int(cap.getExposureTime() * 1000))
        # 模拟增益区间为0到256
        cv2.createTrackbar("g1", "exposure press q to exit", 0, 1,
                           lambda x: None)
        cv2.setTrackbarMax("g1", "exposure press q to exit", 256)
        cv2.setTrackbarMin("g1", "exposure press q to exit", 0)
        cv2.setTrackbarPos("g1", "exposure press q to exit",
                           int(cap.getAnalogGain()))
    else:
        cv2.createTrackbar("ex", "exposure press q to exit", 0, 1,
                           lambda x: None)
        cv2.setTrackbarMax("ex", "exposure press q to exit", 120)
        cv2.setTrackbarMin("ex", "exposure press q to exit", 0)
        cv2.setTrackbarPos("ex", "exposure press q to exit",
                           int(cap.getExposureTime()))
        cv2.createTrackbar("g1", "exposure press q to exit", 0, 1,
                           lambda x: None)
        cv2.setTrackbarMax("g1", "exposure press q to exit", 256)
        cv2.setTrackbarMin("g1", "exposure press q to exit", 0)
        cv2.setTrackbarPos("g1", "exposure press q to exit",
                           int(cap.getAnalogGain()))

    flag, frame = cap.read()

    while (flag):
        if high_reso:
            cap.setExposureTime(
                cv2.getTrackbarPos("ex", "exposure press q to exit"))
        else:
            cap.setExposureTime(
                cv2.getTrackbarPos("ex", "exposure press q to exit") * 1000)
        cap.setGain(cv2.getTrackbarPos("g1", "exposure press q to exit"))

        cv2.imshow("exposure press q to exit", frame)
        flag, frame = cap.read()
        key = cv2.waitKey(1)
        if key == ord('q') & 0xFF:
            break
        if key == ord('s') & 0xFF:
            cap.saveParam(date)
            break

    ex = cv2.getTrackbarPos("ex", "exposure press q to exit")
    g1 = cv2.getTrackbarPos("g1", "exposure press q to exit")
    if high_reso:
        ex = ex / 1000
    print(f"finish set exposure time {ex:.03f}ms")
    print(f"finish set analog gain {g1}")
    cv2.destroyWindow("exposure press q to exit")



