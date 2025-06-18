# Controller/vehicle_controller.py

import traci
import math

class VehicleController:
    def __init__(self, vehicle_list, route_groups):
        self.vehicle_list = vehicle_list
        self.route_groups = route_groups  # 字典结构，如 {"main_forward": [...], ...}

    def step(self):
        to_remove = []

        for vehicle in self.vehicle_list:
            veh_id = vehicle.id
            slot = vehicle.current_slot

            try:
                if veh_id not in traci.vehicle.getIDList():
                    to_remove.append(vehicle)
                    continue

                # 获取 SUMO 实时状态
                front_x, front_y = traci.vehicle.getPosition(veh_id)
                heading_deg = traci.vehicle.getAngle(veh_id)
                heading_rad = math.radians(heading_deg)
                speed = traci.vehicle.getSpeed(veh_id)

                center_x = front_x - (vehicle.vehicle_type.length / 2.0) * math.cos(heading_rad)
                center_y = front_y - (vehicle.vehicle_type.length / 2.0) * math.sin(heading_rad)
                vehicle.position = (center_x, center_y)
                vehicle.heading = heading_deg
                vehicle.speed = speed

                # ======= 离开检测与解绑 =======
                current_edge = traci.vehicle.getRoadID(veh_id)
                if slot and "off_ramp" in current_edge:
                    vehicle.current_slot = None
                    print(f"[INFO] 车辆 {veh_id} 进入 {current_edge}，解绑 Slot")

                # ======= Reroute 检测逻辑 =======
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
                                    distance_to_end = lane_length - pos_on_lane

                                    if distance_to_end < 50:
                                        lane_index = int(lane_id.split("_")[-1])
                                        if lane_index != 0:
                                            new_route_id = route_list[current_index + 1]
                                            traci.vehicle.setRouteID(veh_id, new_route_id)
                                            print(f"[REROUTE] 车辆 {veh_id} 从 {route_id} -> {new_route_id}")

                # ======= 动作完成检查：释放 previous_slot =======
                if vehicle.previous_slot:
                    new_slot = vehicle.current_slot
                    dx = new_slot.center[0] - center_x
                    dy = new_slot.center[1] - center_y
                    new_slot_heading_rad = math.radians(new_slot.heading)
                    dist = dx * math.cos(new_slot_heading_rad) + dy * math.sin(new_slot_heading_rad)
                    if abs(dist) < 1:  # 阈值可调
                        vehicle.previous_slot.release()
                        print(f"[ACTION] 车辆 {vehicle.id} 动作完成，释放 slot {vehicle.previous_slot.id}")
                        vehicle.previous_slot = None

                # ======= Slot 同步控制 =======
                if vehicle.current_slot:
                    slot = vehicle.current_slot
                    dx = slot.center[0] - center_x
                    dy = slot.center[1] - center_y
                    slot_heading_rad = math.radians(slot.heading)
                    delta_along = dx * math.cos(slot_heading_rad) + dy * math.sin(slot_heading_rad)

                    tolerance = 0.1
                    max_adjust = 2.0

                    if abs(delta_along) > tolerance:
                        k_p = 0.8
                        correction = k_p * delta_along
                        correction = max(-max_adjust, min(max_adjust, correction))
                        target_speed = slot.speed + correction
                        target_speed = max(0, min(target_speed, vehicle.vehicle_type.max_speed))
                        traci.vehicle.setSpeed(veh_id, target_speed)
                    else:
                        traci.vehicle.setSpeed(veh_id, slot.speed)

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
        self.perform_action(vehicle, action_id)

    def perform_action(self, vehicle, action_id: int):
        """
        车辆动作执行函数：
        0: 保持当前 slot（默认）
        1: 前进至前一个 slot
        2: 后退至后一个 slot
        """

        slot = vehicle.current_slot
        if not slot or not hasattr(slot, "full_lane") or slot.full_lane is None:
            print(f"[SKIP] 车辆 {vehicle.id} 无绑定 slot，跳过动作 {action_id}")
            return

        full_lane = slot.full_lane
        slots = full_lane.slots

        try:
            current_pos = next(i for i, s in enumerate(slots) if s.id == slot.id)
        except StopIteration:
            print(f"[ERROR] slot {slot.id} 未在 full_lane 中找到，跳过动作")
            return

        if action_id == 1 and current_pos + 1 < len(slots):
            new_slot = slots[current_pos + 1]
            vehicle.previous_slot = slot  # 不立即释放旧 slot
            vehicle.current_slot = new_slot
            new_slot.occupy(vehicle.id)
            print(f"[ACTION] 车辆 {vehicle.id} 前进至 slot {new_slot.id}，等待动作完成")

        elif action_id == 2 and current_pos - 1 >= 0:
            new_slot = slots[current_pos - 1]
            vehicle.previous_slot = slot
            vehicle.current_slot = new_slot
            new_slot.occupy(vehicle.id)
            print(f"[ACTION] 车辆 {vehicle.id} 后退至 slot {new_slot.id}，等待动作完成")

        else:
            print(f"[ACTION] 未知或非法动作 {action_id}，当前仅支持 0-2")
