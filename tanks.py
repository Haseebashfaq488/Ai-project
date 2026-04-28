"""
Tanks — base class + player + all enemy AI tanks.

Module B: BFS (Basic), Greedy Best-First (Fast), A* (Armor)
Module C: Minimax + Alpha-Beta (Boss) — stub ready for later.
"""

import random
from collections import deque
from constants import *
from bullet import Bullet


# ─── Base Tank ────────────────────────────────────────────────────────────────

class Tank:
    def __init__(self, x, y, tank_type):
        self.x          = x
        self.y          = y
        self.tank_type  = tank_type
        self.direction  = DOWN
        self.hp         = HP[tank_type]
        self.max_hp     = HP[tank_type]
        self.alive      = True
        self.speed      = SPEED[tank_type]     # ticks per move
        self._move_tick = 0
        self._fire_cd   = 0                    # cooldown in ticks
        self.fire_rate  = 45                   # ticks between shots (default)
        self.bullets    = []                   # owned bullets

    # ── Shared helpers ────────────────────────────────────────────────────────

    def take_hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
        return self.alive

    def try_move(self, tilemap, dx, dy):
        nx, ny = self.x + dx, self.y + dy
        if tilemap.is_passable(nx, ny):
            self.x, self.y = nx, ny
            self.direction  = (dx, dy)
            return True
        self.direction = (dx, dy)
        return False

    def try_shoot(self):
        if self._fire_cd <= 0:
            # Only one bullet at a time per tank (for player; enemies can stack)
            bx = self.x + self.direction[0]
            by = self.y + self.direction[1]
            b  = Bullet(bx, by, self.direction, self.tank_type)
            self.bullets.append(b)
            self._fire_cd = self.fire_rate
            return b
        return None

    def tick_cooldowns(self):
        self._move_tick += 1
        if self._fire_cd > 0:
            self._fire_cd -= 1

    def can_move(self):
        return self._move_tick >= self.speed

    def reset_move_tick(self):
        self._move_tick = 0

    def line_of_sight(self, tilemap, tx, ty):
        """True if clear horizontal or vertical line of sight to (tx, ty)."""
        if self.x == tx:
            miny, maxy = sorted([self.y, ty])
            for y in range(miny + 1, maxy):
                t = tilemap.get(self.x, y)
                if t in (BRICK, STEEL, WATER):
                    return False
            return True
        if self.y == ty:
            minx, maxx = sorted([self.x, tx])
            for x in range(minx + 1, maxx):
                t = tilemap.get(x, self.y)
                if t in (BRICK, STEEL, WATER):
                    return False
            return True
        return False


# ─── Player Tank ──────────────────────────────────────────────────────────────

class PlayerTank(Tank):
    def __init__(self, x, y):
        super().__init__(x, y, TANK_PLAYER)
        self.direction  = UP
        self.fire_rate  = 15          # ticks between shots
        self.lives      = 3           # 3 lives as requested
        self._pending   = None        # direction set this frame only

    def set_direction(self, dx, dy):
        self._pending = (dx, dy)

    def update(self, tilemap, shoot=False):
        self.tick_cooldowns()
        # Only move if a direction was pressed THIS frame (pending is cleared after use)
        if self.can_move() and self._pending is not None:
            self.try_move(tilemap, *self._pending)
            self.reset_move_tick()
        # Clear pending so tank stops when key released
        self._pending = None
        if shoot:
            alive_bullets = [b for b in self.bullets if b.alive]
            if not alive_bullets:
                self.try_shoot()

    def respawn(self):
        self.x, self.y  = PLAYER_SPAWN
        self.hp          = HP[TANK_PLAYER]
        self.alive       = True
        self.direction   = UP
        self.bullets.clear()


# ─── Basic Tank (Simple Reflex + BFS) ────────────────────────────────────────

class BasicTank(Tank):
    """
    Simple Reflex Agent.
    Primary rule: shoot if player is in same row/col with clear LoS.
    Movement: follow BFS path toward Eagle; re-plan every 5s or when blocked.
    """

    def __init__(self, x, y):
        super().__init__(x, y, TANK_BASIC)
        self.direction  = DOWN
        self.fire_rate  = 60   # fires every 3 seconds at 20 FPS
        self._path      = []
        self._replan_cd = 0

    def update(self, tilemap, player):
        self.tick_cooldowns()

        # Reflex rule — shoot player if visible
        if self.line_of_sight(tilemap, player.x, player.y):
            dx = player.x - self.x
            dy = player.y - self.y
            if dx != 0:
                self.direction = (1 if dx > 0 else -1, 0)
            else:
                self.direction = (0, 1 if dy > 0 else -1)
            self.try_shoot()

        # Replan timer
        self._replan_cd -= 1
        if self._replan_cd <= 0 or not self._path:
            self._path      = tilemap.bfs_path((self.x, self.y), EAGLE_POS)
            self._replan_cd = FPS * 5

        # Wall rule — shoot brick blocking next step
        if self._path:
            nx, ny = self._path[0]
            if tilemap.get(nx, ny) == BRICK:
                self.direction = (nx - self.x, ny - self.y)
                self.try_shoot()
                return   # wait for wall to be destroyed

        # Movement
        if self.can_move():
            if self._path:
                nx, ny = self._path[0]
                if self.try_move(tilemap, nx - self.x, ny - self.y):
                    self._path.pop(0)
                else:
                    # Blocked by something other than brick — replan
                    self._path = []
            else:
                # Random fallback
                d = random.choice(DIRS)
                self.try_move(tilemap, *d)
            self.reset_move_tick()


