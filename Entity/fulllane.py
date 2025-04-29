# Entity/full_lane.py

import math

class FullLane:
    def __init__(self, start_lane_id):
        self.start_lane_id = start_lane_id
        self.lanes = []  # 顺序存储，按照行驶路径顺序
        self.full_shape = []  # 组合而成的完整轨迹点

    def add_lane(self, lane):
        """顺序添加一个lane，并更新full_shape"""
        if not self.lanes:
            self.full_shape.extend(lane.shape)
        else:
            # 避免shape重复连接点
            last_point = self.full_shape[-1]
            if lane.shape and lane.shape[0] == last_point:
                self.full_shape.extend(lane.shape[1:])
            else:
                self.full_shape.extend(lane.shape)
        
        self.lanes.append(lane)

    def get_total_length(self):
        """计算FullLane的几何长度"""
        length = 0
        for i in range(1, len(self.full_shape)):
            x1, y1 = self.full_shape[i-1]
            x2, y2 = self.full_shape[i]
            length += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        return length

    def __repr__(self):
        return f"FullLane(start={self.start_lane_id}, lanes={[lane.id for lane in self.lanes]}, shape={self.full_shape})"
