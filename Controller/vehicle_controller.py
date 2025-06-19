# Controller/vehicle_controller.py

import traci
import math

class VehicleController:
    def __init__(self, vehicle_list, route_groups):
        self.vehicle_list = vehicle_list
        self.route_groups = route_groups

    def step(self):
        to_remove = []

        for vehicle in self.vehicle_list:
            veh_id = vehicle.id
            slot = vehicle.current_slot

            try:
                if veh_id not in traci.vehicle.getIDList():
                    to_remove.append(vehicle)
                    continue

                front_x, front_y = traci.vehicle.getPosition(veh_id)
                heading_deg = traci.vehicle.getAngle(veh_id)
                heading_rad = math.radians(heading_deg)
                speed = traci.vehicle.getSpeed(veh_id)

                center_x = front_x - (vehicle.vehicle_type.length / 2.0) * math.cos(heading_rad)
                center_y = front_y - (vehicle.vehicle_type.length / 2.0) * math.sin(heading_rad)
                vehicle.position = (center_x, center_y)
                vehicle.heading = heading_deg
                vehicle.speed = speed

                # ======= 离开检测 =======
                current_edge = traci.vehicle.getRoadID(veh_id)
                if vehicle.current_slot and "off_ramp" in current_edge:
                    vehicle.current_slot.release()
                    vehicle.current_slot.busy = False
                    vehicle.current_slot = None

                    if vehicle.previous_slot:
                        vehicle.previous_slot.release()
                        vehicle.previous_slot.busy = False
                        vehicle.previous_slot = None

                    print(f"[INFO] 车辆 {veh_id} 进入 {current_edge}，解绑 Slot")

                # ======= 动作完成检测 =======
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
                        print(f"[ACTION] 车辆 {vehicle.id} 动作完成，释放 slot {vehicle.previous_slot.id}")
                        vehicle.previous_slot = None

                # ======= Slot 同步控制 =======
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

                # ======= Reroute 逻辑 =======
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
                                            print(f"[REROUTE] 车辆 {veh_id} 从 {route_id} -> {new_route_id}")

            except traci.TraCIException as e:
                print(f"[WARN] 控制失败 {veh_id}: {e}")
                to_remove.append(vehicle)

        for v in to_remove:
            self.vehicle_list.remove(v)
            print(f"[CLEAN] 移除车辆 {v.id}")

    def _get_vehicle_by_slot(self, slot):
        for vehicle in self.vehicle_list:
            if vehicle.id == slot.vehicle_id:
                return vehicle
        return None

    def execute_slot_action(self, slot, action_id: int):
        vehicle_id = slot.vehicle_id
        if vehicle_id is None:
            print(f"[SKIP] slot {slot.id} 无车辆绑定，无法执行动作 {action_id}")
            return
        vehicle = self._get_vehicle_by_slot(slot)
        if vehicle is None:
            print(f"[ERROR] slot {slot.id} 没有找到绑定的车辆，跳过执行动作 {action_id}")
            return

        self.perform_action(vehicle, action_id)


    def perform_action(self, vehicle, action_id: int):
        slot = vehicle.current_slot
        if not slot or not hasattr(slot, "full_lane") or slot.full_lane is None:
            print(f"[SKIP] 车辆 {vehicle.id} 无绑定 slot，跳过动作 {action_id}")
            return

        if slot.busy:
            print(f"[BLOCK] 当前 slot {slot.id} 忙碌，跳过动作")
            return

        full_lane = slot.full_lane
        slots = full_lane.slots
        try:
            current_pos = next(i for i, s in enumerate(slots) if s.id == slot.id)
        except StopIteration:
            print(f"[ERROR] slot {slot.id} 未在 full_lane 中找到")
            return

        if action_id == 1 and current_pos + 1 < len(slots):  # 前进
            new_slot = slots[current_pos + 1]
            if new_slot.occupied or new_slot.busy:
                print(f"[BLOCK] slot {new_slot.id} 忙碌或被占用，跳过前进")
                return
            slot.busy = True
            new_slot.busy = True
            vehicle.previous_slot = slot
            vehicle.current_slot = new_slot
            new_slot.occupy(vehicle.id)
            print(f"[ACTION] 车辆 {vehicle.id} 前进至 slot {new_slot.id}")

        elif action_id == 2 and current_pos - 1 >= 0:  # 后退
            new_slot = slots[current_pos - 1]
            if new_slot.occupied or new_slot.busy:
                print(f"[BLOCK] slot {new_slot.id} 忙碌或被占用，跳过后退")
                return
            slot.busy = True
            new_slot.busy = True
            vehicle.previous_slot = slot
            vehicle.current_slot = new_slot
            new_slot.occupy(vehicle.id)
            print(f"[ACTION] 车辆 {vehicle.id} 后退至 slot {new_slot.id}")

        elif action_id in [3, 4]:  # 变道
            lane_id = traci.vehicle.getLaneID(vehicle.id)
            if "ramp" in lane_id.lower():
                print(f"[INFO] 车辆 {vehicle.id} 当前在 ramp 上，禁止变道")
                return
            if ":" in lane_id.lower():
                print(f"[INFO] 车辆 {vehicle.id} 当前在 内部边 中 禁止变道")
                return

            direction = -1 if action_id == 3 else 1  # -1: 左变道, +1: 右变道
            current_x = slot.center[0]

            candidate_full_lanes = []
            for start_x, end_x, neighbor, neighbor_direction in full_lane.neighbor_full_lanes:
                if neighbor_direction == direction and start_x <= current_x <= end_x:
                    candidate_full_lanes.append(neighbor)

            if not candidate_full_lanes:
                print(f"[LANE CHANGE] 车辆 {vehicle.id} 无邻接 FullLane 可用于 {'左' if direction == -1 else '右'}变道")
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
                    print(f"[BLOCK] slot {slot.id} 忙碌，跳过变道")
                    return
                slot.busy = True
                best_slot.busy = True
                vehicle.previous_slot = slot
                vehicle.current_slot = best_slot
                best_slot.occupy(vehicle.id)
                lane_result = traci.simulation.convertRoad(*best_slot.center)
                traci.vehicle.changeLane(vehicle.id, lane_result[2], 50)
                print(f"[LANE CHANGE] 车辆 {vehicle.id} 向 {'左' if direction == -1 else '右'} 变道至 slot {best_slot.id}")
            else:
                print(f"[LANE CHANGE] 车辆 {vehicle.id} 未找到可用变道 slot")

        elif action_id == 0:
            print(f"[Action] 动作 0, 维持不动")
        else:
            if action_id == 1:
                print(f"[Action] 动作 1， 前方无可用 slot")
            elif action_id == 2:
                print(f"[Action] 动作 2， 前方无可用 slot")
            else:
                print(f"[ACTION] 未知动作 {action_id}，跳过")
