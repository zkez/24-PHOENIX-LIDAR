import serial


def main(port, baudrate, bytesize, stopbits, parity):
    ser = serial.Serial(port, baudrate, bytesize, parity=parity, stopbits=stopbits, timeout=1)
    if ser.isOpen():
        print("串口已打开")
    strength = 0
    while 1:
        data = ser.read(9)
        if data[0] == 0x59 and data[1] == 0x59:
            dist = (data[2] + data[3] * 256)
            strength = data[4] + data[5] * 256

        if strength >= 100:
            # 计算信号强度值

            # 计算温度值（单位：℃）
            temp = (data[6] + data[7] * 256) / 8.0 - 256
            # 打印距离、信号强度和温度值
            print('Distance: %.2f cm, Strength: %d, Temperature: %.2f ℃' % (dist, strength, temp))
        else:
            print('Strength is out of range')

    ser.close()


if __name__ == "__main__":
    port = '/dev/ttyUSB0'  # 串口号
    baudrate = 115200  # 波特率
    bytesize = 8  # 数据位
    stopbits = 1  # 停止位
    parity = serial.PARITY_NONE  # 奇偶校验

    main(port, baudrate, bytesize, stopbits, parity)
