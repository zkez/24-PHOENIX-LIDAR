import os
import open3d as o3d
import numpy as np
import pcl


def pcd_to_nparray(pcd_file):
    pcd = o3d.io.read_point_cloud(pcd_file)
    points = np.asarray(pcd.points)
    return points


if __name__ == "__main__":
    pcd_folder = "/home/zk/livox/src/livox_camera_lidar_calibration/data/pcdFiles/"
    output_folder = "../save_stuff/points/"

    for filename in os.listdir(pcd_folder):
        if filename.endswith(".pcd"):
            pcd_file = os.path.join(pcd_folder, filename)
            output_file = os.path.join(output_folder, filename.split('.')[0] + '.npy')
            points = pcd_to_nparray(pcd_file)
            np.save(output_file, points)
