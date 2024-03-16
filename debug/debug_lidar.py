import cv2
import traceback
import numpy as np

from camera.camera import CameraThread
from common.common import read_yaml
from Calibration.location import locate_pick
from lidar.Lidar import Radar


if __name__ == '__main__':
    # 测试demo 同时也是非常好的测距测试脚本

    _, K_0, C_0, E_0, imgsz = read_yaml(0)

    ra = Radar(K_0, C_0, E_0, imgsz=imgsz)
    Radar.start()

    cv2.namedWindow("out", cv2.WINDOW_NORMAL)  # 显示雷达深度图
    cv2.resizeWindow("out", 1280, 960)
    cv2.namedWindow("img", cv2.WINDOW_NORMAL)  # 显示实际图片
    cv2.resizeWindow("img", 1280, 960)

    cap = CameraThread(0)
    try:
        flag, frame = cap.read()

        # 选定一个ROI区域来测深度
        cv2.imshow("img", frame)
        rect = cv2.selectROI("img", frame, False)

        _, rvec, tvec = locate_pick(cap, 0, 0)  # 用四点手动标定估计位姿

        # 创建transform matrix
        T = np.eye(4)
        T[:3, :3] = cv2.Rodrigues(rvec)[0]
        T[:3, 3] = tvec.reshape(-1)
        T = np.linalg.inv(T)

        key = cv2.waitKey(1)

        while(flag and key != ord('q') & 0xFF):

            depth = ra.read()  # 获得深度图

            # 分别在实际相机图和深度图上画ROI框来对照
            cv2.rectangle(frame, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (0, 255, 0), 3)

            cv2.rectangle(depth, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), 255, 3)

            cv2.imshow("out", depth)
            cv2.imshow("img", frame)

            key = cv2.waitKey(1)
            if key == ord('r') & 0xFF:
                # 重选区域
                rect = cv2.selectROI("img", frame, False)

            if key == ord('s') & 0xFF:
                # 显示世界坐标系和相机坐标系坐标和深度，以对测距效果进行粗略测试
                cp = ra.detect_depth([rect]).reshape(-1)

                cp = (T @ np.concatenate(
                    [np.concatenate([cp[:2], np.ones(1)], axis=0) * cp[2], np.ones(1)], axis=0))[:3]

                cp_eye = (np.eye(4) @ np.concatenate(
                    [np.concatenate([cp[:2], np.ones(1)], axis=0) * cp[2], np.ones(1)], axis=0))[:3]

                print(f"target position is ({cp[0]:0.3f},{cp[1]:0.3f},{cp[2]:0.3f}) and distance is {np.linalg.norm(cp):0.3f}")

                print(f"origin target position is ({cp_eye[0]:0.3f},{cp_eye[1]:0.3f},{cp_eye[2]:0.3f}) and distance is {np.linalg.norm(cp_eye):0.3f}")

            flag, frame = cap.read()
    except:
        traceback.print_exc()
    Radar.stop()
    cap.release()
    cv2.destroyAllWindows()
