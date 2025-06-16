# Controller/vehicle_controller.py

import traci
import math

class VehicleController:
    def __init__(self, vehicle_list):
        self.vehicle_list = vehicle_list

    def step(self):
        to_remove = []

        for vehicle in self.vehicle_list:
            veh_id = vehicle.id
            slot = vehicle.current_slot

            try:
                # 兼容版本 SUMO: 检查车辆是否仍存在
                if veh_id not in traci.vehicle.getIDList():
                    to_remove.append(vehicle)
                    continue

                # 获取 SUMO 动态信息
                front_x, front_y = traci.vehicle.getPosition(veh_id)
                heading_deg = traci.vehicle.getAngle(veh_id)
                heading_rad = math.radians(heading_deg)
                speed = traci.vehicle.getSpeed(veh_id)

                # 实时更新实体类
                center_x = front_x - (vehicle.vehicle_type.length / 2.0) * math.cos(heading_rad)
                center_y = front_y - (vehicle.vehicle_type.length / 2.0) * math.sin(heading_rad)

                vehicle.position = (center_x, center_y)
                vehicle.heading = heading_deg
                vehicle.speed = speed

                # 离开检测与解绑逻辑
                current_edge = traci.vehicle.getRoadID(veh_id)
                if slot and ("exit" in current_edge or "off_ramp" in current_edge):
                    vehicle.current_slot = None
                    print(f"[INFO] 车辆 {veh_id} 进入 {current_edge}，已解绑 slot.")

                # 动态同步逻辑
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
                print(f"[WARN] 车辆 {veh_id} 控制失败: {e}")
                to_remove.append(vehicle)

        for v in to_remove:
            self.vehicle_list.remove(v)
            print(f"[CLEAN] 已移除消失车辆 {v.id}")
