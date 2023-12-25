import serial
import binascii  # 在BIN(二进制)和ASCII之间转换
import struct  # 将数据作为完整的结构传输，用struct模块进行处理
from binascii import *
from crcmod import *
import time
import offical_Judge_Handler
import numpy as np
import copy
import threading
import random

from macro import home_test, position_alarm, enemy, receiver_id


def is_inside(box: np.ndarray, point: np.ndarray):
    """
    判断点是否在凸四边形中
    :param box:为凸四边形的四点 shape is (4,2)
    :param point:为需判断的是否在内的点 shape is (2,)
    """
    assert box.shape == (4, 2)
    assert point.shape == (2,)
    AM = point - box[0]
    AB = box[1] - box[0]
    BM = point - box[1]
    BC = box[2] - box[1]
    CM = point - box[2]
    CD = box[3] - box[2]
    DM = point - box[3]
    DA = box[0] - box[3]
    a = np.cross(AM, AB)
    b = np.cross(BM, BC)
    c = np.cross(CM, CD)
    d = np.cross(DM, DA)
    return a >= 0 and b >= 0 and c >= 0 and d >= 0 or \
        a <= 0 and b <= 0 and c <= 0 and d <= 0


class Static_UART:
    if home_test:
        home_width = 9.3
        home_height = 4.65
    else:
        home_width = 28
        home_height = 15
    real_width = 28
    real_height = 15
    specific_color = {0: [1, 2, 3, 4, 5, 7], 1: [101, 102, 103, 104, 105, 107]}
    _lock = threading.Lock()
    stop_flag = False
    robot_location = None
    alarm_flag = 0
    alarm_location = None
    alarm_enemy = ['enemy_is_red', 'enemy_is_blue'][enemy]
    send_id = 9 if enemy else 109
    data_id = 0x020F
    receiver = receiver_id[enemy]

    @staticmethod
    def create_SOF(datalen):
        """
        创建一个帧头（SOF），其中包含了长度信息、校验和等数据，以便用于数据传输
        """
        buffer = [0]
        buffer = buffer * 5
        buffer[0] = 0xa5
        buffer[1] = datalen
        buffer[2] = 0
        buffer[3] = 0
        buffer[4] = offical_Judge_Handler.myGet_CRC8_Check_Sum(id(buffer), 4, 0xff)  # 校验值

        return bytes(bytearray(buffer))

    @staticmethod
    def push_loc(location):
        """
        将传入的位置信息 location 深复制到类变量 Static_UART.robot_location 中
        """
        # Static_UART._lock.acquire()
        # 如果不适用深复制（或许浅复制也行），那么多进程时可能反而会更慢
        Static_UART.robot_location = copy.deepcopy(location)
        # Static_UART._lock.release()

    @staticmethod
    def push_alarm(location):
        """
        将传入的位置信息 location 深复制到类变量 Static_UART.alarm_location  中
        """
        Static_UART.alarm_location = copy.deepcopy(location)
        Static_UART.alarm_flag = 1

    @staticmethod
    def radar_between_car(data: list, datalenth: int, receiver_id, ser):
        """
        将指定的数据通过串口 ser 传输给雷达设备
        """
        SOF = Static_UART.create_SOF(datalenth + 6)  # datalength 指的是我要发的数据长度，前面还有6位的字节漂移
        CMDID = (b'\x01' b'\x03')
        data = bytes(bytearray(data))  # 将列表转换为字节流
        dataid_sender_receiver = struct.pack('<3H', Static_UART.data_id, Static_UART.send_id, receiver_id)
        data_sum = SOF + CMDID + dataid_sender_receiver + data
        decodeData = binascii.b2a_hex(data_sum).decode('utf-8')  # 将 data_sum 转换为十六进制表示，并通过 decode('utf-8') 将其解码为字符串
        data_last, hexer = offical_Judge_Handler.crc16Add(decodeData)
        # data_last: 附加了 CRC-16 校验码后的完整数据
        # hexer: 附加了 CRC-16 校验码的完整数据的二进制表示
        ser.write(hexer)

    @staticmethod
    def random_receiver(whether_random):
        """
        根据 whether_random 参数来决定是否随机选择接收者
        """
        if whether_random:
            return random.choice(Static_UART.receiver)
        else:
            return Static_UART.receiver[0]

    @staticmethod
    def radar_map(ID, X, Y):
        Z = 1
        try:
            SOF = Static_UART.create_SOF(14)
            CMDID = (b'\x05' b'\x03')
            data = struct.pack("<1H3f", ID, X, Y, Z)  # 按照格式 "<1H3f"打包为二进制数据
            data1 = SOF + CMDID + data
            decodeData = binascii.b2a_hex(data1).decode('utf-8')  # 转换为16进制表示，又将其解码成字符串
            _, hexer = offical_Judge_Handler.crc16Add(decodeData)
            # hexer: 附加了 CRC-16 校验码的完整数据的二进制表示
            return hexer

        except Exception as e:
            print("serial write data has ERROR: \033[0m", e)

    @staticmethod
    def xy_check(x: float, y: float, ):
        """
        将传入坐标（x,y）转换为相对于真实场地的坐标值x,y
        """
        new_x = x * Static_UART.real_width / Static_UART.home_width
        new_y = y * Static_UART.real_height / Static_UART.home_height

        return new_x, new_y

    @staticmethod
    def alarm_xy_check(numpy_xy):
        """
        将传入坐标（numpy）转换为相对于真实场地的坐标值(numpy)
        """
        new_x = numpy_xy[0] * Static_UART.real_width / Static_UART.home_width
        new_y = numpy_xy[1] * Static_UART.real_height / Static_UART.home_height
        return np.array([new_x, new_y])

    @staticmethod
    def Robot_Data_Transmit_Map(ser):
        """
        通过串口传输位置信息，判断是否报警
        """
        try:
            for row in Static_UART.robot_location:
                target_id = int(row[0])
                if target_id in Static_UART.specific_color[enemy]:
                    x, y = float(row[1]), float(row[2])
                    # check_xy 之后获得 真实场地的xy
                    x, y = Static_UART.xy_check(x, y)
                    print(x, y)
                    hexer = Static_UART.radar_map(target_id, x, y)
                    ser.write(hexer)  # 将生成的数据 hexer（包含id,坐标）通过串口 ser 进行传输
                    for alarm in position_alarm[Static_UART.alarm_enemy]:
                        # 检查当前目标ID是否在报警相关数据中，并调用 is_inside() 函数判断机器人的位置是否在报警区域内
                        if target_id in alarm[0] and is_inside(np.array(alarm[1]),
                                                               Static_UART.alarm_xy_check(row[1:3])):
                            data = Static_UART.handle_id(target_id) + Static_UART.handle_id(alarm[-1])
                            print(data)
                            # print(Static_UART.random_receiver(False if home_test else True))
                            Static_UART.radar_between_car(data, datalenth=4,
                                                          receiver_id=Static_UART.random_receiver(
                                                              104 if home_test else True), ser=ser)
                time.sleep(0.1)
        except:
            # print(Static_UART.robot_location)
            time.sleep(0.1)

    @staticmethod
    def handle_id(target_id):
        if target_id > 100:
            target_id -= 100
        if target_id == 1:
            target_id = [1, 0]
        if target_id == 2:
            target_id = [2, 0]
        if target_id == 3:
            target_id = [2, 1]
        if target_id == 4:
            target_id = [2, 2]
        if target_id == 5:
            target_id = [3, 2]

        return target_id

    @staticmethod
    def advanced_loop(ser):
        while 1:
            Static_UART.Robot_Data_Transmit_Map(ser)
            if Static_UART.stop_flag:
                break


if __name__ == "__main__":
    import threading
    import copy

    ser = serial.Serial('/dev/ttyUSB0', 115200, 8, 'N', 1, timeout=0.01)
    pred_loc1 = np.array([
        [104, 2.8346, 0.06]])
    alarm_thread = threading.Thread(target=Static_UART.advanced_loop, args=(ser,))
    alarm_thread.start()

    # counter = 0
    # whole_pred = [pred_loc1, pred_loc2]
    # Static_UART.push_loc(pred_loc1)

    while 1:
        Static_UART.push_loc(pred_loc1)
        # Static_UART.push_alarm(pred_loc1)
        # Static_UART.Robot_map_debug(ser)
        # Static_UART.radar_between_car([2, 3, 1, 0], datalenth=4, receiver_id=104, ser=ser)

