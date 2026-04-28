"""
Renderer — draws the tile grid, tanks, bullets, and HUD panel.
Pure pygame drawing; no game logic lives here.
"""

import pygame
from constants import *


def _darken(col, factor=0.6):
    return tuple(max(0, int(c * factor)) for c in col)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font_lg = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_sm = pygame.font.SysFont("monospace", 14)
        self.font_xs = pygame.font.SysFont("monospace", 11)
        self._anim   = 0

    def tick(self):
        self._anim = (self._anim + 1) % 60

    # ── Main draw call ─────────────────────────────────────────────────────

    def draw(self, tilemap, player, enemies, bullets, level, kills_left):
        self.screen.fill(DARK_GREY)
        self._draw_grid(tilemap)
        self._draw_bullets(bullets)
        self._draw_enemies(enemies)
        self._draw_player(player)
        self._draw_hud(player, level, kills_left)
        pygame.display.flip()

    # ── Grid ──────────────────────────────────────────────────────────────

    def _draw_grid(self, tm):
        T = TILE_SIZE
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = tm.get(x, y)
                rx   = x * T
                ry   = y * T
                r    = pygame.Rect(rx, ry, T, T)

                if tile == EMPTY:
                    pygame.draw.rect(self.screen, DARK_GREY, r)

                elif tile == BRICK:
                    pygame.draw.rect(self.screen, BRICK_RED, r)
                    # mortar lines
                    pygame.draw.line(self.screen, BRICK_DARK, (rx, ry + T//2), (rx + T, ry + T//2), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx + T//2, ry), (rx + T//2, ry + T//2), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx, ry + T//2 + 1), (rx + T//4, ry + T//2 + 1), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx + T//4*3, ry + T//2 + 1), (rx + T, ry + T//2 + 1), 1)

                elif tile == STEEL:
                    pygame.draw.rect(self.screen, STEEL_BLUE, r)
                    pygame.draw.rect(self.screen, (100, 130, 190), r, 1)
                    pygame.draw.line(self.screen, (120, 150, 210), (rx+2, ry+2), (rx+T-2, ry+2), 1)

                elif tile == WATER:
                    col = WATER_BLUE if (self._anim // 15) % 2 == 0 else WATER_LIGHT
                    pygame.draw.rect(self.screen, col, r)
                    # wave lines
                    for i in range(2):
                        wy = ry + 6 + i * 10
                        pygame.draw.line(self.screen, WATER_LIGHT, (rx+2, wy), (rx + T//2, wy - 2), 1)
                        pygame.draw.line(self.screen, WATER_LIGHT, (rx + T//2, wy - 2), (rx + T - 2, wy), 1)

                elif tile == FOREST:
                    pygame.draw.rect(self.screen, DARK_GREEN, r)
                    pygame.draw.circle(self.screen, GREEN, (rx + T//4, ry + T//2), T//4)
                    pygame.draw.circle(self.screen, GREEN, (rx + T//2, ry + T//3), T//4)
                    pygame.draw.circle(self.screen, GREEN, (rx + T//4*3, ry + T//2), T//4)

                elif tile == EAGLE:
                    pygame.draw.rect(self.screen, DARK_GREY, r)
                    # Eagle symbol (simple flag)
                    pygame.draw.polygon(self.screen, GOLD, [
                        (rx + T//2, ry + 2),
                        (rx + T - 4, ry + T//2),
                        (rx + T//2, ry + T//3 * 2),
                        (rx + 4, ry + T//2),
                    ])
                    pygame.draw.circle(self.screen, WHITE, (rx + T//2, ry + T//2), 4, 2)

    # ── Tanks ─────────────────────────────────────────────────────────────

    TANK_COLORS = {
        TANK_PLAYER: (YELLOW, (200, 180, 40)),
        TANK_BASIC:  ((80, 180, 80), (40, 120, 40)),
        TANK_FAST:   ((80, 200, 220), (40, 140, 160)),
        TANK_ARMOR:  ((190, 100, 60), (130, 60, 30)),
        TANK_BOSS:   (RED, (140, 20, 20)),
    }

    def _draw_tank(self, tank, color_pair):
        T      = TILE_SIZE
        body_c, dark_c = color_pair
        rx     = tank.x * T
        ry     = tank.y * T

        # Flicker when armor tank is hit
        if tank.tank_type == TANK_ARMOR and tank.hp < tank.max_hp:
            if (self._anim // 3) % 2 == 1:
                body_c = WHITE

        # Body
        body = pygame.Rect(rx + 3, ry + 3, T - 6, T - 6)
        pygame.draw.rect(self.screen, body_c, body, border_radius=3)
        pygame.draw.rect(self.screen, dark_c, body, 1, border_radius=3)

        # Tracks (side bars)
        pygame.draw.rect(self.screen, dark_c, (rx + 1, ry + 4, 3, T - 8))
        pygame.draw.rect(self.screen, dark_c, (rx + T - 4, ry + 4, 3, T - 8))

        # Barrel
        dx, dy = tank.direction
        cx, cy = rx + T // 2, ry + T // 2
        bx     = cx + dx * (T // 2 - 2)
        by_    = cy + dy * (T // 2 - 2)
        pygame.draw.line(self.screen, dark_c, (cx, cy), (bx, by_), 3)

        # HP bar for armor tank
        if tank.tank_type == TANK_ARMOR:
            bar_w = T - 6
            filled = int(bar_w * tank.hp / tank.max_hp)
            pygame.draw.rect(self.screen, RED,   (rx + 3, ry - 4, bar_w, 3))
            pygame.draw.rect(self.screen, GREEN,  (rx + 3, ry - 4, filled, 3))

    def _draw_player(self, player):
        if not player.alive:
            return
        self._draw_tank(player, self.TANK_COLORS[TANK_PLAYER])

    def _draw_enemies(self, enemies):
        for e in enemies:
            if e.alive:
                colors = self.TANK_COLORS.get(e.tank_type, ((150, 150, 150), (80, 80, 80)))
                self._draw_tank(e, colors)

    # ── Bullets ───────────────────────────────────────────────────────────

    def _draw_bullets(self, bullets):
        for b in bullets:
            if not b.alive:
                continue
            px, py = b.rect_xy()
            col    = YELLOW if b.is_player_bullet else (255, 100, 50)
            pygame.draw.circle(self.screen, col, (px, py), 3)
            # Tracer
            tx = px - b.dx * 5
            ty = py - b.dy * 5
            pygame.draw.line(self.screen, _darken(col), (tx, ty), (px, py), 1)

    # ── HUD Panel ─────────────────────────────────────────────────────────

    def _draw_hud(self, player, level, kills_left):
        px = GRID_SIZE * TILE_SIZE
        pw = PANEL_WIDTH
        ph = SCREEN_H
        pygame.draw.rect(self.screen, HUD_BG, (px, 0, pw, ph))
        pygame.draw.line(self.screen, HUD_LINE, (px, 0), (px, ph), 2)

        y = 16
        # Title
        surf = self.font_lg.render("BATTLE", True, YELLOW)
        self.screen.blit(surf, (px + (pw - surf.get_width()) // 2, y))
        y += 26
        surf = self.font_lg.render("CITY", True, YELLOW)
        self.screen.blit(surf, (px + (pw - surf.get_width()) // 2, y))
        y += 34

        pygame.draw.line(self.screen, HUD_LINE, (px + 10, y), (px + pw - 10, y))
        y += 14

        def label(text, val, col=WHITE):
            nonlocal y
            s1 = self.font_sm.render(text, True, MID_GREY)
            s2 = self.font_sm.render(str(val), True, col)
            self.screen.blit(s1, (px + 12, y))
            self.screen.blit(s2, (px + pw - s2.get_width() - 12, y))
            y += 22

        label("LEVEL", level, YELLOW)

        # Difficulty label based on total enemies (shown as text)
        diff_levels = {1: "EASY", 2: "MEDIUM", 3: "HARD"}
        diff_text   = diff_levels.get(level, "???")
        diff_col    = {1: GREEN, 2: ORANGE, 3: RED}.get(level, WHITE)
        label("DIFF", diff_text, diff_col)

        label("ENEMIES", kills_left, ORANGE)
        y += 4

        # Lives as hearts
        pygame.draw.line(self.screen, HUD_LINE, (px + 10, y), (px + pw - 10, y))
        y += 12
        s = self.font_sm.render("LIVES", True, MID_GREY)
        self.screen.blit(s, (px + 12, y))
        y += 20
        hearts = ""
        for i in range(3):
            hearts += "♥ " if i < player.lives else "♡ "
        hcol = RED if player.lives > 1 else (255, 80, 80)
        hs = self.font_lg.render(hearts.strip(), True, hcol)
        self.screen.blit(hs, (px + (pw - hs.get_width()) // 2, y))
        y += 30

        # HP bar (for future multi-hp player)
        pygame.draw.line(self.screen, HUD_LINE, (px + 10, y), (px + pw - 10, y))
        y += 14

        # Enemy tank type legend
        s = self.font_sm.render("TANK TYPES", True, MID_GREY)
        self.screen.blit(s, (px + 12, y)); y += 18
        legend = [
            ("■ Basic",  (80, 180, 80)),
            ("■ Fast",   (80, 200, 220)),
            ("■ Armor",  (190, 100, 60)),
        ]
        for txt, col in legend:
            s = self.font_xs.render(txt, True, col)
            self.screen.blit(s, (px + 16, y)); y += 14

        y += 6
        pygame.draw.line(self.screen, HUD_LINE, (px + 10, y), (px + pw - 10, y))
        y += 12

        # Controls
        for line in ["[WASD] Move", "[SPACE] Fire", "[ESC]  Quit"]:
            s = self.font_xs.render(line, True, MID_GREY)
            self.screen.blit(s, (px + 12, y))
            y += 15

    # ── Overlay screens ───────────────────────────────────────────────────

    def draw_overlay(self, text, sub="", color=YELLOW):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        big = self.font_lg.render(text, True, color)
        self.screen.blit(big, (SCREEN_W // 2 - big.get_width() // 2, SCREEN_H // 2 - 30))
        if sub:
            sm = self.font_sm.render(sub, True, WHITE)
            self.screen.blit(sm, (SCREEN_W // 2 - sm.get_width() // 2, SCREEN_H // 2 + 10))
        pygame.display.flip()
