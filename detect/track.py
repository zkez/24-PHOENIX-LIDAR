from typing import List
from scipy.optimize import linear_sum_assignment
from Kalman import KalmanTracker

MAX_AGE = 4
MIN_HITS = 2
IOU_THRESHOLD = 0.1
MIN_CLASSIFICATION = 3
MIN_PROBABILITY = 0.75
HIGH_RESET_TIME = 20
LOW_RESET_TIME = 5


class DetectorBox:
    def __init__(self, robot_id, conf, box):
        self.robot_id = robot_id  # 机器人编号
        self.conf = conf  # 机器人的置信度
        self.box = box  # 机器人的识别位置box: [x, y, w, h]


class TrackBox:
    def __init__(self):
        self.resetFlag = True  # 重新分类标志
        self.output = False  # 输出标志
        self.robot_id = -1  # 追踪目标的id
        self.resetRank = 0  # 重新分类等级
        self.resetCount = 0  # 重置计时器
        self.classifyCount = 0  # 连续分类计时器
        self.armorProb = 0  # 追踪目标的概率
        self.conf = 0  # 置信度
        self.tracker = KalmanTracker()  # 卡尔曼滤波器
        self.situation = -1  # 记录输出情况：-1刚创建，1检测更新，2已经预测


def get_iou(box_a, box_b):
    intersection = box_a & box_b
    inter_area = intersection.area()
    union_area = box_a.area() + box_b.area() - inter_area

    if union_area < 1e-9:
        return 0.0

    return float(inter_area / union_area)


class TargetDetect(object):
    def __init__(self):
        self.result = 0  # 判断结果是否正常输出
        self.frameCount = 0  # 帧数计数器

        self.iouMatrix = []  # iou matrix
        self.predictedBoxes = []  # 已经进行卡尔曼滤波预测
        self.assignment = []  # 成功进行匹配的容器
        self.unmatchedDetections = set()  # 未匹配的检测
        self.unmatchedTrajectories = set()  # 未匹配的跟踪
        self.allItems = set()  # 所有的目标
        self.matchedItems = set()  # 匹配到的目标
        self.matchedPairs = []  # 配对好的一对

    def TargetSort(self, detectBoxes: List[DetectorBox], trackers: List[TrackBox]):
        self.frameCount += 1

        # 初始化追踪器
        if len(trackers) == 0:
            for dBox in detectBoxes:
                box = dBox.box
                kBox = TrackBox()
                kBox.tracker = KalmanTracker(box)
                kBox.conf = dBox.conf
                trackers.append(kBox)

        # 追踪器预测本帧
        for track in trackers:
            track.tracker.predict()
            pBox = track.tracker.getHistory()
            track.situation = 2
            track.conf = 0
            if pBox[0] >= 0 and pBox[1] >= 0:
                self.predictedBoxes.append(pBox)
            else:
                trackers.remove(track)

        # 用于调试
        if len(self.predictedBoxes) == 0 and len(detectBoxes) == 0:
            self.result = -1
            return self.result

        # 匈牙利算法预处理
        for i in range(len(self.predictedBoxes)):
            self.iouMatrix.append([])
            for j in range(len(detectBoxes)):
                self.iouMatrix[i].append(1 - get_iou(self.predictedBoxes[i], detectBoxes[j].box))

        HungAlgo = linear_sum_assignment(self.iouMatrix)
        self.assignment = list(zip(HungAlgo[0], HungAlgo[1]))

        # 检测器多于追踪框，则认为有新的目标出现
        if len(self.predictedBoxes) < len(detectBoxes):
            self.allItems = str(range(detectBoxes))  # 将检测框中的目标为全部目标
            self.matchedItems = str(self.assignment[:len(self.predictedBoxes)])  # 将追踪框中的作为已配对
            self.unmatchedDetections = self.allItems - self.matchedItems  # 将上述两者的差集作为未配对的
        else:
            self.unmatchedTrajectories = {i for i, a in enumerate(self.assignment) if a == -1}  # 没有受到分配的检测框为新目标

        # 对分配矩阵进行处理
        for i in range(len(self.predictedBoxes)):
            if self.assignment[i] == -1:
                continue
            if 1 - self.iouMatrix[i][self.assignment[i]] < IOU_THRESHOLD:
                self.unmatchedTrajectories.add(i)
                self.unmatchedDetections.add(self.assignment[i])
            else:
                self.matchedPairs.append((i, self.assignment[i]))

        # 对于没有检测结果来更新的追踪框，采取以预测来更新
        for i in self.unmatchedTrajectories:
            pBox = trackers[i].tracker.getHistory()
            trackers[i].tracker.pre_update(pBox)

        # 对已分配队列进行处理，用检测结果对跟踪器进行更新
        for trackID, dectID in self.matchedPairs:
            trackers[trackID].tracker.update(detectBoxes[dectID].box)
            trackers[trackID].situation = 1
            trackers[trackID].conf = detectBoxes[dectID].conf

        # 对没有匹配到的检测框创建追踪器
        for umd in self.unmatchedDetections:
            tracker = KalmanTracker(detectBoxes[umd].box)
            kBox = TrackBox(tracker, detectBoxes[umd].conf)
            trackers.append(kBox)

        # 处理输出结果
        for track in trackers:
            if track.tracker.getSinceTime() <= MAX_AGE and ((track.tracker.getHits() >= MIN_HITS) or
                                                            (self.frameCount <= MIN_HITS)):
                track.outputFlag = True
                track.resetCount += 1
                if track.resetRank == 0:
                    track.resetFlag = True
                    track.resetCount = 0
                elif track.resetRank == 1 and track.resetCount >= LOW_RESET_TIME:
                    track.resetFlag = True
                    track.resetCount = 0
                elif track.resetRank == 2 and track.resetCount >= HIGH_RESET_TIME:
                    track.resetFlag = True
                    track.resetCount = 0
                else:
                    if track.situation == 2:
                        track.outputFlag = False

        trackers = [track for track in trackers if track.tracker.getSinceTime() <= MAX_AGE]
        return self.result
