# Controller/merge_controller.py

class MergeController:
    def __init__(self, full_lanes, ramp_to_fulllane_map, safety_gap=5.0):
        """
        full_lanes: List of FullLane 实体
        ramp_to_fulllane_map: dict, 例如 {'on_ramp1': 'e3_0'}
        safety_gap: 允许绑定的最大合流距离阈值（单位: 米）
        """
        self.full_lanes = full_lanes
        self.ramp_map = ramp_to_fulllane_map
        self.full_lane_dict = {fl.start_lane_id: fl for fl in full_lanes}
        self.safety_gap = safety_gap


    def step(self, vehicle_list):
        for veh in vehicle_list:
            if veh.current_slot is not None:
                continue  # 已绑定 slot，无需再次绑定

            route_entry = veh.route.edges[0]
            for ramp_edge, target_start_lane in self.ramp_map.items():
                if route_entry.startswith(ramp_edge):

                    fl = self.full_lane_dict.get(target_start_lane)

                    if not fl:
                        continue

                    veh_pos = veh.get_front_position()  # 注意：你实体类已实现此方法
                    candidate_slot = self._find_nearest_slot(fl, veh_pos)

                    if candidate_slot:
                        veh.current_slot = candidate_slot
                        candidate_slot.occupy(veh.id)
                        print(f"[MERGE] 车辆 {veh.id} 成功绑定 slot {candidate_slot.id}")

    def _find_nearest_slot(self, full_lane, veh_pos):
        best_slot = None
        best_dist = float("inf")
        for slot in full_lane.slots:
            if not slot.occupied:
                dist = self._euclidean_distance(veh_pos, slot.center)
                if dist < best_dist and dist < self.safety_gap:
                    best_dist = dist
                    best_slot = slot
        return best_slot

    @staticmethod
    def _euclidean_distance(p1, p2):
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
