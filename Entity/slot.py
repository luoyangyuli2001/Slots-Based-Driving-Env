# Entity/slot.py

class Slot:
    def __init__(self,
                 id,
                 segment_id,
                 lane,
                 index,
                 position_start,
                 speed,
                 length=8.0,
                 gap_to_previous=3.0,
                 vehicle_id=None,
                 heading=0.0,
                 full_lane=None):
        
        self.id = id
        self.segment_id = segment_id
        self.lane = lane
        self.index = index
        self.position_start = position_start
        self.length = length
        self.gap_to_previous = gap_to_previous
        self.speed = speed
        self.position_end = self.position_start + self.length
        self.center = (self.position_start + self.position_end) / 2
        self.heading = heading  # degree 方向角（相对于SUMO坐标系）
        self.occupied = False #是否有车辆
        self.vehicle_id = vehicle_id
        self.full_lane = full_lane
        self.busy = False #是否正在被某个动作占用

    def occupy(self, vehicle_id):
        self.occupied = True
        self.vehicle_id = vehicle_id

    def release(self):
        self.occupied = False
        self.vehicle_id = None

    def __repr__(self):
        return (f"Slot(id={self.id}, lane={self.lane.id}, index={self.index}, "
                f"range=({self.position_start:.2f}-{self.position_end:.2f}), "
                f"center={self.center:.2f}, heading={self.heading:.2f}, "
                f"occupied={self.occupied}, vehicle={self.vehicle_id})")
