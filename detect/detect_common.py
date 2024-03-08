import cv2
import random
import numpy as np


def plot_one_box(x, img, color=None, label=None, line_thickness=None):
    """
    description: Plots one bounding box on image img,
                 this function comes from YoLov8 project.
    param:
        x:      a box likes [x1,y1,x2,y2]
        img:    a opencv image object
        color:  color to draw rectangle, such as (0,255,0)
        label:  str
        line_thickness: int
    return:
        no return
    """
    tl = (
            line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1
    )
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)
        cv2.putText(
            img,
            label,
            (c1[0], c1[1] - 2),
            0,
            tl / 3,
            [225, 255, 255],
            thickness=tf,
            lineType=cv2.LINE_AA,
        )


def xyxy_xyxy(y):
    """
    description:    Convert nx4 boxes from [x1, y1, x2, y2] to [x3, y3, x4, y4, x5, y5, x6, y6]
                    where xy3=top-left, xy4=bottom-left, xy5=bottom-right, xy6=top-right(Counterclockwise)
    param:
        origin_h:   height of original image
        origin_w:   width of original image
        y:          A boxes numpy, each row is a box [x1, y1, x2, y2]
    return:
        z:          A boxes numpy, each row is a box [x3, y3, x4, y4, x5, y5, x6, y6]
    """
    z = np.zeros((y.shape[0], 8))
    z[:, 0] = y[:, 0]
    z[:, 1] = y[:, 1]
    z[:, 2] = y[:, 0]
    z[:, 3] = y[:, 3]
    z[:, 4] = y[:, 2]
    z[:, 5] = y[:, 3]
    z[:, 6] = y[:, 2]
    z[:, 7] = y[:, 1]

    return z


def armor_post_process(armor_location, car_box):
    armor_location[:, 0] += car_box[0]
    armor_location[:, 1] += car_box[1]
    armor_location[:, 2] += car_box[0]
    armor_location[:, 3] += car_box[1]
    armor_location[:, 4] += car_box[0]
    armor_location[:, 5] += car_box[1]
    armor_location[:, 6] += car_box[0]
    armor_location[:, 7] += car_box[1]

    armor_location[:, 10] += car_box[0]
    armor_location[:, 11] += car_box[1]
    armor_location[:, 12] += car_box[0]
    armor_location[:, 13] += car_box[1]
