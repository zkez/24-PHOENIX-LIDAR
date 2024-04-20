import numpy as np
import cv2
from camera.camera import CameraThread
import yaml


def calibrate_camera(rows, cols, grid, max_images=20):
    size = (cols, rows)

    objp = np.zeros((rows * cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * grid

    obj_points = []
    img_points = []

    cap = CameraThread(0)

    if not cap.is_open():
        print("Error: Failed to open camera.")
        exit()

    image_count = 0
    frame_count = 0

    while image_count < max_images:
        ret, frame = cap.read()

        if not ret:
            print("Error: Failed to capture frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        ret, corners = cv2.findChessboardCorners(gray, size, None)

        if ret:
            if frame_count % 10 == 0:  # 每隔10帧取一个点
                obj_points.append(objp)

                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                img_points.append(corners2)

                frame = cv2.drawChessboardCorners(frame, size, corners2, ret)
                image_count += 1

        frame_count += 1

        cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Frame', 1280, 960)
        cv2.imshow('Frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(obj_points) > 0:
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray.shape[::-1], None, None)
        if ret:
            print("相机内参数矩阵:")
            print(mtx)
            print("\n畸变系数:")
            print(dist)

            # 计算重投影误差
            total_error = 0
            for i in range(len(obj_points)):
                img_points_reprojected, _ = cv2.projectPoints(obj_points[i], rvecs[i], tvecs[i], mtx, dist)
                error = cv2.norm(img_points[i], img_points_reprojected, cv2.NORM_L2) / len(img_points_reprojected)
                total_error += error
            mean_error = total_error / len(obj_points)
            print("\n重投影误差:", mean_error)

            np.savez("camera_calibration.npz", mtx=mtx, dist=dist)
        else:
            print("Error: Failed to calibrate camera.")
    else:
        print("Error: No images provided for calibration.")


def read_camera_params_from_yaml(yaml_file):
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
        camera_matrix = np.array(data['K_0']).reshape((3, 3))  # 将相机内参转换为 3x3 的矩阵
        dist_coeffs = np.array(data['C_0'])  # 畸变参数是一个一维数组
    return camera_matrix, dist_coeffs


def estimate_distance_with_manual_points(image, camera_matrix, dist_coeffs, known_width, known_height):
    image_copy = image.copy()

    image_points = []

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            image_points.append((x, y))
            cv2.circle(image_copy, (x, y), 5, (0, 255, 0), -1)
            cv2.imshow('Image', image_copy)

            if len(image_points) == 5:
                cv2.destroyAllWindows()
                return

    cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
    cv2.imshow('Image', image)
    cv2.setMouseCallback('Image', mouse_callback)
    cv2.waitKey(0)  # 等待键盘输入
    cv2.destroyAllWindows()

    pixel_distances = []
    for i in range(len(image_points)):
        for j in range(i + 1, len(image_points)):
            pixel_distance = np.linalg.norm(np.array(image_points[i]) - np.array(image_points[j]))
            pixel_distances.append(pixel_distance)
    distance = np.mean(pixel_distances)

    distance_actual = (known_width * camera_matrix[0, 0]) / distance
    return distance_actual


def test():
    camera_matrix, dist_coeffs = read_camera_params_from_yaml('../Camera_config/camera0.yaml')

    known_width = 0.65
    known_height = 0.65

    cap = CameraThread(0)
    ret, frame = cap.read()
    if ret:
        distance_actual = estimate_distance_with_manual_points(frame, camera_matrix, dist_coeffs, known_width, known_height)
        print("物体到相机的实际距离为:", distance_actual, "米")


if __name__ == "__main__":
    calibrate_camera(8, 12, 20, max_images=800)
