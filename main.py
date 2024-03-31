import time
import ctypes
import serial
import traceback
import threading
from process.radarprocess import RadarProcess
from macro import position_choice, PLUGIN_LIBRARY
from referee_system.static_uart import StaticUART


if __name__ == '__main__':
    try:
        ctypes.CDLL(PLUGIN_LIBRARY)
        # ser = serial.Serial('/dev/ttyUSB0', 115200, 8, 'N', 1, timeout=0.01)
        main_process = RadarProcess()
        choice = position_choice if isinstance(position_choice, str) else input(
            'Get new position? Y/y for yes, N/n for no\n')
        # uart_thread = threading.Thread(target=StaticUART.advanced_loop, args=(ser, ), name='uart')
        # alarm_thread = threading.Thread(target=StaticUART.alarm_loop, args=(ser, ), name='alarm')
        # uart_thread.start()
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

