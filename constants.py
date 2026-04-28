# ─── Battle City Constants ───────────────────────────────────────────────────

GRID_SIZE    = 26          # 26x26 tile grid
TILE_SIZE    = 24          # pixels per tile
PANEL_WIDTH  = 180         # right-side HUD panel
SCREEN_W     = GRID_SIZE * TILE_SIZE + PANEL_WIDTH   # 624 + 180 = 804
SCREEN_H     = GRID_SIZE * TILE_SIZE                 # 624
FPS          = 20          # slower overall game speed

# ─── Tile Types ───────────────────────────────────────────────────────────────
EMPTY  = 0
BRICK  = 1
STEEL  = 2
WATER  = 3
FOREST = 4
EAGLE  = 5

# ─── Directions ───────────────────────────────────────────────────────────────
UP    = (0, -1)
DOWN  = (0,  1)
LEFT  = (-1, 0)
RIGHT = (1,  0)
DIRS  = [UP, DOWN, LEFT, RIGHT]

# ─── Colours ─────────────────────────────────────────────────────────────────
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
DARK_GREY   = (30,  30,  30)
MID_GREY    = (60,  60,  60)
YELLOW      = (255, 220,  50)
ORANGE      = (220, 120,  30)
RED         = (200,  40,  40)
GREEN       = (50,  160,  60)
DARK_GREEN  = (20,  80,  30)
STEEL_BLUE  = (80,  110, 160)
WATER_BLUE  = (50,   90, 180)
WATER_LIGHT = (80,  130, 220)
BRICK_RED   = (170,  60,  30)
BRICK_DARK  = (120,  40,  20)
GOLD        = (220, 180,  30)
HUD_BG      = (18,  18,  18)
HUD_LINE    = (40,  40,  40)

# ─── Tank types ───────────────────────────────────────────────────────────────
TANK_BASIC  = "basic"
TANK_FAST   = "fast"
TANK_ARMOR  = "armor"
TANK_PLAYER = "player"
TANK_BOSS   = "boss"

# ─── Speed table (ticks per move) ─────────────────────────────────────────────
SPEED = {
    TANK_PLAYER: 3,    # moves every 3 ticks
    TANK_BASIC:  6,    # slow enemy
    TANK_FAST:   4,    # fast enemy (still slower than before)
    TANK_ARMOR:  5,    # medium enemy
    TANK_BOSS:   5,
}

# ─── HP table ─────────────────────────────────────────────────────────────────
HP = {
    TANK_PLAYER: 1,
    TANK_BASIC:  1,
    TANK_FAST:   1,
    TANK_ARMOR:  4,
    TANK_BOSS:   10,
}

# ─── Fixed positions ──────────────────────────────────────────────────────────
EAGLE_POS        = (12, 24)
PLAYER_SPAWN     = (4,  24)
ENEMY_SPAWNS     = [(0, 0), (12, 0), (24, 0)]
MAX_ACTIVE_ENEMY = 3
