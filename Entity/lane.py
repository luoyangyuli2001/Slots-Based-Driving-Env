# Entity/Lane.py

class Lane:
    def __init__(self, id, index, speed, shape, from_node=None, to_node=None, is_internal=False):
        self.id = id                           # lane的唯一标识
        self.index = index                     # 车道在edge内的编号（左起0）
        self.speed = speed                     # 限速 m/s
        self.shape = self._parse_shape(shape)  # [(x1,y1), (x2,y2), ...] 解析成点列
        self.from_node = from_node             # 起点节点
        self.to_node = to_node                 # 终点节点
        self.is_internal = is_internal         # 是否为internal lane

        # 未来扩展字段
        self.segment_id = None                    # 归属的Segment（现在可以留空）
        self.connected_lanes = []              # 与本lane直接连接的其他lanes（用于动态查找）
    
    def _parse_shape(self, shape_str):
        """将SUMO的shape字符串转成[(x,y), (x,y)]"""
        points = []
        for pair in shape_str.strip().split():
            x, y = map(float, pair.split(','))
            points.append((x, y))
        return points

    def __repr__(self):
        return f"Lane(id={self.id}, from={self.from_node}, to={self.to_node}, internal={self.is_internal})"

