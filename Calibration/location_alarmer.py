import numpy as np
from macro import armor_list


class LocationAlarmer:
    _ids = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 0, 6: 10, 7: 11, 8: 12, 9: 13, 10: 14, 11: 9}  # 装甲板编号到标准编号

    # param
    _pred_time = 10  # 预测几次
    _pred_radio = 0.2  # 预测速度比例
    _lp = True  # 是否位置预测
    _z_a = True  # 是否进行z轴突变调整
    _z_thre = 0.2  # z轴突变调整阈值
    _ground_thre = 100  # 地面阈值，我们最后调到了100就是没用这个阈值，看情况调
    _using_l1 = True  # 不用均值，若两个都有预测只用右相机预测值

    def __init__(self, whether_2_cam, whether_debug, z_a=True):
        self._two_camera = whether_2_cam
        if self._two_camera:
            self._z_cache = [None, None]
            self._camera_position = [None, None]
            self._T = [None, None]
        else:
            self._camera_position = [None]
            self._T = [None]
        self._z_a = z_a
        self._debug = whether_debug
        self._location = {}

    def push_T(self, T, camera_position, camera_type):
        """
        位姿信息
        :param T:相机到世界转移矩阵
        :param camera_position:相机在世界坐标系坐标
        :param camera_type:相机编号，若为单相机填0
        """
        if camera_type > 0 and not self._two_camera:
            return

        self._camera_position[camera_type] = camera_position.copy()
        self._T[camera_type] = T.copy()

    def refine_cood(self, locations, radar):
        rls = []
        if isinstance(locations, np.ndarray):
            l = radar.detect_depth(locations[:, 10:])
            # 这个mask可以找到l中不是nan值的行
            mask = np.logical_not(np.any(np.isnan(l), axis=1))
            rls.append(np.concatenate([locations[mask].reshape(-1, 14)[:, 9].reshape(-1, 1),
                                       l[mask].reshape(-1, 3)], axis=1))
        else:
            rls.append(None)

        l1 = None
        radar_xyz = rls[0]
        pred_loc = []
        for armor in self._ids.keys():
            if isinstance(radar_xyz, np.ndarray):
                mask = radar_xyz[:, 0] == armor
                # 这里有可能因为误识别或者其他原因，没有识别到车辆，但是识别到了诸如前哨站的东西
                # 也会让l1变成None
                if mask.any():
                    l1 = radar_xyz[mask].reshape(-1)
                    l1[1:] = (self._T[0] @ np.concatenate(
                        [np.concatenate([l1[1:3], np.ones(1)], axis=0) * l1[3], np.ones(1)], axis=0))[:3]
                    pred_loc.append(l1)

        return pred_loc

    def _adjust_z_one_armor(self, l, camera_type):
        """
        z轴突变调整，仅针对一个装甲板
        :param l:(cls+x+y+z) 一个id的位置
        :param camera_type:相机编号
        """
        if isinstance(self._z_cache[camera_type], np.ndarray):
            mask = np.array(self._z_cache[camera_type][:, 0] == l[0])  # 检查上一帧缓存z坐标中有没有对应id
            if mask.any():
                z_0 = self._z_cache[camera_type][mask][:, 1]
                if z_0 < self._ground_thre:  # only former is on ground do adjust
                    z = l[3]
                    if z - z_0 > self._z_thre:  # only adjust the step from down to up
                        # 以下计算过程详见技术报告公式
                        ori = l[1:].copy()
                        line = l[1:] - self._camera_position[camera_type]
                        radio = (z_0 - self._camera_position[camera_type][2]) / line[2]
                        new_line = radio * line
                        l[1:] = new_line + self._camera_position[camera_type]
                        if self._debug:
                            # z轴变换debug输出
                            print('{0} from'.format(armor_list[(self._ids[int(l[0])]) - 1]), ori, 'to', l[1:])
