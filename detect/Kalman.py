import cv2
import numpy as np


class KalmanTracker:
    def __init__(self, init_rect):
        self.kf = cv2.KalmanFilter(7, 4, 0)
        self.measurement = np.zeros((4, 1), np.float32)
        self.m_history = []
        self.m_time_since_update = 0
        self.m_hits = 0
        self.m_hit_streak = 0
        self.m_age = 0
        self.init_kf(init_rect)

    def init_kf(self, state_mat):
        state_num = 7
        measure_num = 4
        self.kf.transitionMatrix = np.array([[1, 0, 0, 0, 1, 0, 0],
                                             [0, 1, 0, 0, 0, 1, 0],
                                             [0, 0, 1, 0, 0, 0, 1],
                                             [0, 0, 0, 1, 0, 0, 0],
                                             [0, 0, 0, 0, 1, 0, 0],
                                             [0, 0, 0, 0, 0, 1, 0],
                                             [0, 0, 0, 0, 0, 0, 1]], np.float32)

        self.kf.measurementMatrix = np.array([[1, 0, 0, 0, 0, 0, 0],
                                              [0, 1, 0, 0, 0, 0, 0],
                                              [0, 0, 1, 0, 0, 0, 0],
                                              [0, 0, 0, 1, 0, 0, 0]], np.float32)

        self.kf.processNoiseCov = np.identity(state_num, np.float32) * 1e-1
        self.kf.measurementNoiseCov = np.identity(measure_num, np.float32) * 3e-3
        self.kf.errorCovPost = np.identity(state_num, np.float32)

        # 初始化状态向量 [cx,cy,s,r]
        cx = state_mat.x + state_mat.width / 2
        cy = state_mat.y + state_mat.height / 2
        s = state_mat.area()
        r = state_mat.width / state_mat.height

        self.kf.statePost = np.array([[cx], [cy], [s], [r], [0], [0], [0]], np.float32)

    def predict(self):
        p = self.kf.predict()
        self.m_age += 1

        if self.m_time_since_update > 0 and self.m_hits < sort_param.MIN_HITS:
            self.m_hit_streak = 0
        self.m_time_since_update += 1

        predict_box = self.get_rect_xysr(p[0, 0], p[1, 0], p[2, 0], p[3, 0])
        self.m_history.append(predict_box)

    def update(self, state_mat):
        self.m_time_since_update = 0
        self.m_history.clear()
        self.m_hits += 1
        self.m_hit_streak += 1

        # measurement
        self.measurement[0, 0] = state_mat.x + state_mat.width / 2
        self.measurement[1, 0] = state_mat.y + state_mat.height / 2
        self.measurement[2, 0] = state_mat.area()
        self.measurement[3, 0] = state_mat.width / state_mat.height

        # update
        self.kf.correct(self.measurement)

    def pre_update(self, state_mat):
        self.m_history.clear()
        self.m_hits += 1
        self.m_hit_streak += 1

        # measurement
        self.measurement[0, 0] = state_mat.x + state_mat.width / 2
        self.measurement[1, 0] = state_mat.y + state_mat.height / 2
        self.measurement[2, 0] = state_mat.area()
        self.measurement[3, 0] = state_mat.width / state_mat.height

        # update
        self.kf.correct(self.measurement)

    def get_state(self):
        s = self.kf.statePost
        return self.get_rect_xysr(s[0, 0], s[1, 0], s[2, 0], s[3, 0])

    def get_rect_xysr(self, cx, cy, s, r):
        w = np.sqrt(s * r)
        h = s / w
        x = max(0, cx - w / 2)
        y = max(0, cy - h / 2)

        return [x, y, w, h]

    def getHistory(self):
        return self.m_history[-1]

    def getSinceTime(self):
        return self.m_time_since_update

    def getHits(self):
        return self.m_hit_streak



