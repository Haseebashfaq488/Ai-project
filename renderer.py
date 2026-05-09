"""
Renderer — draws the tile grid, tanks, bullets, and HUD panel.
Pure pygame drawing; no game logic lives here.
"""

import math
import pygame
from constants import *


def _darken(col, factor=0.6):
    out = [min(255, max(0, int(c * factor))) for c in col]
    return pygame.Color(*out)

def _lighten(col, factor=1.4):
    out = [min(255, max(0, int(c * factor))) for c in col]
    return pygame.Color(*out)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        # Use a modern font look (Trebuchet or generic sans-serif)
        self.font_lg = pygame.font.SysFont("Trebuchet MS", 28, bold=True)
        self.font_md = pygame.font.SysFont("Trebuchet MS", 20, bold=True)
        self.font_sm = pygame.font.SysFont("Trebuchet MS", 16)
        self.font_xs = pygame.font.SysFont("Trebuchet MS", 13)
        self._anim   = 0
        self.particles = []

    def add_explosion(self, px, py, color, count=15):
        import random
        for _ in range(count):
            dx = random.uniform(-3, 3)
            dy = random.uniform(-3, 3)
            life = random.randint(15, 40)
            self.particles.append([px, py, dx, dy, life, color])

    def tick(self):
        self._anim = (self._anim + 1) % 180

    # ── Main draw call ─────────────────────────────────────────────────────

    def draw(self, tilemap, player, enemies, bullets, level, kills_left):
        self.screen.fill(BLACK)
        self._draw_grid(tilemap)
        self._draw_bullets(bullets)
        self._draw_enemies(enemies)
        self._draw_player(player)
        self._draw_particles()
        self._draw_hud(player, level, kills_left)
        pygame.display.flip()

    def _draw_particles(self):
        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
            if p[4] <= 0:
                self.particles.remove(p)
                continue
            alpha = min(255, int((p[4] / 30.0) * 255))
            pygame.draw.circle(self.screen, p[5], (int(p[0]), int(p[1])), max(1, p[4]//8))
            
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
                    # Give empty areas a subtle very dark shading maybe (using DARK_GREY)
                    pygame.draw.rect(self.screen, DARK_GREY, r)

                elif tile == BRICK:
                    pygame.draw.rect(self.screen, BRICK_RED, r)
                    # Beveled edges
                    pygame.draw.line(self.screen, _lighten(BRICK_RED, 1.3), (rx, ry), (rx+T-1, ry), 1)
                    pygame.draw.line(self.screen, _lighten(BRICK_RED, 1.3), (rx, ry), (rx, ry+T-1), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx, ry+T-1), (rx+T-1, ry+T-1), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx+T-1, ry), (rx+T-1, ry+T-1), 1)
                    # Brick pattern
                    pygame.draw.line(self.screen, BRICK_DARK, (rx, ry + T//2), (rx + T, ry + T//2), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx + T//2, ry), (rx + T//2, ry + T//2), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx + T//4, ry + T//2), (rx + T//4, ry + T), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx + T//4*3, ry + T//2), (rx + T//4*3, ry + T), 1)

                elif tile == STEEL:
                    pygame.draw.rect(self.screen, STEEL_BLUE, r)
                    pygame.draw.rect(self.screen, _lighten(STEEL_BLUE, 1.4), r, 2, border_radius=2)
                    pygame.draw.rect(self.screen, _darken(STEEL_BLUE, 0.7), r.inflate(-4, -4), 1)
                    pygame.draw.line(self.screen, WHITE, (rx+4, ry+4), (rx+8, ry+4), 1)

                elif tile == WATER:
                    # Smooth wave animation using sine
                    pygame.draw.rect(self.screen, WATER_BLUE, r)
                    offset = math.sin((self._anim + x*10 + y*5) * 0.1) * 2
                    pygame.draw.line(self.screen, WATER_LIGHT, (rx+2, ry+T//3+offset), (rx+T-2, ry+T//3+offset), 2)
                    pygame.draw.line(self.screen, WATER_LIGHT, (rx+2, ry+T//3*2-offset), (rx+T-2, ry+T//3*2-offset), 2)

                elif tile == FOREST:
                    # Dark green base
                    pygame.draw.rect(self.screen, DARK_GREEN, r)
                    # Bush clusters
                    pygame.draw.circle(self.screen, GREEN, (rx + T//4+1, ry + T//2), T//3+1)
                    pygame.draw.circle(self.screen, GREEN, (rx + T//2+1, ry + T//3), T//3+1)
                    pygame.draw.circle(self.screen, GREEN, (rx + T//4*3, ry + T//2+1), T//3)

                elif tile == EAGLE:
                    pygame.draw.rect(self.screen, DARK_GREY, r)
                    # Gold base
                    pygame.draw.rect(self.screen, GOLD, (rx+4, ry+T-6, T-8, 4))
                    pygame.draw.rect(self.screen, GOLD, (rx+8, ry+T-10, T-16, 4))
                    # Eagle shape
                    pygame.draw.polygon(self.screen, GOLD, [
                        (rx + T//2, ry + 2),
                        (rx + T - 2, ry + T//2+2),
                        (rx + T//2, ry + T//2+6),
                        (rx + 2, ry + T//2+2),
                    ])
                    # Emblem
                    pygame.draw.circle(self.screen, WHITE, (rx + T//2, ry + T//2), 3)

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
        
        # Smooth linear interpolation for continuous visual movement
        if not hasattr(tank, 'visual_x') or abs(tank.x - tank.visual_x) > 1.5 or abs(tank.y - tank.visual_y) > 1.5:
            tank.visual_x = float(tank.x)
            tank.visual_y = float(tank.y)
            
        step = 1.0 / max(1.0, float(tank.speed) * 0.85)
        
        if tank.visual_x < tank.x:
            tank.visual_x = min(float(tank.x), tank.visual_x + step)
        elif tank.visual_x > tank.x:
            tank.visual_x = max(float(tank.x), tank.visual_x - step)
            
        if tank.visual_y < tank.y:
            tank.visual_y = min(float(tank.y), tank.visual_y + step)
        elif tank.visual_y > tank.y:
            tank.visual_y = max(float(tank.y), tank.visual_y - step)

        rx = int(tank.visual_x * T)
        ry = int(tank.visual_y * T)

        # Flicker when armor tank is hit
        if tank.tank_type == TANK_ARMOR and tank.hp < tank.max_hp:
            if (self._anim // 3) % 2 == 1:
                body_c = WHITE
        
        # Player glow effect
        if tank.tank_type == TANK_PLAYER:
            glow_r = pygame.Rect(rx, ry, T, T)
            pygame.draw.rect(self.screen, _darken(body_c, 0.4), glow_r, border_radius=6)

        # Body
        body = pygame.Rect(rx + 3, ry + 3, T - 6, T - 6)
        pygame.draw.rect(self.screen, body_c, body, border_radius=4)
        pygame.draw.rect(self.screen, dark_c, body, 2, border_radius=4)

        # Tracks (side bars)
        track_w = max(4, T // 7)
        if tank.direction[1] != 0: # Moving vertically, tracks on left/right
            pygame.draw.rect(self.screen, dark_c, (rx + 1, ry + 2, track_w, T - 4), border_radius=2)
            pygame.draw.rect(self.screen, dark_c, (rx + T - 1 - track_w, ry + 2, track_w, T - 4), border_radius=2)
        else: # Moving horizontally, tracks top/bottom
            pygame.draw.rect(self.screen, dark_c, (rx + 2, ry + 1, T - 4, track_w), border_radius=2)
            pygame.draw.rect(self.screen, dark_c, (rx + 2, ry + T - 1 - track_w, T - 4, track_w), border_radius=2)

        # Hull detail ring
        highlight = pygame.Rect(rx + 7, ry + 7, T - 14, T - 14)
        highlight_color = _lighten(body_c, 1.2)
        pygame.draw.rect(self.screen, highlight_color, highlight, border_radius=6)

        # Barrel
        dx, dy = tank.direction
        cx, cy = rx + T // 2, ry + T // 2
        barrel_length = max(10, T // 2)
        bx = cx + dx * barrel_length
        by_ = cy + dy * barrel_length
        pygame.draw.line(self.screen, WHITE, (cx, cy), (bx, by_), max(4, T // 8))
        pygame.draw.line(self.screen, dark_c, (cx, cy), (bx, by_), max(2, T // 10))

        # HP bar for boss / armor tank
        if tank.max_hp > 1:
            bar_w = T - 4
            filled = int(bar_w * tank.hp / tank.max_hp)
            pygame.draw.rect(self.screen, RED,   (rx + 2, ry - 6, bar_w, 3))
            pygame.draw.rect(self.screen, GREEN, (rx + 2, ry - 6, filled, 3))

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
            if not getattr(b, 'visible', False):
                continue
            px, py = b.rect_xy()
            col    = YELLOW if b.is_player_bullet else ORANGE
            # Outer glow
            pygame.draw.circle(self.screen, _darken(col, 0.5), (int(px), int(py)), 6)
            pygame.draw.circle(self.screen, col, (int(px), int(py)), 3)
            pygame.draw.circle(self.screen, WHITE, (int(px), int(py)), 1)
            # Long Tracer line trailing opposite to direction
            tx = px - b.dx * 12
            ty = py - b.dy * 12
            pygame.draw.line(self.screen, col, (tx, ty), (px, py), 2)

    # ── HUD Panel ─────────────────────────────────────────────────────────

    def _draw_hud(self, player, level, kills_left):
        px = GRID_SIZE * TILE_SIZE
        pw = PANEL_WIDTH
        ph = SCREEN_H
        # Dark pane for UI with subtle gradient effect (approximated with rects)
        pygame.draw.rect(self.screen, (10, 12, 14), (px, 0, pw, ph))
        pygame.draw.line(self.screen, (30, 40, 50), (px, 0), (px, ph), 4)

        y = 20
        # Title with drop shadow
        title = self.font_lg.render("BATTLE", True, GOLD)
        shadow = self.font_lg.render("BATTLE", True, BLACK)
        self.screen.blit(shadow, (px + (pw - shadow.get_width()) // 2 + 3, y + 3))
        self.screen.blit(title, (px + (pw - title.get_width()) // 2, y))
        y += 28
        title2 = self.font_lg.render("CITY", True, ORANGE)
        shadow2 = self.font_lg.render("CITY", True, BLACK)
        self.screen.blit(shadow2, (px + (pw - shadow2.get_width()) // 2 + 3, y + 3))
        self.screen.blit(title2, (px + (pw - title2.get_width()) // 2, y))
        y += 40

        # Beautiful horizontal separator
        def draw_separator(sy):
            c1 = (30, 40, 50)
            pygame.draw.line(self.screen, c1, (px + 15, sy), (px + pw - 15, sy), 2)
            pygame.draw.line(self.screen, BLACK, (px + 15, sy+2), (px + pw - 15, sy+2), 2)

        draw_separator(y); y += 15

        def label(text, val, col=WHITE):
            nonlocal y
            # Backplate
            pygame.draw.rect(self.screen, (20, 24, 28), (px + 10, y-2, pw - 20, 26), border_radius=4)
            s1 = self.font_sm.render(text, True, (120, 130, 140))
            s2 = self.font_md.render(str(val), True, col)
            self.screen.blit(s1, (px + 16, y + 2))
            self.screen.blit(s2, (px + pw - s2.get_width() - 16, y - 2))
            y += 34

        label("LEVEL", level, YELLOW)

        diff_levels = {1: "EASY", 2: "MED", 3: "HARD"}
        diff_text   = diff_levels.get(level, "???")
        diff_col    = {1: GREEN, 2: ORANGE, 3: RED}.get(level, WHITE)
        label("DIFF", diff_text, diff_col)

        label("ENEMIES", kills_left, ORANGE)
        y += 10

        # Lives as scalable glowing hearts
        draw_separator(y); y += 15
        s = self.font_sm.render("LIVES", True, (120, 130, 140))
        self.screen.blit(s, (px + (pw - s.get_width())//2, y))
        y += 24
        
        hearts = ""
        for i in range(3):
            hearts += "♥ " if i < player.lives else "♡ "
        
        # Pulse animation if 1 life
        hcol = RED if player.lives > 1 else (255, max(80, 80 + int(math.sin(self._anim*0.1)*80)), 80)
        hs = self.font_lg.render(hearts.strip(), True, hcol)
        self.screen.blit(hs, (px + (pw - hs.get_width()) // 2, y))
        y += 40

        draw_separator(y); y += 15

        # Legend using background plates
        s = self.font_sm.render("TANKS", True, (120, 130, 140))
        self.screen.blit(s, (px + 15, y)); y += 22
        legend = [
            ("Basic",  (80, 180, 80)),
            ("Fast",   (80, 200, 220)),
            ("Armor",  (190, 100, 60)),
        ]
        for txt, col in legend:
            pygame.draw.rect(self.screen, col, (px + 16, y + 2, 10, 10), border_radius=2)
            s = self.font_xs.render(txt, True, WHITE)
            self.screen.blit(s, (px + 34, y))
            y += 18

        # Draw controls pinned to bottom
        y = ph - 65
        draw_separator(y-10)
        for line in ["[WASD] Move", "[SPACE] Fire", "[ESC] Quit"]:
            s = self.font_xs.render(line, True, (100, 110, 120))
            self.screen.blit(s, (px + 15, y))
            y += 18

    # ── Overlay screens ───────────────────────────────────────────────────

    def draw_overlay(self, text, sub="", color=GOLD):
        # Slightly blurry transparent overlay effect
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((10, 15, 20, 200))
        self.screen.blit(overlay, (0, 0))

        # Box backplate
        bw, bh = 400, 150
        box = pygame.Rect(SCREEN_W//2 - bw//2, SCREEN_H//2 - bh//2, bw, bh)
        pygame.draw.rect(self.screen, (20, 25, 30), box, border_radius=10)
        pygame.draw.rect(self.screen, color, box, 2, border_radius=10)

        big = self.font_lg.render(text, True, color)
        self.screen.blit(big, (SCREEN_W // 2 - big.get_width() // 2, SCREEN_H // 2 - 35))
        if sub:
            # Pulsing subtext alpha
            alpha = 150 + int(math.sin(self._anim * 0.1) * 105)
            sm = self.font_md.render(sub, True, WHITE)
            sm.set_alpha(alpha)
            self.screen.blit(sm, (SCREEN_W // 2 - sm.get_width() // 2, SCREEN_H // 2 + 10))
        pygame.display.flip()
