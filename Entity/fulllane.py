# Entity/full_lane.py

import math

class FullLane:
    def __init__(self, id: str):
        """
        表示一整条逻辑连续的车道链，包含多个 Lane (跨越多个 Segment).
        :param id: 全局唯一 ID 或命名(如 full_0)
        """
        self.id = id
        self.lanes = []           # 类型: List[Lane]
        self.entry_lane = None    # 起点 Lane (is_entry = True)
        self.end_lane = None      # 终点 Lane (is_end = True)
        self.slots = []           # 类型: List[Slot]，绑定的所有 Slot

    def add_lane(self, lane):
        """
        添加组成该 FullLane 的一段 Lane, 按顺序添加
        """
        self.lanes.append(lane)
        if getattr(lane, "is_entry", False):
            self.entry_lane = lane
        if getattr(lane, "is_end", False):
            self.end_lane = lane

    def get_total_length(self):
        shape = self.get_combined_shape()
        total = 0.0
        for i in range(len(shape) - 1):
            x1, y1 = shape[i]
            x2, y2 = shape[i + 1]
            total += math.hypot(x2 - x1, y2 - y1)
        return total


    def get_combined_shape(self):
        """拼接所有 Lane 的 shape 构建一条完整形状线"""
        combined_shape = []
        for lane in self.lanes:
            if not lane.shape:
                continue
            if not combined_shape:
                combined_shape.extend(lane.shape)
            else:
                # 防止重复点（连续段之间相接时会有重复）
                if combined_shape[-1] == lane.shape[0]:
                    combined_shape.extend(lane.shape[1:])
                else:
                    combined_shape.extend(lane.shape)
        return combined_shape

    def __repr__(self):
        return f"[FULLLANE] {self.id} | lanes: {[lane.id for lane in self.lanes]}"
