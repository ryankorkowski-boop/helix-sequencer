"""Layer compositor for animated preview sprites."""


class SpriteCompositor:
    def __init__(self, sprites):
        self.sprites = sprites

    def layers_for_pose(self, pose):
        return [self.sprites.get(layer) for layer in pose.layers]

    def compose(self, pose):
        """Return ordered layers for rendering backend.

        Actual alpha compositing is delegated to the renderer backend.
        """
        return self.layers_for_pose(pose)
