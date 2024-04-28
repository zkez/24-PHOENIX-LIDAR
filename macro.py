enemy: int = 1  # 0:red, 1:blue
home_test = False
debug = True

CAMERA_CONFIG_DIR = 'Camera_config'
CACHE_CONFIG_SAVE_DIR = 'save_stuff'
preview_location = [(100, 100)]
PC_STORE_DIR = 'save_stuff/points'
LIDAR_TOPIC_NAME = '/livox/lidar'
LOCATION_SAVE_DIR = 'save_stuff/position'

armor_list = ['R1', 'R2', 'R3', 'R4', 'R5', 'B1', 'B2', 'B3', 'B4', 'B5']  # 雷达站实际考虑的各个装甲板类
categories = ["B1", "B2", "B3", "B4", "B5", "B7", "R1", "R2", "R3", "R4", "R5", "R7"]  # 雷达站实际考虑的各个装甲板类(全国赛)
img_sz = [3088, 2064]
armor_locations = []

VIDEO_SAVE_DIR = 'save_stuff/video'
MAP_PATH = 'save_stuff/output_map.jpg'

PLUGIN_LIBRARY = 'detect/infer/libmyplugins.so'
car_engine_file_path = "detect/infer/yolov8m_car.engine"
armor_engine_file_path = "detect/infer/yolov8s_armor.engine"
CONF_THRESH_CAR = 0.5
CONF_THRESH_ARMOR = 0.01
IOU_THRESHOLD = 0.4
ArmorFlag = False

model_imgsz = (640, 640)
map_size = [960, 536]

position_choice = 'y'
SaveFlag = False

color2enemy = {"red": 0, "blue": 1}
enemy2color = ['red', 'blue']

location_targets = {
    # enemy:red
    # red_base -> blue_outpost -> b_rt -> b_lt
    # enemy:blue
    # blue_base -> red_outpost -> r_rt -> r_lt
    'home_test':  # 家里测试，填自定义类似于赛场目标的空间位置
        {
            'red_base': [],
            'blue_outpost': [],
            'red_outpost': [],
            'blue_base': [],
            'r_rt': [1.196, 6.376, 0.598],
            'r_lt': [0.598, 6.376, 0.598],
            'b_rt': [],
            'b_lt': []
        },
    'game':  # 按照官方手册填入-24赛季相机位姿估计标记点（！规则手册中世界坐标系原点在红方左上角，而雷达通信使用坐标系原点在红方左下角！）
        {
            # 前哨战顶部 基地飞镖引导灯
            'red_base': [1.760, 7.500, 1.043],  # red base
            'blue_outpost': [16.816, -2.421 + 15.0, 1.586],  # blue outpost
            'red_outpost': [11.184, -12.579 + 15.0, 1.586],  # red outpost
            'blue_base': [26.240, 7.500, 1.043],  # blue base
            # 狗洞附近的定位标签的左上角和右上角
            'r_rt': [8.670, -5.715 - 0.400 + 15., 0.420],  # r0 right_top
            'r_lt': [8.670, -5.715 + 15., 0.420],  # r0 left_top
            'b_rt': [19.330, -9.285 + 0.400 + 15., 0.420],  # b0 right_top
            'b_lt': [19.330, -9.285 + 15., 0.420]  # b0 left_top
        }
}

receiver_id = [[103, 104, 105], [3, 4, 5]]

position_alarm = {
    'enemy_is_red': [
        ([1], [[4.73, 15.], [8.94, 15.], [6.636, 15-4.1], [4.73, 15-4.06]], 1),
        ([1, 3, 4, 5], [[12.12, 13.763], [12.893, 13.224], [10.072, 9.265], [9.132, 9.5]], 2),
        ([1, 3, 4, 5], [[5.76, 0.797], [12.487, 0.797], [12.487, 0.05], [5.76, 0.05]], 3)

    ],
    'enemy_is_blue': [
        ([101], [[28-4.73, 0], [28-8.94, 0], [28-6.636, 4.1], [28-4.73, 4.06]], 1),
        ([101, 103, 104, 105], [[17.928, 5.735], [18.868, 5.5], [15.88, 1.237], [15.107, 1.776]], 2),
        ([101, 103, 104, 105], [[15.513, 14.817], [22.24, 14.95], [22.24, 14.203], [15.513, 14.07]], 3)
    ]
}

