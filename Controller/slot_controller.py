# Controller/slot_controller.py


import math
import os
import sys
from typing import List, Dict, Tuple

# === 设置路径 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)


from Entity.slot import Slot
from Entity.fulllane import FullLane
from Controller.slot_generator import generate_single_slot_on_full_lane

class SlotController:
    def __init__(self, full_lanes: List[FullLane], time_step: float = 0.1):
        """
        初始化 Slot 控制器
        :param slots: 初始 slot 列表（所有 lane 的 slot 可合并）
        """
        self.full_lanes = full_lanes
        self.time_step = time_step  # 默认每个 step 模拟 1 秒 0.1s

    def step(self) -> List[Tuple[Slot, FullLane]]:
        """
        推进所有 slot，并返回到达末尾需要移除的 slot 及其所在 full_lane
        :return: List of (slot, full_lane) 元组
        """
        removed_slots = []

        for fl in self.full_lanes:
            updated_slots = []
            for slot in fl.slots:
                # 推进位置
                slot.position_start += slot.speed * self.time_step
                slot.position_end = slot.position_start + slot.length

                # 判断是否超出 full_lane
                if slot.position_start >= fl.get_total_length():
                    removed_slots.append((slot, fl))
                    new_slot = generate_single_slot_on_full_lane(fl)
                    updated_slots.append(new_slot)
                else:
                    updated_slots.append(slot)

            fl.slots = updated_slots

        return removed_slots

    def update_center_by_shape(self):
        """
        使用 FullLane 的形状插值更新所有 slot 的中心点坐标。
        """
        for full_lane in self.full_lanes:
            shape = full_lane.get_combined_shape()
            for slot in full_lane.slots:
                center_d = slot.position_start + slot.length / 2
                slot.center = self.interpolate(shape, center_d)


    @staticmethod
    def interpolate(shape, target_distance):
        accumulated = 0.0
        for i in range(len(shape) - 1):
            x1, y1 = shape[i]
            x2, y2 = shape[i + 1]
            dx = x2 - x1
            dy = y2 - y1
            seg_len = math.hypot(dx, dy)
            if accumulated + seg_len >= target_distance:
                ratio = (target_distance - accumulated) / seg_len
                return (x1 + dx * ratio, y1 + dy * ratio)
            accumulated += seg_len
        return shape[-1]
