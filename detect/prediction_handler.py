from macro import color2enemy
import numpy as np
import cv2


def plot(results, frame, only_car=True):
    """
    画车辆预测框

    :param results: list, every item is (predicted_class,conf_score,bounding box(format:x0,y0,x1,y1))
    :param frame: the image to plot on it
    :param only_car:ignore the watcher(guard) and base class

    :return: 当输入有仅有颜色预测框时，返回该类预测框的bbox和其他对应id的bbox整合
    """
    color_bbox = []
    # plot on the raw frame
    for cat, score, bound in results:
        if cat in "watcher base" and only_car:
            continue
        if '0' in cat:
            # 通过颜色检测出的bounding box
            color_bbox.append(np.array([color2enemy[cat.split('_')[1]], *bound]))
        plot_one_box(cat, bound, frame)
    if len(color_bbox):
        return np.stack(color_bbox, axis=0)
    else:
        return None


def plot_one_box(cat, b, img):
    """
    绘制边界框
    cat: 对象类别
    b: 边界框坐标 (x0,y0,x1,y1)
    img: 被绘制的图片
    """
    if cat.split('_')[0] == "car":
        if len(cat.split('_')) == 3:  # car_{armor_color}_{armor_id}
            cat = cat.split('_')
            color = cat[1]
            armor = cat[2]
        else:
            color = "C"
            armor = '0'
    else:
        # 只预测出颜色情况
        color = cat  # ‘R0’ or 'B0'
        armor = '0'
    cv2.rectangle(img, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (0, 255, 0), 2)
    cv2.putText(img, color[0].upper() + armor, (int(b[0]), int(b[1])), cv2.FONT_HERSHEY_SIMPLEX,
                3 * img.shape[1] // 3088, (255, 0, 255), 2)


def armor_plot(location, img):
    """
    画四点装甲板框

    :param location: np.ndarray (N,armor_points + data) 即后一个维度前八位必须是按顺时针顺序的装甲板四点坐标
    """
    if isinstance(location, np.ndarray):
        for gl in location:
            l = gl[:8].reshape(4, 2).astype(np.int)
            for i in range(len(l)):
                cv2.line(img, tuple(l[i]), tuple(l[(i + 1) % len(l)]), (0, 255, 0), 2)


class Bbox_Handler:
    real_width = 28
    real_height = 15

    def __init__(self):
        pass

    def refine_extra_box(self, armor, bbox):
        # 改变装甲板外框
        pass

    def push_T_and_inver(self, rvec, tvec):
        '''
        接收旋转向量（rvec）和平移向量（tvec），将它们保存到类的成员变量中，并生成一个4x4的变换矩阵T
        该方法还返回T与原点(0,0,0,1)相乘后的结果的前三个元素，即变换后的原点坐标
        '''
        self._rvec = rvec
        self._tvec = tvec
        # 基于位姿做反投影，初始化scene_region预警区域字典
        T = np.eye(4)
        # 这里将旋转向量转换成为旋转矩阵
        T[:3, :3] = cv2.Rodrigues(rvec)[0]
        T[:3, 3] = tvec.reshape(-1)
        T = np.linalg.inv(T)

        return T, (T @ (np.array([0, 0, 0, 1])))[:3]

    def update(self, frame, results, armors):
        # 更新边界框和装甲板位置信息，并将它们绘制在图像上
        self._every_scene = frame
        self._color_bbox = plot(results, self._every_scene)  # color bbox (x1,y1,x2,y2)
        # 画装甲板
        armor_plot(armors, self._every_scene)
        if self._scene_init:
            self._plot_region(self._every_scene)

    def draw_on_map(self, pred_loc, map):
        # 在地图上绘制预测位置，并添加对应的标签
        radius = 9
        thickness = -1
        text_thick = 4
        if isinstance(pred_loc, np.ndarray):
            for loc in pred_loc:
                xy = tuple(loc[1:3])
                xy = self.xy_check(xy, map)
                text = str(int(loc[0]))
                cv2.circle(map, xy, radius, (0, 215, 255), thickness)
                text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX,
                                               1, text_thick)
                text_x = int(xy[0] - text_size[0] / 2)
                text_y = int(xy[1] + text_size[1] / 2)
                cv2.putText(map, text, (text_x - 2 * radius, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255),
                            text_thick)
        # 如果pred_loc为None，那么只返回地图就好了
        return map

    def xy_check(self, xy, map):
        '''
        xy: 需要被画图的点的xy坐标, 其中y采用的是“下原点”模式, 但是opencv画图要用“上原点模式”
        map: 需要被画在的图片上
        这个函数主要就是检测xy是否超过了图片的界限
        如果超过了就想办法让程序不报错
        '''
        x, y = xy
        y = self.real_height - y
        width = map.shape[1]
        height = map.shape[0]
        new_x = x * width / self.real_width
        new_y = y * height / self.real_height
        if new_x < 0:
            new_x = 0
        if new_x > width:
            new_x = width
        if new_y < 0:
            new_y = 0
        if new_y > height:
            new_y = height
        return (int(new_x), int(new_y))




