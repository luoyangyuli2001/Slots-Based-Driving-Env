# Controller/slot_controller.py

import math
from typing import List, Tuple
from Entity.slot import Slot
from Entity.fulllane import FullLane
from Controller.slot_generator import SlotGenerator
from Config.config import default_config

class SlotController:
    def __init__(self, slot_generator: SlotGenerator, full_lanes: List[FullLane], time_step: float = None):
        """
        Controls the lifecycle of slots: advancing, removing, and regenerating them.

        Args:
            slot_generator (SlotGenerator): Responsible for creating new slots.
            full_lanes (List[FullLane]): All FullLane objects where slots exist and move.
            time_step (float, optional): Simulation time step. If not provided, defaults to config.
        """
        self.slot_generator = slot_generator
        self.full_lanes = full_lanes
        self.time_step = time_step if time_step is not None else default_config["time_step"]
        self.min_spawn_distance = slot_generator.slot_length + slot_generator.slot_gap

    def step(self) -> List[Tuple[Slot, FullLane]]:
        """
        Advance all slots, handle removal and regeneration.

        Returns:
            List[Tuple[Slot, FullLane]]: A list of removed slots and their corresponding FullLane.
        """
        removed_slots = []

        for fl in self.full_lanes:
            total_length = fl.get_total_length()
            shape = fl.full_shape
            updated_slots = []

            for slot in fl.slots:
                # Advance slot based on arc length
                slot.position_start += slot.speed * self.time_step
                slot.position_end = slot.position_start + slot.length

                if slot.position_start >= total_length:
                    removed_slots.append((slot, fl))
                else:
                    # Update center and heading
                    center_pos = slot.position_start + slot.length / 2
                    center_xy, heading = self.interpolate_position_and_heading(shape, center_pos)
                    slot.center = center_xy
                    slot.heading = heading
                    updated_slots.append(slot)

            # === Regeneration logic ===
            if not updated_slots:
                allow_insert = True
            else:
                head_slot = updated_slots[0]
                allow_insert = head_slot.position_start >= self.min_spawn_distance

            if allow_insert:
                new_slot = self.slot_generator.generate_single_slot_on_full_lane(fl)
                new_slot.center, new_slot.heading = self.interpolate_position_and_heading(shape, new_slot.length / 2)
                updated_slots.insert(0, new_slot)

            # Sort slots to ensure ascending order of position_start
            updated_slots.sort(key=lambda s: s.position_start)

            fl.slots = updated_slots

        return removed_slots

    def interpolate_position_and_heading(self, shape, target_distance):
        """
        Interpolate a position and calculate heading at a given distance along a shape polyline.

        Args:
            shape (List[Tuple[float, float]]): Polyline representing the lane geometry.
            target_distance (float): Arc length distance along the shape.

        Returns:
            Tuple[Tuple[float, float], float]: The (x, y) position and heading (in degrees) at the given distance.
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

        # Fallback to the end of the last segment
        x1, y1 = shape[-2]
        x2, y2 = shape[-1]
        heading = math.degrees(math.atan2(y2 - y1, x2 - x1))
        return shape[-1], heading
