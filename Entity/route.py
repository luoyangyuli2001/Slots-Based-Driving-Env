# Entity/route.py

class Route:
    def __init__(self, id, edges):
        self.id = id
        self.edges = edges  # List[str]

    def __repr__(self):
        return f"Route(id={self.id}, edges={self.edges})"