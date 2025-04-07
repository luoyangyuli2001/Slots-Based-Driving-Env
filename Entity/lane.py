# Entity/Lane.py

class Lane:
    def __init__(self, 
                 id: str, 
                 index: int, 
                 speed: float, 
                 length: float, 
                 shape: list = None):

        self.id = id                      # 唯一的 lane ID（来自 net.xml）
        self.index = index                # 车道在 segment 中的索引（如0、1、2）
        self.speed = speed                # 限速（m/s）
        self.length = length              # 车道长度（m）
        self.shape = shape                # 车道的几何路径（点序列）
        self.segment_id = None            # 所属 segment ID，可在解析时赋值

        self.next_lane = None             # 后继车道对象（单一引用）
        self.is_entry = False             # 标记为Slot生成起始路段

    def __repr__(self):
        return f"Lane(id={self.id}, index={self.index}, speed={self.speed}, length={self.length}, next_lane={self.next_lane}, is_entry={self.is_entry})"
