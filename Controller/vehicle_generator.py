import os
import sys
import traci

# === 设置路径 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Entity.vehicle import Vehicle, VehicleStatus
from Entity.slot import Slot
from Entity.fulllane import FullLane
from Sumo.sumo_netxml_parser import parse_netxml
from Controller.slot_generator import SlotGenerator
from Tools.utils import generate_temp_cfg

class VehicleGenerator:
    def __init__(self):
        self.global_vehicle_index = 0
        self.generated_vehicles = []

    def generate_vehicle(self, full_lane: FullLane, slot: Slot) -> Vehicle:
        veh_id = f"veh_{self.global_vehicle_index}"
        self.global_vehicle_index += 1

        vehicle = Vehicle(
            id=veh_id,
            lane=slot.lane,
            segment=slot.lane.segment_id,
            route_entry=full_lane.entry_lane.id,
            route_exit=full_lane.end_lane.id,
            full_lane=full_lane,
            position=slot.position_start,
            speed=slot.speed,
            current_slot=slot,
            status=VehicleStatus.INITIALIZING
        )
        self.generated_vehicles.append(vehicle)
        return vehicle

# === 测试入口 ===
if __name__ == "__main__":
    print("[TEST] 启动 SUMO 并测试 VehicleGenerator")

    SUMO_BINARY = "sumo-gui"
    CFG_FILE = os.path.join("Sim", "temp.sumocfg")
    NET_FILE = os.path.join("Sim", "joined_segments.net.xml")

    generate_temp_cfg()
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    # 解析路网与 FullLane
    segments, full_lanes = parse_netxml(NET_FILE)

    # 使用 SlotGenerator 生成 slot
    slot_generator = SlotGenerator()
    all_slots = slot_generator.generate_slots_for_all_full_lanes(full_lanes)

    # 获取一个测试用的 slot 和 full_lane
    test_lane = full_lanes[0]
    test_slot = test_lane.slots[0]

    # 生成车辆实体
    vg = VehicleGenerator()
    vehicle = vg.generate_vehicle(test_lane, test_slot)

    # 添加车辆到 SUMO 环境中
    traci.vehicle.add(
        vehID=vehicle.id,
        routeID="",  # 临时空 route（此测试不使用真实路径）
        typeID="DEFAULT_VEHTYPE",
        departPos=vehicle.position,
        departSpeed=vehicle.speed,
        departLane=str(test_slot.lane.index) 
    )

    print(f"[INFO] 已添加车辆 {vehicle.id} 于 lane {vehicle.lane.id}，slot 起点位置 {vehicle.position}")

    # 模拟若干步
    for step in range(300):
        traci.simulationStep()

    traci.close()
    print("[TEST] 仿真结束")
