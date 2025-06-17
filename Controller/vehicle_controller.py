# Controller/vehicle_controller.py

import traci
import math

class VehicleController:
    def __init__(self, vehicle_list, route_groups):
        self.vehicle_list = vehicle_list
        self.route_groups = route_groups  # 字典结构，如 {"main_forward": [route_offramp1, route_main]}

    def step(self):
        to_remove = []

        for vehicle in self.vehicle_list:
            veh_id = vehicle.id
            slot = vehicle.current_slot

            try:
                # 若车辆已不在 SUMO 中，移除
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
                route_info = self._parse_route_id(route_id)
                if not route_info:
                    continue

                group_key = route_info["group_key"]
                if group_key not in self.route_groups:
                    continue

                route_list = self.route_groups[group_key]
                if route_id not in route_list:
                    continue

                current_index = route_list.index(route_id)
                # 若还未是最终 route，才允许 reroute
                if current_index < len(route_list) - 1:
                    # 检测是否临近 off-ramp，仍未靠边
                    route_edges = traci.vehicle.getRoute(veh_id)
                    current_edge = traci.vehicle.getRoadID(veh_id)
                    current_edge_index = route_edges.index(current_edge) if current_edge in route_edges else -1

                    if current_edge_index == len(route_edges) - 2:
                        # 到达倒数第二个 edge，检查 lane index
                        lane_id = traci.vehicle.getLaneID(veh_id)
                        lane_index = int(lane_id.split("_")[-1])
                        if lane_index != 0:
                            # 执行 reroute
                            new_route_id = route_list[current_index + 1]
                            traci.vehicle.setRouteID(veh_id, new_route_id)
                            print(f"[REROUTE] 车辆 {veh_id} 从 {route_id} -> {new_route_id}")

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

    def _parse_route_id(self, route_id: str):
        """
        将 route_id 拆分为 entry、exit 和方向等字段。
        例如 route_main_offramp1_r => entry=main, exit=offramp1, is_reverse=True
        返回 None 表示无法解析。
        """
        if not route_id.startswith("route_"):
            return None

        parts = route_id.split("_")
        if len(parts) < 3:
            return None

        entry = parts[1]
        exit = parts[2]
        is_reverse = parts[-1] == "r"
        group_key = f"{entry}_{'reverse' if is_reverse else 'forward'}"

        return {
            "entry": entry,
            "exit": exit,
            "is_reverse": is_reverse,
            "group_key": group_key
        }
