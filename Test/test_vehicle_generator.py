# Test/test_vehicle_generator.py

import os
import sys
import time
import random
import traci
import math
from collections import defaultdict

# 设置路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Sumo.sumo_netxml_parser import NetXMLParser
from Sumo.sumo_routexml_parser import RouteXMLParser
from Tools.utils import generate_temp_cfg
from Controller.slot_generator import SlotGenerator
from Controller.slot_controller import SlotController
from Controller.vehicle_generator import VehicleGenerator

# SUMO 配置路径
SUMO_BINARY = "sumo-gui"
NET_FILE = "Sim/test.net.xml"
ROUTE_FILE = "Sim/test.rou.xml"
CFG_FILE = "Sim/temp.sumocfg"

if __name__ == "__main__":
    print("[TEST] 启动 SUMO，并生成 Slot 与车辆")
    generate_temp_cfg()

    # 加载 FullLane 与 Route
    net_parser = NetXMLParser(NET_FILE)
    full_lanes = net_parser.build_full_lanes()
    lane_dict = net_parser.lane_dict

    route_parser = RouteXMLParser(ROUTE_FILE)
    routes = route_parser.get_routes()
    default_vtype = route_parser.get_default_vehicle_type()

    # 启动 SUMO
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    # 初始化 Slot 系统
    slot_generator = SlotGenerator()
    slot_generator.generate_slots_for_all_full_lanes(full_lanes)
    slot_controller = SlotController(slot_generator, full_lanes)

    # 初始化 Vehicle 系统
    vehicle_generator = VehicleGenerator(routes, default_vtype)

    rendered_slots = set()
    rendered_vehicles = set()

    # 初始 slot 可视化
    for fl in full_lanes:
        for slot in fl.slots:
            if slot.center:
                x, y = slot.center
                try:
                    traci.poi.add(slot.id, x, y, color=(255, 0, 0), layer=5)
                    traci.poi.setParameter(slot.id, "label", slot.id)
                    rendered_slots.add(slot.id)
                except:
                    pass

    print("[TEST] 开始动态添加车辆并更新 slot")
    for step in range(500):
        traci.simulationStep()

        # 推进 slot 并获取移除项
        removed = slot_controller.step()

        # 更新现有 slot 坐标或添加新 slot
        for fl in full_lanes:
            for slot in fl.slots:
                if slot.center:
                    if slot.id in rendered_slots:
                        try:
                            traci.poi.setPosition(slot.id, *slot.center)
                        except:
                            pass
                    else:
                        try:
                            traci.poi.add(slot.id, *slot.center, color=(255, 0, 0), layer=5)
                            traci.poi.setParameter(slot.id, "label", slot.id)
                            traci.poi.setParameter(slot.id, "imgWidth", "5")
                            traci.poi.setParameter(slot.id, "imgHeight", "5")
                            rendered_slots.add(slot.id)
                        except Exception as e:
                            print(f"[WARN] 新 slot {slot.id} 添加失败: {e}")

        # 移除并补充 slot
        for old_slot, full_lane in removed:
            try:
                traci.poi.remove(old_slot.id)
                rendered_slots.discard(old_slot.id)
            except:
                pass

        # 每 30 步添加一个车辆（仅示范）
        if step % 30 == 0:
            selected_route = vehicle_generator.select_random_route()
            entry_edge = selected_route.edges[0]

            candidate_lanes = [lane for lane in lane_dict.values() if lane.id.startswith(entry_edge + "_")]
            if not candidate_lanes:
                print(f"[WARN] 无法在 edge {entry_edge} 上找到可用 lane")
                continue
            
            selected_lane = random.choice(candidate_lanes)

            # 检查是否为 ramp
            is_ramp = "ramp" in selected_lane.id.lower()

            vehicle = None
            if is_ramp:
                vehicle = vehicle_generator.generate_vehicle(slot=None, route=selected_route)
            else:
                # 查找 full lane 并分配 slot
                target_fl = None
                for fl in full_lanes:
                    if fl.start_lane_id == selected_lane.id:
                        target_fl = fl
                        break

                if not target_fl or not target_fl.slots:
                    print(f"[INFO] 未找到合适 FullLane 或无可用 slot：{selected_lane.id}")
                    continue

                slot = target_fl.slots[0]
                if getattr(slot, "occupied", False):
                    print(f"[INFO] slot {slot.id} 已被占用，跳过生成")
                    continue

                vehicle = vehicle_generator.generate_vehicle(slot=slot, route=selected_route)

            if vehicle and vehicle.id not in rendered_vehicles:
                try:
                    if vehicle.current_slot:
                        slot = vehicle.current_slot
                        traci.vehicle.add(
                            vehID=vehicle.id,
                            routeID=vehicle.route.id,
                            typeID=vehicle.vehicle_type.id,
                            departPos=str(slot.position_start),
                            departSpeed=str(slot.speed),
                            departLane=slot.lane.id.split("_")[-1]
                        )
                        # 禁用变道
                        traci.vehicle.setLaneChangeMode(vehicle.id, 256)

                        # 禁用自动加速
                        # 默认（所有检查开启）-> [0 0 1 1 1 1 1] -> 速度模式 = 31
                        # 大多数检查关闭（遗留）-> [0 0 0 0 0 0 0] -> 速度模式 = 0
                        # 所有检查均关闭 -> [1 1 0 0 0 0 0] -> 速度模式 = 96
                        # 禁用通行权检查 -> [0 1 1 0 1 1 1] -> 速度模式 = 55
                        # 闯红灯 [0 0 0 0 1 1 1] = 7（也需要 setSpeed 或 slowDown）
                        # 即使路口有人，也要闯红灯 [0 1 0 0 1 1 1] = 39（也需要 setSpeed 或 slowDown）

                        traci.vehicle.setSpeedMode(vehicle.id, 0)
                        # 指定速度为车道速度
                        traci.vehicle.setSpeed(vehicle.id, vehicle.speed)

                        # === 使用slot.heading进行精确放置 ===
                        vehicle_length = vehicle.vehicle_type.length
                        heading_rad = math.radians(slot.heading)

                        x_center, y_center = slot.center
                        x_front = x_center + (vehicle_length / 2.0) * math.cos(heading_rad)
                        y_front = y_center + (vehicle_length / 2.0) * math.sin(heading_rad)

                        edge_id = slot.lane.id.rsplit("_", 1)[0]
                        lane_index = int(slot.lane.id.rsplit("_", 1)[-1])

                        # 精确定位到 slot 中心
                        edge_id = slot.lane.id.rsplit("_", 1)[0]
                        lane_index = int(slot.lane.id.rsplit("_", 1)[-1])
                        traci.vehicle.moveToXY(
                            vehicle.id,
                            edgeID=edge_id,
                            laneIndex=lane_index,
                            x=x_front,
                            y=y_front,
                            angle=slot.heading,
                            keepRoute=1
                        )
                    else:
                        traci.vehicle.add(
                            vehID=vehicle.id,
                            routeID=vehicle.route.id,
                            typeID=vehicle.vehicle_type.id,
                            departLane=selected_lane.id.split("_")[-1],
                            departSpeed="0",
                            departPos="0"
                        )
                        traci.vehicle.setLaneChangeMode(vehicle.id, 256)
                        traci.vehicle.setSpeedMode(vehicle.id, 0)

                    rendered_vehicles.add(vehicle.id)
                    print(f"[ADD VEH] {vehicle.id} 添加成功，路线 {selected_route.id}")
                except Exception as e:
                    print(f"[WARN] 添加 {vehicle.id} 失败：{e}")

    traci.close()
    print("[TEST] 测试完成")
