# Entity/Lane.py

class Lane:
    def __init__(self, id, index, speed, length, shape=None):
        self.id = id
        self.index = index
        self.speed = speed
        self.length = length
        self.shape = shape or []

    def __repr__(self):
        return f"Lane(id={self.id}, index={self.index}, speed={self.speed}, length={self.length})"
