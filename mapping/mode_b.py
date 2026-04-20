import math

class AudioField:
    def __init__(self, audio_features):
        self.features = audio_features

    def sample(self, x, y, t):
        base = self.features.get("energy", 0.5)
        return base * (math.sin(x + t) + math.cos(y - t)) * 0.5 + 0.5

class SpatialNode:
    def __init__(self, node_id, x, y, z=0.0):
        self.id = node_id
        self.x = x
        self.y = y
        self.z = z

    def evaluate(self, field, t):
        return field.sample(self.x, self.y, t)

class ModeBMapper:
    def __init__(self, nodes):
        self.nodes = nodes

    def render_frame(self, audio_features, t):
        field = AudioField(audio_features)

        frame = {}
        for node in self.nodes:
            intensity = node.evaluate(field, t)
            frame[node.id] = intensity

        return frame