# ─── Fast Tank (Goal-Based + Greedy Best-First) ───────────────────────────────

class FastTank(Tank):
    """
    Goal-Based Agent — single goal: destroy Eagle.
    Greedy best-first: always steps to neighbour with lowest Manhattan dist to Eagle.
    Ignores player entirely.
    """

    def __init__(self, x, y):
        super().__init__(x, y, TANK_FAST)
        self.direction = DOWN
        self.fire_rate = 30   # fires every 1.5s at 20 FPS

    def update(self, tilemap, player):
        self.tick_cooldowns()

        if self.can_move():
            best_tile = None
            best_h    = 999
            gx, gy    = EAGLE_POS
            for dx, dy in DIRS:
                nx, ny = self.x + dx, self.y + dy
                t      = tilemap.get(nx, ny)
                if t == BRICK:
                    # Shoot it down — don't detour
                    self.direction = (dx, dy)
                    self.try_shoot()
                    self.reset_move_tick()
                    return
                if tilemap.is_passable(nx, ny):
                    h = abs(nx - gx) + abs(ny - gy)
                    if h < best_h:
                        best_h, best_tile = h, (dx, dy)

            if best_tile:
                self.try_move(tilemap, *best_tile)
            self.reset_move_tick()


# ─── Armor Tank (Model-Based Reflex + A*) ─────────────────────────────────────

class ArmorTank(Tank):
    """
    Model-Based Reflex Agent — tracks hit_count internally.
    A* for navigation; retreats to steel cover on 3rd hit.
    """

    def __init__(self, x, y):
        super().__init__(x, y, TANK_ARMOR)
        self.direction   = DOWN
        self.fire_rate   = 40   # fires every 2s at 20 FPS
        self._path       = []
        self._state      = "attack"    # "attack" | "retreat" | "cover"
        self._cover_cd   = 0

    def take_hit(self):
        super().take_hit()
        if self.hp == 1 and self._state == "attack":   # 3rd hit (hp 4→1)
            self._state = "retreat"
            self._path  = []
        return self.alive

    def _find_cover(self, tilemap):
        """BFS to nearest steel wall tile (park adjacent to it)."""
        visited = {(self.x, self.y)}
        queue   = deque([((self.x, self.y), [])])
        while queue:
            (cx, cy), path = queue.popleft()
            for dx, dy in DIRS:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                if tilemap.get(nx, ny) == STEEL:
                    return path   # park on the tile before steel
                if tilemap.is_passable(nx, ny):
                    queue.append(((nx, ny), path + [(nx, ny)]))
        return []

    def update(self, tilemap, player):
        self.tick_cooldowns()

        # Shoot player if in line-of-sight
        if self.line_of_sight(tilemap, player.x, player.y):
            dx = player.x - self.x
            dy = player.y - self.y
            self.direction = (1 if dx > 0 else -1, 0) if dx != 0 else (0, 1 if dy > 0 else -1)
            self.try_shoot()

        if self._state == "retreat":
            if not self._path:
                self._path = self._find_cover(tilemap)
                if not self._path:
                    self._state = "attack"
            if self._path and self.can_move():
                nx, ny = self._path[0]
                if self.try_move(tilemap, nx - self.x, ny - self.y):
                    self._path.pop(0)
                    if not self._path:
                        self._state  = "cover"
                        self._cover_cd = FPS * 2
                self.reset_move_tick()

        elif self._state == "cover":
            self._cover_cd -= 1
            if self._cover_cd <= 0:
                self._state = "attack"
                self._path  = tilemap.astar_path((self.x, self.y), EAGLE_POS)

        else:  # attack
            if not self._path:
                self._path = tilemap.astar_path((self.x, self.y), EAGLE_POS)

            # Wall rule — shoot through brick in A* path
            if self._path:
                nx, ny = self._path[0]
                if tilemap.get(nx, ny) == BRICK:
                    self.direction = (nx - self.x, ny - self.y)
                    self.try_shoot()
                    return

            if self.can_move() and self._path:
                nx, ny = self._path[0]
                if self.try_move(tilemap, nx - self.x, ny - self.y):
                    self._path.pop(0)
                else:
                    self._path = []   # replan next tick
                self.reset_move_tick()


# ─── Factory ──────────────────────────────────────────────────────────────────

def make_enemy(tank_type, x, y):
    if tank_type == TANK_BASIC:
        return BasicTank(x, y)
    if tank_type == TANK_FAST:
        return FastTank(x, y)
    if tank_type == TANK_ARMOR:
        return ArmorTank(x, y)
    raise ValueError(f"Unknown tank type: {tank_type}")
