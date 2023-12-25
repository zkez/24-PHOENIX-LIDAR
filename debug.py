from datetime import datetime


class Debugger(object):
    # hard coding here
    loc_output_interval = 1
    specific_class = None

    def __init__(self, panel):
        self.calculator = 0
        self.start_time = datetime.now()
        self.panel = panel

    def pred_loc_debugger(self, pred_loc):
        # 在debug的时候我们只想看某一行或者某一类的信息
        class2row = 0
        if isinstance(self.specific_class, int):
            for i, row in enumerate(pred_loc):
                if int(row[0]) == self.specific_class: class2row = i
            pred_loc = pred_loc[class2row]
        else:
            pred_loc = pred_loc[0]

        if self.calculator == 0:
            self.start_time = datetime.now()
            self.distance_sum_x = 0
            self.distance_sum_y = 0
            self.distance_sum_z = 0

        self.distance_sum_x += pred_loc[1]
        self.distance_sum_y += pred_loc[2]
        self.distance_sum_z += pred_loc[3]
        self.calculator += 1
        if (datetime.now() - self.start_time).total_seconds() >= self.loc_output_interval:
            self.panel.update_text(
                f'The x: {self.distance_sum_x / self.calculator}, y: {self.distance_sum_y / self.calculator}, z: {self.distance_sum_z / self.calculator}')
            # 使用完毕后要及时归零
            self.calculator = 0
        else:
            pass

