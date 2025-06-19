# Controller/merge_controller.py

class MergeController:
    def __init__(self, full_lanes, ramp_to_fulllane_map, safety_gap=5.0):
        """
        Initialize the MergeController.

        Args:
            full_lanes (list): A list of FullLane instances representing main road lanes.
            ramp_to_fulllane_map (dict): Mapping from ramp edge IDs to target start lane IDs on the main road.
                Example: {'on_ramp1': 'e3_0'}
            safety_gap (float): Maximum allowed distance (in meters) between the merging vehicle and slot center
                to allow binding.
        """
        self.full_lanes = full_lanes
        self.ramp_map = ramp_to_fulllane_map
        self.full_lane_dict = {fl.start_lane_id: fl for fl in full_lanes}
        self.safety_gap = safety_gap

    def step(self, vehicle_list):
        """
        Perform a merging step for a list of vehicles.

        For each vehicle entering from a ramp, find the closest available slot on the corresponding
        main road lane within the safety distance, and bind it.

        Args:
            vehicle_list (list): List of Vehicle instances to check for merging.
        """
        for veh in vehicle_list:
            if veh.current_slot is not None:
                continue  # Already bound to a slot, skip

            route_entry = veh.route.edges[0]
            for ramp_edge, target_start_lane in self.ramp_map.items():
                if route_entry.startswith(ramp_edge):

                    fl = self.full_lane_dict.get(target_start_lane)
                    if not fl:
                        continue  # Skip if target lane is not found

                    veh_pos = veh.get_front_position()  # Assumes vehicle has this method implemented
                    candidate_slot = self._find_nearest_slot(fl, veh_pos)

                    if candidate_slot:
                        veh.current_slot = candidate_slot
                        candidate_slot.occupy(veh.id)
                        candidate_slot.busy = True
                        print(f"[MERGE] Vehicle {veh.id} successfully bound to slot {candidate_slot.id}")

    def _find_nearest_slot(self, full_lane, veh_pos):
        """
        Find the nearest available slot on the given full lane within the safety gap.

        Args:
            full_lane (FullLane): The full lane to search for available slots.
            veh_pos (tuple): The (x, y) position of the vehicle front.

        Returns:
            Slot: The closest unoccupied slot within the safety gap, or None if none found.
        """
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
        """
        Compute the Euclidean distance between two 2D points.

        Args:
            p1 (tuple): (x, y) coordinates of point 1.
            p2 (tuple): (x, y) coordinates of point 2.

        Returns:
            float: The Euclidean distance.
        """
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
