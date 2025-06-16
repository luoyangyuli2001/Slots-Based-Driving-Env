# Controller/vehicle_controller.py

import traci
import math

class VehicleController:
    def __init__(self, vehicle_list):
        self.vehicle_list = vehicle_list

    def step(self):
        for vehicle in self.vehicle_list:
            veh_id = vehicle.id
            slot = vehicle.current_slot

            try:
                # 获取 SUMO 动态信息
                front_x, front_y = traci.vehicle.getPosition(veh_id)
                heading_deg = traci.vehicle.getAngle(veh_id)
                heading_rad = math.radians(heading_deg)
                speed = traci.vehicle.getSpeed(veh_id)

                # === 实时更新实体类 ===
                center_x = front_x - (vehicle.vehicle_type.length / 2.0) * math.cos(heading_rad)
                center_y = front_y - (vehicle.vehicle_type.length / 2.0) * math.sin(heading_rad)

                vehicle.position = (center_x, center_y)
                vehicle.heading = heading_deg
                vehicle.speed = speed

                # === 动态同步控制逻辑 ===
                if slot:
                    dx = slot.center[0] - center_x
                    dy = slot.center[1] - center_y

                    # 投影到 slot 方向上，计算前后位置偏移
                    slot_heading_rad = math.radians(slot.heading)
                    delta_along = dx * math.cos(slot_heading_rad) + dy * math.sin(slot_heading_rad)

                    tolerance = 0.1  # 允许的同步误差
                    max_adjust = 2.0  # 最大加减速限制

                    if abs(delta_along) > tolerance:
                        # 简单比例控制（可选调节比例系数）
                        k_p = 0.8
                        correction = k_p * delta_along
                        correction = max(-max_adjust, min(max_adjust, correction))  # 限制修正速度幅度

                        target_speed = slot.speed + correction
                        target_speed = max(0, min(target_speed, vehicle.vehicle_type.max_speed))
                        traci.vehicle.setSpeed(veh_id, target_speed)
                    else:
                        # 已基本同步，直接匹配 slot 速度
                        traci.vehicle.setSpeed(veh_id, slot.speed)

            except traci.TraCIException as e:
                print(f"[WARN] 车辆 {veh_id} 控制失败: {e}")
