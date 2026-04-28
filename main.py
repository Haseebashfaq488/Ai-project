"""
Battle City — Main Game Loop
Run:  python main.py

Fixes applied:
  - Player moves only while key held (set_direction called per frame from held keys)
  - Game slowed down (FPS=20, higher speed values)
  - Enemy tank touching Eagle border = instant game over
  - Bullets kill tanks on hit (any bullet kills any enemy; enemy bullets kill player)
  - Player has 3 lives
  - Enemy pool size = difficulty indicator shown in HUD
"""

import sys
import random
import pygame

from constants import *
from tilemap   import MapGenerator
from tanks     import PlayerTank, make_enemy
from renderer  import Renderer


# ─── Level enemy pools (size = difficulty) ───────────────────────────────────

LEVEL_POOLS = {
    1: [TANK_BASIC] * 8 + [TANK_FAST] * 4,          # 12 enemies — easy
    2: [TANK_BASIC] * 4 + [TANK_FAST] * 6 + [TANK_ARMOR] * 4,  # 14 — medium
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _manhattan(ax, ay, bx, by):
    return abs(ax - bx) + abs(ay - by)

def _near_eagle(x, y):
    """True if tank is on or adjacent (1 tile) to the Eagle tile."""
    ex, ey = EAGLE_POS
    return abs(x - ex) <= 1 and abs(y - ey) <= 1


# ─── Game ─────────────────────────────────────────────────────────────────────

class Game:
    def __init__(self):
        pygame.init()
        self.screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Battle City — AL2002")
        self.clock    = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.load_level(1)

    # ── Level loading ─────────────────────────────────────────────────────

    def load_level(self, level):
        self.level         = level
        self.tilemap       = MapGenerator().generate(level=level, seed=level * 42)
        self.player        = PlayerTank(*PLAYER_SPAWN)
        self.enemy_pool    = list(LEVEL_POOLS.get(level, LEVEL_POOLS[1]))
        self.total_enemies = len(self.enemy_pool)
        self.enemies       = []
        self.spawn_timer   = FPS * 1      # first spawn after 1 second
        self.game_over     = False
        self.win           = False
        self._respawn_timer = 0

    # ── Spawning ──────────────────────────────────────────────────────────

    def _spawn_enemy(self):
        if not self.enemy_pool:
            return
        active = [e for e in self.enemies if e.alive]
        if len(active) >= MAX_ACTIVE_ENEMY:
            return

        px, py = self.player.x, self.player.y
        candidates = list(ENEMY_SPAWNS)
        random.shuffle(candidates)
        for sx, sy in candidates:
            if _manhattan(sx, sy, px, py) < 10:
                continue
            if any(e.x == sx and e.y == sy and e.alive for e in self.enemies):
                continue
            tank_type = self.enemy_pool.pop(0)
            self.enemies.append(make_enemy(tank_type, sx, sy))
            return

    # ── Collision resolution ───────────────────────────────────────────────

    def _resolve_collisions(self):
        """
        Resolve:
          bullet → wall     (handled in bullet.update already)
          bullet → player   (enemy bullet hits player)
          bullet → enemy    (any bullet hits enemy — player bullets kill; enemy bullets skip friendlies)
          bullet → bullet   (both destroyed)
          bullet → eagle    (game over)
          enemy tank → eagle border  (game over)
        """
        all_bullets = (
            [b for b in self.player.bullets if b.alive] +
            [b for e in self.enemies for b in e.bullets if b.alive]
        )

        for b in all_bullets:
            if not b.alive:
                continue
            bx, by = b.x, b.y

            # ── Eagle hit by bullet ──────────────────────────────────────
            if (bx, by) == EAGLE_POS:
                b.alive = False
                self.game_over = True
                return

            # ── Enemy bullet hits player ─────────────────────────────────
            if (not b.is_player_bullet
                    and self.player.alive
                    and bx == self.player.x
                    and by == self.player.y):
                b.alive = False
                self._handle_player_hit()
                continue

            # ── Any bullet hits an enemy ─────────────────────────────────
            # Player bullets kill enemies; enemy bullets skip fellow enemies
            if b.is_player_bullet:
                for e in self.enemies:
                    if e.alive and bx == e.x and by == e.y:
                        b.alive = False
                        e.take_hit()   # reduces HP; sets alive=False if hp<=0
                        break

        # ── Bullet vs bullet ────────────────────────────────────────────
        for i, b1 in enumerate(all_bullets):
            for b2 in all_bullets[i + 1:]:
                if b1.alive and b2.alive and b1.x == b2.x and b1.y == b2.y:
                    b1.alive = b2.alive = False

        # ── Enemy tank reaches Eagle border → game over ──────────────────
        for e in self.enemies:
            if e.alive and _near_eagle(e.x, e.y):
                self.game_over = True
                return

    def _handle_player_hit(self):
        self.player.alive   = False
        self.player.lives  -= 1
        self._respawn_timer = FPS * 2   # 2-second respawn pause

    # ── Main loop ─────────────────────────────────────────────────────────

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.renderer.tick()

            # ── Events ────────────────────────────────────────────────────
            shoot_this_frame = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key == pygame.K_SPACE:
                        shoot_this_frame = True
                    if (self.game_over or self.win) and event.key == pygame.K_RETURN:
                        self.load_level(1)

            # ── Game-over / win overlay ────────────────────────────────────
            if self.game_over or self.win:
                kills_left = len(self.enemy_pool) + len([e for e in self.enemies if e.alive])
                self.renderer.draw(self.tilemap, self.player, self.enemies, [], self.level, kills_left)
                msg = "YOU WIN!" if self.win else "GAME OVER"
                col = YELLOW if self.win else RED
                self.renderer.draw_overlay(msg, "Press ENTER to restart", col)
                continue

            # ── Read held keys for movement (movement only while held) ────
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if   keys[pygame.K_w] or keys[pygame.K_UP]:     dy = -1
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:   dy =  1
            elif keys[pygame.K_a] or keys[pygame.K_LEFT]:   dx = -1
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:  dx =  1

            # set_direction is called every frame — player.update() clears
            # _pending after using it, so the tank stops the moment no key held
            if dx or dy:
                self.player.set_direction(dx, dy)

            # ── Respawn ────────────────────────────────────────────────────
            if not self.player.alive:
                self._respawn_timer -= 1
                if self._respawn_timer <= 0:
                    if self.player.lives <= 0:
                        self.game_over = True
                    else:
                        self.player.respawn()

            # ── Update player ──────────────────────────────────────────────
            if self.player.alive:
                self.player.update(self.tilemap, shoot=shoot_this_frame)

            # ── Spawn enemies ──────────────────────────────────────────────
            self.spawn_timer -= 1
            if self.spawn_timer <= 0 and self.enemy_pool:
                self._spawn_enemy()
                self.spawn_timer = FPS * 3   # new enemy every 3 seconds

            # ── Update enemies ─────────────────────────────────────────────
            for e in self.enemies:
                if e.alive:
                    e.update(self.tilemap, self.player)

            # ── Move bullets ───────────────────────────────────────────────
            all_bullets = (
                self.player.bullets +
                [b for e in self.enemies for b in e.bullets]
            )
            for b in all_bullets:
                if b.alive:
                    b.update(self.tilemap)

            # ── Resolve all collisions ─────────────────────────────────────
            self._resolve_collisions()

            # ── Prune dead objects ─────────────────────────────────────────
            self.player.bullets = [b for b in self.player.bullets if b.alive]
            for e in self.enemies:
                e.bullets = [b for b in e.bullets if b.alive]
            self.enemies = [e for e in self.enemies if e.alive]

            # ── Win / level-advance check ──────────────────────────────────
            kills_left = len(self.enemy_pool) + len([e for e in self.enemies if e.alive])
            if kills_left == 0 and not self.game_over:
                if self.level < max(LEVEL_POOLS.keys()):
                    self.load_level(self.level + 1)
                else:
                    self.win = True

            # ── Render ────────────────────────────────────────────────────
            self.renderer.draw(
                self.tilemap, self.player, self.enemies, all_bullets,
                self.level, kills_left
            )


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    Game().run()

