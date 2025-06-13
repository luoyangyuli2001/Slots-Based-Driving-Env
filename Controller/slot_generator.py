# Controller/slot_generator.py

import math
from Entity.slot import Slot
from Entity.fulllane import FullLane
from Config import config

class SlotGenerator:
    def __init__(self, slot_length=None, slot_gap=None):
        self.slot_length = slot_length if slot_length is not None else config.SLOT_LENGTH
        self.slot_gap = slot_gap if slot_gap is not None else config.SLOT_GAP
        self.global_index = 0

    def interpolate_position_and_heading(self, shape, target_distance):
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

        # fallback (最后一个点)
        x1, y1 = shape[-2]
        x2, y2 = shape[-1]
        heading = math.degrees(math.atan2(y2 - y1, x2 - x1))
        return shape[-1], heading

    def generate_slots_for_full_lane(self, full_lane):
        slots = []
        total_length = full_lane.get_total_length()
        shape = full_lane.full_shape
        speed = full_lane.lanes[0].speed if full_lane.lanes else 0.0
        lane = full_lane.lanes[0] if full_lane.lanes else None

        position = 0.0
        while position + self.slot_length <= total_length:
            slot_id = f"slot_{self.global_index}"
            self.global_index += 1

            center_pos = position + self.slot_length / 2
            center_xy, heading = self.interpolate_position_and_heading(shape, center_pos)

            slot = Slot(
                id=slot_id,
                lane=lane,
                segment_id=lane.segment_id if lane else "unknown",
                index=self.global_index,
                position_start=position,
                length=self.slot_length,
                gap_to_previous=self.slot_gap,
                speed=speed,
                heading=heading
            )
            slot.center = center_xy
            slots.append(slot)

            position += self.slot_length + self.slot_gap

        slots.sort(key=lambda s: s.position_start)
        full_lane.slots = slots
        return slots

    def generate_single_slot_on_full_lane(self, full_lane: FullLane) -> Slot:
        slot_id = f"slot_{self.global_index}"
        self.global_index += 1
        lane = full_lane.lanes[0]

        center_pos = 0.0 + self.slot_length / 2
        center_xy, heading = self.interpolate_position_and_heading(full_lane.full_shape, center_pos)

        slot = Slot(
            id=slot_id,
            lane=lane,
            segment_id=lane.segment_id,
            index=self.global_index,
            position_start=0.0,
            length=self.slot_length,
            gap_to_previous=self.slot_gap,
            speed=lane.speed,
            heading=heading
        )
        slot.center = center_xy
        return slot

    def generate_slots_for_all_full_lanes(self, full_lanes):
        all_slots = []
        for full_lane in full_lanes:
            slots = self.generate_slots_for_full_lane(full_lane)
            full_lane.slots = slots
            all_slots.extend(slots)
        return all_slots
