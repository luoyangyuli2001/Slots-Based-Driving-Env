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
                    # 更新 center 与 heading
                    center_pos = slot.position_start + slot.length / 2
                    center_xy, heading = self.interpolate_position_and_heading(shape, center_pos)
                    slot.center = center_xy
                    slot.heading = heading
                    updated_slots.append(slot)

            # === 再生逻辑 ===
            if not updated_slots:
                allow_insert = True
            else:
                head_slot = updated_slots[0]
                allow_insert = head_slot.position_start >= self.min_spawn_distance

            if allow_insert:
                new_slot = self.slot_generator.generate_single_slot_on_full_lane(fl)
                new_slot.center, new_slot.heading = self.interpolate_position_and_heading(shape, new_slot.length / 2)
                updated_slots.insert(0, new_slot)

            # 排序：确保 slot 始终按 position_start 升序排列
            updated_slots.sort(key=lambda s: s.position_start)

            fl.slots = updated_slots

        return removed_slots

    def interpolate_position_and_heading(self, shape, target_distance):
        """
        插值并计算当前位置与切线方向 (heading in degrees)
        """
        accumulated = 0.0
        for i in range(len(shape) - 1):
            x1, y1 = shape[i]
            x2, y2 = shape[i + 1]
            dx = x2 - x1
            dy = y2 - y1
            segment_length = math.hypot(dx, dy)

            if accumulated + segment_length >= target_distance:
                ratio = (target_distance - accumulated) / segment_length
                x = x1 + ratio * dx
                y = y1 + ratio * dy
                heading = math.degrees(math.atan2(dy, dx))
                return (x, y), heading

            accumulated += segment_length

        # fallback 到最后一个segment尾部
        x1, y1 = shape[-2]
        x2, y2 = shape[-1]
        heading = math.degrees(math.atan2(y2 - y1, x2 - x1))
        return shape[-1], heading
