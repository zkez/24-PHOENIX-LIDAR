import time
import ctypes
import serial
import traceback
import threading
import pexpect
from process.radarprocess import RadarProcess
from macro import position_choice, PLUGIN_LIBRARY
from referee_system.static_uart import StaticUART, ReadUART


if __name__ == '__main__':
    try:
        ctypes.CDLL(PLUGIN_LIBRARY)

        password = '123'
        ch = pexpect.spawn('sudo chmod 777 /dev/ttyUSB0')
        ch.sendline(password)
        ser = serial.Serial('/dev/ttyUSB0', 115200, 8, 'N', 1, timeout=0.01)

        main_process = RadarProcess()
        choice = position_choice if isinstance(position_choice, str) else input(
            'Get new position? Y/y for yes, N/n for no\n')

        uart_thread = threading.Thread(target=StaticUART.advanced_loop, args=(ser, ), name='uart')
        read_thread = threading.Thread(target=ReadUART.read, args=(ser, ), name='read')
        # alarm_thread = threading.Thread(target=StaticUART.alarm_loop, args=(ser, ), name='alarm')
        uart_thread.start()
        read_thread.start()
        # alarm_thread.start()

        if choice in ['Y', 'y']:
            # main_process.panel.set_cam()
            main_process.get_position_new()
        elif choice in ['N', 'n']:
            main_process.get_position_using_last()
        while 1:
            t1 = time.time()
            main_process.spin_once()
            fps = 1 / (time.time() - t1)
            main_process.panel.update_text(f'The fps is:{fps}', True)

            if main_process.stop_flag:
                main_process.stop_and_release()
                break
    except:
        traceback.print_exc()
