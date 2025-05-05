# Controller/slot_controller.py

import math
from typing import List, Tuple
from Entity.slot import Slot
from Entity.fulllane import FullLane
from Controller.slot_generator import SlotGenerator
from Config import config

class SlotController:
    def __init__(self, slot_generator: SlotGenerator, full_lanes: List[FullLane], time_step: float = None):
        self.slot_generator = slot_generator
        self.full_lanes = full_lanes
        self.time_step = time_step if time_step is not None else config.TIME_STEP
        self.min_spawn_distance = slot_generator.slot_length + slot_generator.slot_gap

    def step(self) -> List[Tuple[Slot, FullLane]]:
        """
        推进所有 slot，完成再生与移除
        :return: 被移除的 slot 和其所属 full_lane 列表
        """
        removed_slots = []

        for fl in self.full_lanes:
            total_length = fl.get_total_length()
            shape = fl.full_shape
            updated_slots = []

            for slot in fl.slots:
                # 基于 arc 长度推进
                slot.position_start += slot.speed * self.time_step
                slot.position_end = slot.position_start + slot.length

                if slot.position_start >= total_length:
                    removed_slots.append((slot, fl))
                else:
                    # 实时更新 center 坐标
                    center_pos = slot.position_start + slot.length / 2
                    slot.center = self.interpolate(shape, center_pos)
                    updated_slots.append(slot)

            # === 再生逻辑 ===
            if not updated_slots:
                allow_insert = True
            else:
                head_slot = updated_slots[0]
                allow_insert = head_slot.position_start >= self.min_spawn_distance

            if allow_insert:
                new_slot = self.slot_generator.generate_single_slot_on_full_lane(fl)
                new_slot.center = self.interpolate(shape, new_slot.position_start + new_slot.length / 2)
                updated_slots.insert(0, new_slot)

            # 排序：确保 slot 始终按 position_start 升序排列
            updated_slots.sort(key=lambda s: s.position_start)

            fl.slots = updated_slots

        return removed_slots

    @staticmethod
    def interpolate(shape, target_distance):
        """
        在 shape 上插值计算目标距离对应的坐标
        """
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
        return shape[-1]  # fallback
