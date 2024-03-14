import yaml
import numpy as np


def read_yaml(camera_type):
    """
    读取相机标定参数,包含外参，内参，以及关于雷达的外参
    :param camera_type: 相机编号
    :return: 读取成功失败标志位，相机内参，畸变系数，和雷达外参，相机图像大小
    """
    # yaml_path = "{0}/camera{1}.yaml".format(CAMERA_CONFIG_DIR, camera_type)
    yaml_path = '/home/zk/zk/Camera_config/camera{0}.yaml'.format(camera_type)
    try:
        with open(yaml_path, 'rb') as f:
            res = yaml.load(f, Loader=yaml.FullLoader)
            K_0 = np.float32(res["K_0"]).reshape(3, 3)
            C_0 = np.float32(res["C_0"])
            E_0 = np.float32(res["E_0"]).reshape(4, 4)
            imgsize = tuple(res['ImageSize'])

        return True, K_0, C_0, E_0, imgsize
    except Exception as e:
        print("[ERROR] {0}".format(e))
        return False, None, None, None, None


