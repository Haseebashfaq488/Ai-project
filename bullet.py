"""Bullet — moves 2 tiles per tick, resolves collisions in game loop."""

from constants import *


class Bullet:
    def __init__(self, x, y, direction, owner_type):
        self.x          = x
        self.y          = y
        self.dx, self.dy = direction
        self.owner_type  = owner_type   # TANK_PLAYER or enemy type
        self.alive       = True
        self._tick       = 0

    def update(self, tilemap):
        """Advance bullet 2 tiles per tick (move called twice)."""
        for _ in range(2):
            if not self.alive:
                return
            self._step(tilemap)

    def _step(self, tilemap):
        nx = self.x + self.dx
        ny = self.y + self.dy
        t  = tilemap.get(nx, ny)

        if t == BRICK:
            tilemap.destroy_brick(nx, ny)
            self.alive = False
        elif t == STEEL:
            self.alive = False
        elif t in (WATER, EAGLE):
            # Eagle collision handled in game loop
            self.x, self.y = nx, ny
            if t == EAGLE:
                self.alive = False
        elif t == EMPTY or t == FOREST:
            self.x, self.y = nx, ny
        else:
            self.alive = False   # OOB or unknown

    @property
    def is_player_bullet(self):
        return self.owner_type == TANK_PLAYER

    def rect_xy(self):
        """Returns pixel centre for drawing."""
        px = self.x * TILE_SIZE + TILE_SIZE // 2
        py = self.y * TILE_SIZE + TILE_SIZE // 2
        return px, py
