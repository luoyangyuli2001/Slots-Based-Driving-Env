# Controller/vehicle_controller.py

import traci
import math

class VehicleController:
    def __init__(self, vehicle_list, route_groups):
        """
        Initialize the VehicleController.

        Args:
            vehicle_list (List[Vehicle]): List of all active vehicles in the simulation.
            route_groups (dict): Grouped route IDs for rerouting logic based on direction and entry edge.
        """
        self.vehicle_list = vehicle_list
        self.route_groups = route_groups

    def step(self):
        """
        Synchronize vehicle state with their assigned slots and execute speed control,
        rerouting logic, and slot releasing upon exit.
        """
        to_remove = []

        for vehicle in self.vehicle_list:
            veh_id = vehicle.id
            slot = vehicle.current_slot

            try:
                if veh_id not in traci.vehicle.getIDList():
                    to_remove.append(vehicle)
                    continue

                # Update vehicle's current position, heading, and speed
                front_x, front_y = traci.vehicle.getPosition(veh_id)
                heading_deg = traci.vehicle.getAngle(veh_id)
                heading_rad = math.radians(heading_deg)
                speed = traci.vehicle.getSpeed(veh_id)

                center_x = front_x - (vehicle.vehicle_type.length / 2.0) * math.cos(heading_rad)
                center_y = front_y - (vehicle.vehicle_type.length / 2.0) * math.sin(heading_rad)
                vehicle.position = (center_x, center_y)
                vehicle.heading = heading_deg
                vehicle.speed = speed

                # === Exit Detection ===
                current_edge = traci.vehicle.getRoadID(veh_id)
                if vehicle.current_slot and "off_ramp" in current_edge:
                    vehicle.current_slot.release()
                    vehicle.current_slot.busy = False
                    vehicle.current_slot = None

                    if vehicle.previous_slot:
                        vehicle.previous_slot.release()
                        vehicle.previous_slot.busy = False
                        vehicle.previous_slot = None

                    print(f"[INFO] Vehicle {veh_id} entered {current_edge}, released slot")

                # === Action Completion Detection ===
                if vehicle.previous_slot:
                    new_slot = vehicle.current_slot
                    dx = new_slot.center[0] - center_x
                    dy = new_slot.center[1] - center_y
                    new_slot_heading_rad = math.radians(new_slot.heading)
                    dist = abs(dx * math.cos(new_slot_heading_rad) + dy * math.sin(new_slot_heading_rad))
                    if dist < 1.0:
                        vehicle.previous_slot.release()
                        vehicle.previous_slot.busy = False
                        vehicle.current_slot.busy = False
                        print(f"[ACTION] Vehicle {vehicle.id} completed action, released slot {vehicle.previous_slot.id}")
                        vehicle.previous_slot = None

                # === Slot Synchronization Control ===
                if vehicle.current_slot:
                    slot = vehicle.current_slot
                    dx = slot.center[0] - center_x
                    dy = slot.center[1] - center_y
                    slot_heading_rad = math.radians(slot.heading)
                    delta_along = dx * math.cos(slot_heading_rad) + dy * math.sin(slot_heading_rad)

                    tolerance = 0.01
                    max_adjust = 2.0
                    if abs(delta_along) > tolerance:
                        correction = max(-max_adjust, min(max_adjust, 0.8 * delta_along))
                        target_speed = max(0, min(slot.speed + correction, vehicle.vehicle_type.max_speed))
                        traci.vehicle.setSpeed(veh_id, target_speed)
                    else:
                        traci.vehicle.setSpeed(veh_id, slot.speed)
                        slot.busy = False

                # === Reroute Logic ===
                route_id = traci.vehicle.getRouteID(veh_id)
                if route_id.startswith("route_"):
                    parts = route_id.split("_")
                    is_reverse = parts[-1] == "r"
                    entry = parts[1]
                    group_key = f"{entry}_{'reverse' if is_reverse else 'forward'}"
                    if group_key in self.route_groups:
                        route_list = self.route_groups[group_key]
                        if route_id in route_list:
                            current_index = route_list.index(route_id)
                            if current_index < len(route_list) - 1:
                                route_edges = traci.vehicle.getRoute(veh_id)
                                current_edge_index = route_edges.index(current_edge) if current_edge in route_edges else -1
                                if current_edge_index == len(route_edges) - 2:
                                    pos_on_lane = traci.vehicle.getLanePosition(veh_id)
                                    lane_id = traci.vehicle.getLaneID(veh_id)
                                    lane_length = traci.lane.getLength(lane_id)
                                    if lane_length - pos_on_lane < 50:
                                        lane_index = int(lane_id.split("_")[-1])
                                        if lane_index != 0:
                                            new_route_id = route_list[current_index + 1]
                                            traci.vehicle.setRouteID(veh_id, new_route_id)
                                            print(f"[REROUTE] Vehicle {veh_id} rerouted: {route_id} -> {new_route_id}")

            except traci.TraCIException as e:
                print(f"[WARN] Control failed for {veh_id}: {e}")
                to_remove.append(vehicle)

        # Remove vehicles no longer in simulation
        for v in to_remove:
            self.vehicle_list.remove(v)
            print(f"[CLEAN] Removed vehicle {v.id}")

    def _get_vehicle_by_slot(self, slot):
        for vehicle in self.vehicle_list:
            if vehicle.id == slot.vehicle_id:
                return vehicle
        return None

    def execute_slot_action(self, slot, action_id: int):
        """
        Execute an action on the vehicle bound to the specified slot.

        Args:
            slot (Slot): The slot whose vehicle will execute the action.
            action_id (int): The action to be executed.
        """
        vehicle_id = slot.vehicle_id
        if vehicle_id is None:
            print(f"[SKIP] Slot {slot.id} has no vehicle bound. Action {action_id} skipped.")
            return
        vehicle = self._get_vehicle_by_slot(slot)
        if vehicle is None:
            print(f"[ERROR] No vehicle found for slot {slot.id}. Action {action_id} skipped.")
            return

        self.perform_action(vehicle, action_id)

    def perform_action(self, vehicle, action_id: int):
        """
        Perform a slot-based driving action (move forward/backward/lane change/stay) for a vehicle.

        Args:
            vehicle (Vehicle): The vehicle performing the action.
            action_id (int): The action ID.
                0 - Stay
                1 - Move forward
                2 - Move backward
                3 - Lane change left
                4 - Lane change right
        """
        slot = vehicle.current_slot
        if not slot or not hasattr(slot, "full_lane") or slot.full_lane is None:
            print(f"[SKIP] Vehicle {vehicle.id} has no valid slot. Action {action_id} skipped.")
            return

        if slot.busy:
            print(f"[BLOCK] Slot {slot.id} is busy. Action skipped.")
            return

        full_lane = slot.full_lane
        slots = full_lane.slots
        try:
            current_pos = next(i for i, s in enumerate(slots) if s.id == slot.id)
        except StopIteration:
            print(f"[ERROR] Slot {slot.id} not found in full_lane.")
            return

        if action_id == 1 and current_pos + 1 < len(slots):  # Move forward
            new_slot = slots[current_pos + 1]
            if new_slot.occupied or new_slot.busy:
                print(f"[BLOCK] Slot {new_slot.id} is busy or occupied. Cannot move forward.")
                return
            slot.busy = True
            new_slot.busy = True
            vehicle.previous_slot = slot
            vehicle.current_slot = new_slot
            new_slot.occupy(vehicle.id)
            print(f"[ACTION] Vehicle {vehicle.id} moved forward to slot {new_slot.id}")

        elif action_id == 2 and current_pos - 1 >= 0:  # Move backward
            new_slot = slots[current_pos - 1]
            if new_slot.occupied or new_slot.busy:
                print(f"[BLOCK] Slot {new_slot.id} is busy or occupied. Cannot move backward.")
                return
            slot.busy = True
            new_slot.busy = True
            vehicle.previous_slot = slot
            vehicle.current_slot = new_slot
            new_slot.occupy(vehicle.id)
            print(f"[ACTION] Vehicle {vehicle.id} moved backward to slot {new_slot.id}")

        elif action_id in [3, 4]:  # Lane change
            lane_id = traci.vehicle.getLaneID(vehicle.id)
            if "ramp" in lane_id.lower():
                print(f"[INFO] Vehicle {vehicle.id} is on a ramp. Lane change not allowed.")
                return
            if ":" in lane_id.lower():
                print(f"[INFO] Vehicle {vehicle.id} is on an internal edge. Lane change not allowed.")
                return

            direction = -1 if action_id == 3 else 1
            current_x = slot.center[0]

            candidate_full_lanes = []
            for start_x, end_x, neighbor, neighbor_direction in full_lane.neighbor_full_lanes:
                if neighbor_direction == direction and start_x <= current_x <= end_x:
                    candidate_full_lanes.append(neighbor)

            if not candidate_full_lanes:
                print(f"[LANE CHANGE] No adjacent FullLane available for vehicle {vehicle.id} to change {'left' if direction == -1 else 'right'}.")
                return

            best_slot = None
            for neighbor_full_lane in candidate_full_lanes:
                for s in neighbor_full_lane.slots:
                    dx = s.center[0] - slot.center[0]
                    dy = s.center[1] - slot.center[1]
                    dist = math.hypot(dx, dy)
                    if dist < 10 and not s.occupied and not s.busy:
                        idx = neighbor_full_lane.slots.index(s)
                        prev_free = idx == 0 or not neighbor_full_lane.slots[idx - 1].occupied
                        next_free = idx == len(neighbor_full_lane.slots) - 1 or not neighbor_full_lane.slots[idx + 1].occupied
                        if prev_free and next_free:
                            best_slot = s
                            break
                if best_slot:
                    break

            if best_slot:
                if slot.busy:
                    print(f"[BLOCK] Slot {slot.id} is busy. Lane change aborted.")
                    return
                slot.busy = True
                best_slot.busy = True
                vehicle.previous_slot = slot
                vehicle.current_slot = best_slot
                best_slot.occupy(vehicle.id)
                lane_result = traci.simulation.convertRoad(*best_slot.center)
                traci.vehicle.changeLane(vehicle.id, lane_result[2], 50)
                print(f"[LANE CHANGE] Vehicle {vehicle.id} changed {'left' if direction == -1 else 'right'} to slot {best_slot.id}")
            else:
                print(f"[LANE CHANGE] No available slot for lane change for vehicle {vehicle.id}")

        elif action_id == 0:
            print(f"[ACTION] Action 0: Stay")
        else:
            print(f"[ACTION] Unknown action {action_id}, skipped.")
