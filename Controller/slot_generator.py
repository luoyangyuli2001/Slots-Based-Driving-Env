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

    def interpolate_position_from_shape(self, shape, target_distance):
        accumulated = 0.0
        for i in range(len(shape) - 1):
            x1, y1 = shape[i]
            x2, y2 = shape[i + 1]
            dx = x2 - x1
            dy = y2 - y1
            segment_length = math.hypot(dx, dy)

            if accumulated + segment_length >= target_distance:
                ratio = (target_distance - accumulated) / segment_length
                return x1 + ratio * dx, y1 + ratio * dy

            accumulated += segment_length

        return shape[-1]

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

            slot = Slot(
                id=slot_id,
                lane=lane,
                segment_id=lane.segment_id if lane else "unknown",
                index=self.global_index,
                position_start=position,
                length=self.slot_length,
                gap_to_previous=self.slot_gap,
                speed=speed
            )
            slot.center = self.interpolate_position_from_shape(shape, position + self.slot_length / 2)
            slots.append(slot)

            position += self.slot_length + self.slot_gap

        slots.sort(key=lambda s: s.position_start)
        full_lane.slots = slots
        return slots

    def generate_single_slot_on_full_lane(self, full_lane: FullLane) -> Slot:
        """
        在 full_lane 起点处生成一个 slot（用于再生）
        """
        slot_id = f"slot_{self.global_index}"
        self.global_index += 1
        lane = full_lane.lanes[0]
        return Slot(
            id=slot_id,
            lane=lane,
            segment_id=lane.segment_id,
            index=self.global_index,
            position_start=0.0,
            length=self.slot_length,
            gap_to_previous=self.slot_gap,
            speed=lane.speed
        )

    def generate_slots_for_all_full_lanes(self, full_lanes):
        all_slots = []
        for full_lane in full_lanes:
            slots = self.generate_slots_for_full_lane(full_lane)
            full_lane.slots = slots
            all_slots.extend(slots)
        return all_slots


# === 以下为旧实现，保留作参考（基于 Lane 而非 FullLane） ===

# def generate_single_slot_on_lane(lane, slot_length=8.0, slot_gap=3.0):
#     global global_index
#     slot_id = f"slot_{global_index}"
#     global_index += 1
#     return Slot(
#         id=slot_id,
#         lane=lane,
#         index=-1,
#         position_start=0.0,
#         length=slot_length,
#         gap_to_previous=slot_gap,
#         segment_id=lane.segment_id,
#         speed=lane.speed
#     )


# def generate_slots_for_lane(lane, slot_length=8.0, slot_gap=3.0):
#     global global_index
#     slots = []
#     lane_length = lane.length
#     step = slot_length + slot_gap
#     num_slots = int(math.floor(lane_length / step))
#     shape = traci.lane.getShape(lane.id)

#     for i in range(num_slots):
#         global_index += 1
#         start_pos = i * step
#         slot_id = f"slot_{global_index}"

#         slot = Slot(
#             id=slot_id,
#             segment_id=lane.segment_id,
#             lane=lane,
#             index=global_index,
#             position_start=start_pos,
#             length=slot_length,
#             gap_to_previous=slot_gap,
#             speed=lane.speed
#         )
#         slot.center = interpolate_position_from_shape(shape, slot.center)
#         slots.append(slot)

#     return slots


# def generate_slots_for_all_segments(segments, slot_length=8.0, slot_gap=3.0):
#     all_slots = []
#     for segment in segments:
#         if segment.segment_type != "standard":
#             continue
#         for lane in segment.lanes:
#             lane.segment_id = segment.id
#             lane_slots = generate_slots_for_lane(
#                 lane,
#                 slot_length=slot_length,
#                 slot_gap=slot_gap
#             )
#             all_slots.extend(lane_slots)
#     return all_slots