CAMERA_CONFIG_DIR = 'Camera_config'
CACHE_CONFIG_SAVE_DIR = 'save_stuff'
preview_location = [(100, 100)]
PC_STORE_DIR = '/home/zk/new_HDU/save_stuff/points'
LIDAR_TOPIC_NAME = '/livox/lidar'
LOCATION_SAVE_DIR = 'save_stuff/position'

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
            'r_rt': [],  # r0 right_top
            'r_lt': [],  # r0 left_top
            'b_rt': [],  # b0 right_top
            'b_lt': []  # b0 right_top
        },
    'game':  # 按照官方手册填入
        {
            # 'red_base': [1.760, -15. + 7.539, 0.200 + 0.920],  # red base
            # 'blue_outpost': [16.776, -15. + 12.565, 1.760],  # blue outpost
            # 'red_outpost': [11.176, -15. + 2.435, 1.760],  # red outpost
            # 'blue_base': [26.162, -15. + 7.539, 0.200 + 0.920],  # blue base
            # 'r_rt': [8.805, -5.728 - 0.660, 0.120 + 0.495],  # r0 right_top
            # 'r_lt': [8.805, -5.728, 0.120 + 0.495],  # r0 left_top
            # 'b_rt': [19.200, -9.272 + 0.660, 0.120 + 0.495],  # b0 right_top
            # 'b_lt': [19.200, -9.272, 0.120 + 0.495]  # b0 left_top
            'red_base': [1.760, 7.539, 0.200 + 0.920],  # red base
            'blue_outpost': [16.776, 12.565, 1.760],  # blue outpost
            'red_outpost': [11.176, 2.435, 1.760],  # red outpost
            'blue_base': [26.162, 7.539, 0.200 + 0.920],  # blue base
            'r_rt': [8.805, -5.728 - 0.660 + 15., 0.120 + 0.495],  # r0 right_top
            'r_lt': [8.805, -5.728 + 15., 0.120 + 0.495],  # r0 left_top
            'b_rt': [19.200, -9.272 + 0.660 + 15., 0.120 + 0.495],  # b0 right_top
            'b_lt': [19.200, -9.272 + 15., 0.120 + 0.495]  # b0 left_top
        }
}
