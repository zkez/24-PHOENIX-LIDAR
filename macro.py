enemy: int = 1  # 0:red, 1:blue
home_test = False
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

receiver_id = [[103,104,105],
[3,4,5]
]

position_alarm = {
    'enemy_is_red':[
        ([1], [[4.73, 15.],[8.94, 15.],[6.636, 15-4.1],[4.73, 15-4.06]], 1),
        ([1, 3, 4, 5], [[12.12, 13.763],[12.893, 13.224], [10.072, 9.265], [9.132, 9.5]], 2),
        ([1,3,4,5], [[5.76, 0.797], [12.487, 0.797], [12.487, 0.05], [5.76, 0.05]], 3)

    ],
    'enemy_is_blue':[
        ([101], [[28-4.73,0],[28-8.94,0],[28-6.636,4.1],[28-4.73,4.06]], 1),
        ([101, 103, 104, 105], [[17.928, 5.735],[18.868, 5.5],[15.88, 1.237],[15.107, 1.776]], 2),
        ([101, 103, 104, 105], [[15.513, 14.817],[22.24, 14.95],[22.24, 14.203],[15.513, 14.07]], 3)
    ]
}

