# Controller/slot_controller.py


import math
import os
import sys
from typing import List

# === 设置路径 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)


from Entity.slot import Slot

class SlotController:
    def __init__(self, slots: List[Slot], time_step: float = 0.1):
        """
        初始化 Slot 控制器
        :param slots: 初始 slot 列表（所有 lane 的 slot 可合并）
        """
        self.slots = slots
        self.time_step = time_step  # 默认每个 step 模拟 1 秒

    def step(self):
        for slot in self.slots:
            distance = slot.speed * self.time_step
            slot.position_start += distance
            slot.position_end += distance

            # if slot.center is not None:
            #     slot.center = (
            #         slot.center[0],  # 当前简化，不修改 x
            #         slot.center[1]   # 同上，不修改 y
            #     )

            if slot.position_start >= slot.lane.length:
                if slot.lane.next_lane:
                    slot.lane = slot.lane.next_lane
                    slot.position_start = 0.0
                    slot.position_end = slot.length
                    slot.center = None  # 等待下帧插值更新
                else:
                    # 暂不处理末端 slot（可清除或重生）
                    continue


    def update_center_by_lane_shape(self, lane_shape_lookup):
        """
        更新所有 slot 的 center 坐标（依赖外部提供 shape）
        lane_shape_lookup: dict[lane_id] -> shape 点集
        """
        def interpolate(shape, target_distance):
            accumulated = 0.0
            for i in range(len(shape) - 1):
                x1, y1 = shape[i]
                x2, y2 = shape[i + 1]
                dx = x2 - x1
                dy = y2 - y1
                segment_length = math.hypot(dx, dy)

                if accumulated + segment_length >= target_distance:
                    ratio = (target_distance - accumulated) / segment_length
                    return (x1 + ratio * dx, y1 + ratio * dy)
                accumulated += segment_length
            return shape[-1]

        for slot in self.slots:
            shape = lane_shape_lookup.get(slot.lane.id)
            if shape:
                center_d = (slot.position_start + slot.position_end) / 2
                slot.center = interpolate(shape, center_d)
