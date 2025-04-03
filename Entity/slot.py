# Entity/slot.py

class Slot:
    def __init__(self,
                 id,
                 segment_id,
                 lane_id,
                 index,
                 position_start,
                 speed,
                 length=8.0,
                 gap_to_previous=3.0,
                 occupied=False,
                 vehicle_id=None):
        
        self.id = id                            # Slot 唯一标识
        self.segment_id = segment_id            # 所属 segment ID
        self.lane_id = lane_id                  # 所属 lane ID
        self.index = index                      # 在 lane 上的序号
        
        self.position_start = position_start    # 起点
        self.length = length                    # Slot 长度，默认 8m
        self.gap_to_previous = gap_to_previous  # 与前 slot 间隔，默认 3m
        self.speed = speed

        # === 派生计算 ===
        self.position_end = self.position_start + self.length
        self.center = (self.position_start + self.position_end) / 2

        # 占用信息
        self.occupied = occupied
        self.vehicle_id = vehicle_id

    def occupy(self, vehicle_id):
        self.occupied = True
        self.vehicle_id = vehicle_id

    def release(self):
        self.occupied = False
        self.vehicle_id = None

    def __repr__(self):
        return (f"Slot(id={self.id}, lane={self.lane_id}, index={self.index}, "
                f"range=({self.position_start:.2f}-{self.position_end:.2f}), "
                f"center={self.center:.2f}, length={self.length}, gap={self.gap_to_previous}, "
                f"occupied={self.occupied}, vehicle={self.vehicle_id})")
