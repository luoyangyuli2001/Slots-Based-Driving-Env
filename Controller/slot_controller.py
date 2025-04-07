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
from Controller.slot_generator import generate_single_slot_on_lane

class SlotController:
    def __init__(self, slots: List[Slot], time_step: float = 0.1):
        """
        初始化 Slot 控制器
        :param slots: 初始 slot 列表（所有 lane 的 slot 可合并）
        """
        self.slots = slots
        self.time_step = time_step  # 默认每个 step 模拟 1 秒
        self.slot_length = 8.0      # 默认slot 长度为8
        self.slot_gap = 3.0         # 默认slot gap为3

    def step(self):
        # 存储需要保留的 slot
        new_slots = []
        respawn_lanes = []

        for slot in self.slots:
            distance = slot.speed * self.time_step
            slot.position_start += distance
            slot.position_end += distance

            # 情况一：slot 已到达末尾且无 next_lane → 回收
            # slot 到达末端且没有下一个 lane，不添加进new_slots, 即移除 ,并准备 respawn
            if not slot.lane.next_lane and slot.position_start >= slot.lane.length:
                if slot.lane.is_end and slot.lane.entry_ref:
                    respawn_lanes.append(slot.lane.entry_ref)
                continue

            # 情况二：slot 可进入下一个 lane
            elif slot.position_start >= slot.lane.length and slot.lane.next_lane:
                slot.lane = slot.lane.next_lane
                slot.position_start = 0.0
                slot.position_end = slot.length
                slot.center = None
                new_slots.append(slot)
            else:
                new_slots.append(slot)

        self.slots = new_slots  # 更新 slot 列表

        # 执行 slot 再生
        for lane in respawn_lanes:
            new_slot = generate_single_slot_on_lane(
                lane=lane,
                slot_length=self.slot_length,
                slot_gap=self.slot_gap
            )
            self.slots.append(new_slot)

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
