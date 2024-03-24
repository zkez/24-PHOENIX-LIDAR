import numpy as np

import sys
sys.path.append('../')
from detect.ByteTrack.kalman_filter import KalmanFilter
from detect.ByteTrack import matching
from detect.ByteTrack.basetrack import BaseTrack, TrackState


# 存放轨迹
class STrack(BaseTrack):
    shared_kalman = KalmanFilter()

    def __init__(self, tlwh, score):  # tlwh:top left width height
        # 新建轨迹 轨迹属性
        self.tlwhs = np.asarray(tlwh)
        self.kalman_filter = None
        self.mean, self.covariance = None, None  # 均值 协方差
        # wait activate 轨迹的激活状态
        self.is_activated = False
        self.score = score
        # 被跟踪的次数
        self.tracked_len = 0

    def predict(self):
        mean_state = self.mean.copy()
        if self.state != TrackState.Tracked:
            mean_state[7] = 0
        # 更新均值 协方差
        self.mean, self.covariance = self.kalman_filter.predict(mean_state, self.covariance)

    @staticmethod
    def multi_predict(tracks):
        # 预测多个轨迹
        if len(tracks) > 0:
            multi_mean = np.asarray([st.mean.copy() for st in tracks])  # 均值
            multi_covariance = np.asarray([st.covariance for st in tracks])  # 协方差
            for i, st in enumerate(tracks):
                if st.state != TrackState.Tracked:
                    multi_mean[i][7] = 0
            multi_mean, multi_covariance = STrack.shared_kalman.multi_predict(multi_mean, multi_covariance)
            for i, (mean, cov) in enumerate(zip(multi_mean, multi_covariance)):
                tracks[i].mean = mean
                tracks[i].covariance = cov

    def activate(self, kalman_filter, frame_id):
        """Start a new tracked"""
        # 开始一个新的轨迹 初始化一个卡尔曼滤波器
        self.kalman_filter = kalman_filter
        # 跟踪ID
        self.track_id = self.next_id()
        self.mean, self.covariance = self.kalman_filter.initiate(self.tlwh_to_xyah(self.tlwhs))
        self.tracked_len = 0
        self.state = TrackState.Tracked  # 设置为“已追踪轨迹”
        if frame_id == 1:  # 第一帧直接成为激活状态
            self.is_activated = True
        self.frame_id = frame_id
        self.start_frame = frame_id

    def re_activate(self, new_track, frame_id, new_id=False):
        # 将旧轨迹（失追轨迹）激活
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self.tlwh_to_xyah(new_track.tlwh)
        )
        self.tracked_len = 0
        self.state = TrackState.Tracked
        self.is_activated = True
        self.frame_id = frame_id
        if new_id:
            self.track_id = self.next_id()
        self.score = new_track.score

    def update(self, new_track, frame_id):
        """
        Update a matched track
        :type new_track: STrack
        :type frame_id: int
        :return:
        """
        self.frame_id = frame_id
        self.tracked_len += 1

        new_tlwh = new_track.tlwh  # 检测出的目标框覆盖原来预测的目标框
        # 根据当前的位置预测新的方差 协方差
        self.mean, self.covariance = self.kalman_filter.update(
            self.mean, self.covariance, self.tlwh_to_xyah(new_tlwh))
        self.state = TrackState.Tracked
        self.is_activated = True
        self.score = new_track.score

    @property
    # @jit(nopython=True)
    def tlwh(self):
        """
        Get current position in bounding box format `(top left x, top left y, width, height)`.
        """
        if self.mean is None:
            return self.tlwhs.copy()
        # xyah to tlwh
        ret = self.mean[:4].copy()
        ret[2] *= ret[3]
        ret[:2] -= ret[2:] / 2
        return ret

    @property
    # @jit(nopython=True)
    def tlbr(self):
        """
        Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,`(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        # tlwh to tlbr
        ret[2:] += ret[:2]
        return ret

    @staticmethod
    # @jit(nopython=True)
    def tlwh_to_xyah(tlwh):
        """
        Convert bounding box to format `(center x, center y, aspect ratio, height)`, where the aspect ratio is `width / height`.
        """
        ret = np.asarray(tlwh).copy()
        # tlwh to xyah
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret

    def to_xyah(self):
        return self.tlwh_to_xyah(self.tlwh)

    @staticmethod
    # @jit(nopython=True)
    def tlbr_to_tlwh(tlbr):
        ret = np.asarray(tlbr).copy()
        # tlbr to tlwh
        ret[2:] -= ret[:2]
        return ret

    @staticmethod
    # @jit(nopython=True)
    def tlwh_to_tlbr(tlwh):
        ret = np.asarray(tlwh).copy()
        # tlwh to tlbr
        ret[2:] += ret[:2]
        return ret

    def __repr__(self):
        return 'OT_{}_({}-{})'.format(self.track_id, self.start_frame, self.end_frame)


class BYTETracker(object):
    def __init__(self, args, frame_rate=10):
        self.tracked_tracks = []  # type: list[STrack]
        self.lost_tracks = []  # type: list[STrack]
        self.removed_tracks = []  # type: list[STrack]

        self.frame_id = 0
        self.args = args
        self.det_thresh = args['track_thresh'] + 0.1
        self.buffer_size = int(frame_rate / 30.0 * args['track_buffer'])
        self.max_time_lost = self.buffer_size
        self.kalman_filter = KalmanFilter()

    def update(self, r_bboxes, r_scores, img_info, img_size):
        self.frame_id += 1
        activated_tracks = []  # 激活状态的轨迹
        refind_tracks = []  # 重新匹配到的失追轨迹
        lost_tracks = []  # 保存当前帧没有匹配到目标的轨迹
        removed_tracks = []  # 保存当前帧需要删除的轨迹

        img_h, img_w = img_info[0], img_info[1]
        scale = min(img_size[0] / float(img_h), img_size[1] / float(img_w))
        r_bboxes /= scale

        remain_inds = r_scores > self.args['track_thresh']  # 提取当前帧高分框
        inds_low = r_scores > 0.1  # 提取当前帧目标框中得分大于0.1的框
        inds_high = r_scores < self.args['track_thresh']  # 提取当前帧目标框中得分小于跟踪阈值的框

        inds_second = np.logical_and(inds_low, inds_high)
        dets_second = r_bboxes[inds_second]  # 提取目标框中得分小于跟踪阈值的框分数处于0.1<分数<跟踪阈值（低分框），用于匹配已跟踪但不活跃的轨迹(目标遮挡等)

        dets = r_bboxes[remain_inds]  # 提取得分处于大于跟踪阈值的目标框（高分框）

        scores_keep = r_scores[remain_inds]  # 提取得分大于跟踪阈值的目标框的得分（高分框的得分）
        scores_second = r_scores[inds_second]  # 提取分得分处于 0.1<分数<跟踪阈值 目标框的得分（低分框的得分）

        if len(dets) > 0:
            '''Detections'''
            # 为所有当前帧的高分框初始化一个轨迹
            detections = [STrack(STrack.tlbr_to_tlwh(tlbr), s) for
                          (tlbr, s) in zip(dets, scores_keep)]
        else:
            detections = []

        ''' Add newly detected tracked to tracked_tracks'''
        unconfirmed = []  # 存储未确认的框（新轨迹）
        tracked_tracks = []  # 历史帧已经跟踪上的轨迹（失追轨迹）
        # 遍历已跟踪的轨迹（包含激活和未激活）
        for track in self.tracked_tracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_tracks.append(track)

        ''' Step 2: First association, with high score detection boxes'''
        # 第一次匹配：将已追踪轨迹与失追轨迹合并 高分匹配
        strack_pool = joint_stracks(tracked_tracks, self.lost_tracks)
        # Predict the current location with KF
        STrack.multi_predict(strack_pool)
        # 计算当前帧中detections与strack_pool（当前帧的预测框和之前未匹配到轨迹的bbox）的代价矩阵
        dists = matching.iou_distance(strack_pool, detections)
        dists = matching.fuse_score(dists, detections)
        # 利用匈牙利算法匹配（更改match_thresh过滤较小的iou已达到获取高分框）
        matches, u_track, u_detection = matching.linear_assignment(dists, thresh=self.args['match_thresh'])
        # 遍历匹配上的轨迹
        for itracked, idet in matches:
            track = strack_pool[itracked]  # stack_pool中的第几个轨迹
            det = detections[idet]  # 当前帧检测出的第几个轨迹
            if track.state == TrackState.Tracked:
                track.update(detections[idet], self.frame_id)
                activated_tracks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_tracks.append(track)

        ''' Step 3: Second association, with low score detection boxes'''
        # 第二次匹配：低分匹配
        if len(dets_second) > 0:
            '''Detections'''
            detections_second = [STrack(STrack.tlbr_to_tlwh(tlbr), s) for
                          (tlbr, s) in zip(dets_second, scores_second)]
        else:
            detections_second = []
        # 找到第一次没有匹配上的轨迹，但是状态为已跟踪的轨迹(由于运动、遮挡，导致轨迹匹配度较小)
        r_tracked_tracks = [strack_pool[i] for i in u_track if strack_pool[i].state == TrackState.Tracked]
        # 计算r_tracked_tracks与detections_second(低分轨迹)之间的IOU（将低分框与未匹配上的轨迹匹配）
        dists = matching.iou_distance(r_tracked_tracks, detections_second)
        matches, u_track, u_detection_second = matching.linear_assignment(dists, thresh=0.5)
        for itracked, idet in matches:
            track = r_tracked_tracks[itracked]
            det = detections_second[idet]
            if track.state == TrackState.Tracked:
                track.update(det, self.frame_id)
                activated_tracks.append(track)
            else:
                track.re_activate(det, self.frame_id, new_id=False)
                refind_tracks.append(track)

        # 遍历第二次也没匹配上的轨迹，调用mark_lost方法，并加入lost_tracks，等待下一帧匹配
        for it in u_track:
            track = r_tracked_tracks[it]
            if not track.state == TrackState.Lost:
                track.mark_lost()  # 将状态标记为Lost在下一帧中会会继续进行匹配，如本函数开始时合并已跟踪的轨迹以及丢失的轨迹
                lost_tracks.append(track)

        '''Deal with unconfirmed tracks, usually tracks with only one beginning frame'''
        detections = [detections[i] for i in u_detection]
        dists = matching.iou_distance(unconfirmed, detections)
        dists = matching.fuse_score(dists, detections)
        matches, u_unconfirmed, u_detection = matching.linear_assignment(dists, thresh=0.7)
        for itracked, idet in matches:
            unconfirmed[itracked].update(detections[idet], self.frame_id)
            activated_tracks.append(unconfirmed[itracked])

        # 遍历第二次匹配中，历史轨迹没有与当前帧检测出来的轨迹相匹配的轨迹
        for it in u_unconfirmed:
            track = unconfirmed[it]
            track.mark_removed()
            removed_tracks.append(track)

        """ Step 4: Init new tracks"""
        # 遍历u_detection（前两步都没匹配到历史轨迹的的目标框,且得分超过跟踪阈值的)认为它是新的目标
        for inew in u_detection:
            track = detections[inew]
            if track.score < self.det_thresh:
                continue
            # 激活一个新的轨迹
            track.activate(self.kalman_filter, self.frame_id)
            activated_tracks.append(track)

        """ Step 5: Update state"""
        for track in self.lost_tracks:
            # 删除消失时间过长的轨迹
            if self.frame_id - track.end_frame > self.max_time_lost:
                track.mark_removed()
                removed_tracks.append(track)

        self.tracked_tracks = [t for t in self.tracked_tracks if t.state == TrackState.Tracked]  # 筛选出已跟踪的轨迹
        self.tracked_tracks = joint_stracks(self.tracked_tracks, activated_tracks)  # 将当前帧重新出现的活跃轨迹以及第一次出现的轨迹合并
        self.tracked_tracks = joint_stracks(self.tracked_tracks, refind_tracks)  # 将重新找到的轨迹重新合并到已跟踪的轨迹

        self.lost_tracks = sub_stracks(self.lost_tracks, self.tracked_tracks)  # 筛选出lost轨迹，参与下一帧的匹配
        self.lost_tracks.extend(lost_tracks)  # 将本帧新发现的lost_tracks添加到self.lost_tracks
        self.lost_tracks = sub_stracks(self.lost_tracks, self.removed_tracks)  # 在lost轨迹中剔除要删除的轨迹

        self.removed_tracks.extend(removed_tracks)  # 添加本帧要删除的轨迹

        self.tracked_tracks, self.lost_tracks = remove_duplicate_stracks(self.tracked_tracks, self.lost_tracks)  # 去除重复轨迹

        # 返回当前帧活跃轨迹
        output_tracks = [track for track in self.tracked_tracks if track.is_activated]

        return output_tracks


def joint_stracks(tlista, tlistb):
    exists = {}
    res = []
    for t in tlista:
        exists[t.track_id] = 1
        res.append(t)
    for t in tlistb:
        tid = t.track_id
        if not exists.get(tid, 0):
            exists[tid] = 1
            res.append(t)
    return res


def sub_stracks(tlista, tlistb):
    stracks = {}
    for t in tlista:
        stracks[t.track_id] = t
    for t in tlistb:
        tid = t.track_id
        if stracks.get(tid, 0):
            del stracks[tid]
    return list(stracks.values())


def remove_duplicate_stracks(stracksa, stracksb):
    pdist = matching.iou_distance(stracksa, stracksb)
    pairs = np.where(pdist < 0.15)
    dupa, dupb = list(), list()
    for p, q in zip(*pairs):
        timep = stracksa[p].frame_id - stracksa[p].start_frame
        timeq = stracksb[q].frame_id - stracksb[q].start_frame
        if timep > timeq:
            dupb.append(q)
        else:
            dupa.append(p)
    resa = [t for i, t in enumerate(stracksa) if not i in dupa]
    resb = [t for i, t in enumerate(stracksb) if not i in dupb]
    return resa, resb
