import numpy as np
from macro import armor_list


class LocationAlarmer:
    _ids = {1: 6, 2: 7, 3: 8, 4: 9, 5: 10, 8: 1, 9: 2, 10: 3, 11: 4, 12: 5}  # 装甲板编号到标准编号

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

    def two_camera_merge_update(self, locations, extra_locations, radar):
        if self._two_camera:
            for i in range(1, 11):
                self._location[str(i)] = [0, 0]
            rls = []
            ex_rls = []
            for location, e_location, ra in zip(locations, extra_locations, radar):
                # 针对每一个相机产生的结果
                # 对于用神经网络直接预测出的装甲板，若不为None
                if isinstance(location, np.ndarray):
                    l = ra.detect_depth(location[:, 11:])  # (N,x0+y0+z)  z maybe nan
                    # nan滤除
                    mask = np.logical_not(np.any(np.isnan(l), axis=1))
                    # 格式为 (N,cls+x0+y0+z)
                    rls.append(np.concatenate([location[mask].reshape(-1, 15)[:, 9].reshape(-1, 1),
                                               l[mask].reshape(-1, 3)], axis=1))
                else:
                    rls.append(None)

                # 同上，不过这里是对IoU预测的装甲板做解析
                # e_location的shape是：（cls, x, y, w, h）
                if isinstance(e_location, np.ndarray):
                    e_l = ra.detect_depth(e_location[:, 1:])
                    # nan滤除
                    mask = np.logical_not(np.any(np.isnan(e_l), axis=1))
                    ex_rls.append(np.concatenate([e_location[mask].reshape(-1, 5)[:, 0].reshape(-1, 1),
                                                  e_l[mask].reshape(-1, 3)], axis=1))
                else:
                    ex_rls.append(None)

            pred_loc = []
            if self._z_a:  # 两个相机z缓存，存储列表
                pred_1 = []
                pred_2 = []
            for armor in self._ids.keys():
                l1 = None  # 对于特定id，第一个相机基于直接神经网络预测装甲板计算出的位置
                l2 = None  # 对于特定id，第二个相机基于直接神经网络预测装甲板计算出的位置
                el1 = None  # 对于特定id，第一个相机基于IoU预测装甲板计算出的位置
                el2 = None  # 对于特定id，第二个相机基于IoU预测装甲板计算出的位置
                al1 = None  # 对于特定id，第一个相机预测出的位置（直接神经网络与IoU最多有一个预测，不可能两个同时）
                al2 = None  # 对于特定id，第二个相机预测出的位置（直接神经网络与IoU最多有一个预测，不可能两个同时）
                if isinstance(rls[0], np.ndarray):
                    mask = rls[0][:, 0] == armor
                    if mask.any():
                        l1 = rls[0][mask].reshape(-1)
                        # 坐标换算为世界坐标
                        l1[1:] = (self._T[0] @ np.concatenate(
                            [np.concatenate([l1[1:3], np.ones(1)], axis=0) * l1[3], np.ones(1)], axis=0))[:3]
                        # z坐标解算
                        if self._z_a:
                            self._adjust_z_one_armor(l1, 0)
                        al1 = l1
                if isinstance(rls[1], np.ndarray):
                    mask = rls[1][:, 0] == armor
                    if mask.any():
                        l2 = rls[1][mask].reshape(-1)
                        l2[1:] = (self._T[1] @ np.concatenate(
                            [np.concatenate([l2[1:3], np.ones(1)], axis=0) * l2[3], np.ones(1)], axis=0))[:3]
                        if self._z_a:
                            self._adjust_z_one_armor(l2, 1)
                        al2 = l2
                if isinstance(ex_rls[0], np.ndarray):
                    mask = ex_rls[0][:, 0] == armor
                    if mask.any():
                        el1 = ex_rls[0][mask].reshape(-1)
                        el1[1:] = (self._T[0] @ np.concatenate(
                            [np.concatenate([el1[1:3], np.ones(1)], axis=0) * el1[3], np.ones(1)], axis=0))[:3]
                        if self._z_a:
                            self._adjust_z_one_armor(el1, 0)
                        al1 = el1
                if isinstance(ex_rls[1], np.ndarray):
                    mask = ex_rls[1][:, 0] == armor
                    if mask.any():
                        el2 = ex_rls[1][mask].reshape(-1)
                        el2[1:] = (self._T[1] @ np.concatenate(
                            [np.concatenate([el2[1:3], np.ones(1)], axis=0) * el2[3], np.ones(1)], axis=0))[:3]
                        if self._z_a:
                            self._adjust_z_one_armor(el2, 1)
                        al2 = el2
                # z cache
                if self._z_a:
                    if isinstance(al1, np.ndarray):
                        pred_1.append(al1[[0, 3]])  # cache cls+z
                    if isinstance(al2, np.ndarray):
                        pred_2.append(al2[[0, 3]])
                # perform merging
                # 参考技术报告，有一些不同，代码里是先进行了z轴调整，不过差不多
                armor_pred_loc = None
                if isinstance(l1, np.ndarray):
                    armor_pred_loc = l1.reshape(-1)
                if isinstance(l2, np.ndarray):
                    if isinstance(armor_pred_loc, np.ndarray):
                        if not self._using_l1:
                            armor_pred_loc = (armor_pred_loc + l2.reshape(-1)) / 2  # 若不用l1，取平均值
                    else:
                        armor_pred_loc = l2.reshape(-1)
                # if not appear in either l1 or l2, then check extra
                if not isinstance(armor_pred_loc, np.ndarray):
                    if isinstance(el1, np.ndarray):
                        armor_pred_loc = el1.reshape(-1)
                    if isinstance(el2, np.ndarray):
                        if isinstance(armor_pred_loc, np.ndarray):
                            if not self._using_l1:
                                armor_pred_loc = (armor_pred_loc + el2.reshape(-1)) / 2
                        else:
                            armor_pred_loc = el2.reshape(-1)
                if isinstance(armor_pred_loc, np.ndarray):
                    pred_loc.append(armor_pred_loc)
            # z cache
            if self._z_a:
                if len(pred_1):
                    self._z_cache[0] = np.stack(pred_1, axis=0)
                else:
                    self._z_cache[0] = None
                if len(pred_2):
                    self._z_cache[1] = np.stack(pred_2, axis=0)
                else:
                    self._z_cache[1] = None

            # 这里保留一个对于裁判系统的接口
            judge_loc = {}
            if len(pred_loc):
                pred_loc = np.stack(pred_loc, axis=0)
                # 我们可能需要进行坐标的变换
                # pred_loc[:, 2] = self._real_size[1] + pred_loc[:, 2]
                for i, armor in enumerate(pred_loc[:, 0]):
                    self._location[str(self._ids[int(armor)])] = pred_loc[i, 1:3].tolist()  # 类成员只存(x,y)信息
                    judge_loc[str(self._ids[int(armor)])] = pred_loc[i, 1:].tolist()  # 发送包存三维信息

            if self._debug:
                # 位置debug输出
                for armor, loc in judge_loc.items():
                    print("{0} in ({1:.3f},{2:.3f},{3:.3f})".format(armor_list[int(armor) - 1], *loc))

        else:
            print('[ERROR] This update function only supports two_camera case, using update instead.')

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
                # 这里有可能因为误识别或者其他原因，没有识别到车辆，但是识别到了诸如前哨站的东西，
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

