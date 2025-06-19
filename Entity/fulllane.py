# Entity/full_lane.py

import math

class FullLane:
    def __init__(self, start_lane_id):
        self.start_lane_id = start_lane_id
        self.lanes = []  # 顺序存储，按照行驶路径顺序
        self.full_shape = []  # 组合而成的完整轨迹点
        self.neighbor_full_lanes = []  # 邻接 FullLane 信息，格式: (start_x, end_x, neighbor_full_lane, direction)

    def add_lane(self, lane):
        """顺序添加一个 lane，并更新 full_shape"""
        if not self.lanes:
            self.full_shape.extend(lane.shape)
        else:
            last_point = self.full_shape[-1]
            if lane.shape and lane.shape[0] == last_point:
                self.full_shape.extend(lane.shape[1:])
            else:
                self.full_shape.extend(lane.shape)
        self.lanes.append(lane)

    def add_neighbor_full_lane(self, start_x, end_x, neighbor_full_lane, direction):
        """注册邻接 FullLane（在 start_x 到 end_x 范围内相邻）"""
        self.neighbor_full_lanes.append((start_x, end_x, neighbor_full_lane, direction))

    def find_neighbor_slot_by_position(self, position_x, position_y):
        """
        根据当前位置，查找邻接 FullLane 中最接近 position 的 slot
        要求该 slot 未被占用，且位于注册的邻接区间内
        """
        best_slot = None
        min_dist = float('inf')

        for start_x, end_x, neighbor_lane in self.neighbor_full_lanes:
            if not (start_x <= position_x <= end_x):
                continue
            if not hasattr(neighbor_lane, "slots"):
                continue
            for slot in neighbor_lane.slots:
                if slot.occupied:
                    continue
                sx, sy = slot.center
                dist = math.hypot(sx - position_x, sy - position_y)
                if dist < min_dist:
                    min_dist = dist
                    best_slot = slot

        return best_slot

    def get_total_length(self):
        """计算 FullLane 的几何长度"""
        length = 0
        for i in range(1, len(self.full_shape)):
            x1, y1 = self.full_shape[i - 1]
            x2, y2 = self.full_shape[i]
            length += math.hypot(x2 - x1, y2 - y1)
        return length

    def __repr__(self):
        return f"FullLane(start={self.start_lane_id}, lanes={[lane.id for lane in self.lanes]})"
        return f"FullLane(start={self.start_lane_id}, lanes={[lane.id for lane in self.lanes]}, shape={self.full_shape})"
