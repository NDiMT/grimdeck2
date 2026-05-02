import random
from dataclasses import dataclass, field
from typing import Optional, List

# ── Room types ────────────────────────────────────────────────────────────────
ROOM_START    = "start"
ROOM_MONSTER  = "monster"
ROOM_ELITE    = "elite"
ROOM_REST     = "rest"
ROOM_TREASURE = "treasure"
ROOM_SHOP     = "shop"
ROOM_BOSS     = "boss"

ROOM_ICONS = {
    ROOM_START:    "S",
    ROOM_MONSTER:  "M",
    ROOM_ELITE:    "E",
    ROOM_REST:     "R",
    ROOM_TREASURE: "$",
    ROOM_SHOP:     "P",
    ROOM_BOSS:     "B",
}

ROOM_COLORS = {
    ROOM_START:    (100, 200, 100),
    ROOM_MONSTER:  (200,  80,  80),
    ROOM_ELITE:    (200,  50, 200),
    ROOM_REST:     ( 80, 160, 220),
    ROOM_TREASURE: (215, 175,  55),
    ROOM_SHOP:     ( 80, 200, 150),
    ROOM_BOSS:     (220,  50,  50),
}


@dataclass(eq=False)
class Room:
    kind:    str
    col:     int   # column 0-2
    row:     int   # row 0 = start, row N = boss
    visited: bool  = False
    children: List["Room"] = field(default_factory=list)   # rooms reachable next

    @property
    def label(self):
        return ROOM_ICONS.get(self.kind, "?")

    @property
    def color(self):
        return ROOM_COLORS.get(self.kind, (150, 150, 150))


class DungeonMap:
    """
    Slay-the-Spire-style map:
    • 3 columns, ROWS rows
    • Row 0 = starting room, row ROWS-1 = boss
    • Each non-start room is reachable via branching paths
    """

    COLS = 3
    ROWS = 8   # rows 0..7; row 0=start, row 7=boss

    # Type weights per row bracket
    _WEIGHTS_EARLY = {ROOM_MONSTER: 70, ROOM_REST: 15, ROOM_TREASURE: 15}
    _WEIGHTS_MID   = {ROOM_MONSTER: 45, ROOM_ELITE: 25, ROOM_REST: 15, ROOM_SHOP: 15}

    def __init__(self, floor: int = 1):
        self.floor        = floor
        self.rooms: List[List[Optional[Room]]] = []  # [row][col]
        self.start_room:  Optional[Room] = None
        self.boss_room:   Optional[Room] = None
        self.current:     Optional[Room] = None
        self._generate()

    # ── generation ────────────────────────────────────────────────────────────
    def _generate(self):
        rows, cols = self.ROWS, self.COLS
        # Build grid – every cell has a Room
        self.rooms = []
        for r in range(rows):
            row_rooms = []
            for c in range(cols):
                kind = self._pick_kind(r, rows)
                row_rooms.append(Room(kind=kind, col=c, row=r))
            self.rooms.append(row_rooms)

        # Fix first and last rows
        for c in range(cols):
            self.rooms[0][c].kind = ROOM_START
            self.rooms[rows - 1][c].kind = ROOM_BOSS

        # Only 1 start room (center col) and 1 boss room (center)
        start_col = cols // 2
        boss_col  = cols // 2
        self.rooms[0] = [None] * cols
        self.rooms[0][start_col] = Room(ROOM_START, start_col, 0)
        self.rooms[rows - 1] = [None] * cols
        self.rooms[rows - 1][boss_col] = Room(ROOM_BOSS, boss_col, rows - 1)

        self.start_room = self.rooms[0][start_col]
        self.boss_room  = self.rooms[rows - 1][boss_col]

        # Build connections (each room links to 1-2 rooms in next row)
        for r in range(rows - 1):
            for c in range(cols):
                room = self.rooms[r][c]
                if room is None:
                    continue
                # Possible next columns: same, ±1 clamped
                candidates = list({max(0, c - 1), c, min(cols - 1, c + 1)})
                n_links = 1 if r == 0 or r == rows - 2 else random.randint(1, 2)
                chosen = random.sample(candidates, min(n_links, len(candidates)))
                for nc in chosen:
                    target = self.rooms[r + 1][nc]
                    if target and target not in room.children:
                        room.children.append(target)

        # Ensure boss is reachable from every second-to-last room
        for c in range(cols):
            room = self.rooms[rows - 2][c]
            if room and self.boss_room not in room.children:
                room.children.append(self.boss_room)

        self.current = self.start_room
        self.start_room.visited = True

    def _pick_kind(self, row: int, total_rows: int) -> str:
        if row == 0:
            return ROOM_START
        if row == total_rows - 1:
            return ROOM_BOSS
        if row <= total_rows // 2:
            weights = self._WEIGHTS_EARLY
        else:
            weights = self._WEIGHTS_MID
        kinds  = list(weights.keys())
        wts    = list(weights.values())
        return random.choices(kinds, weights=wts, k=1)[0]

    # ── navigation ────────────────────────────────────────────────────────────
    def available_rooms(self) -> List[Room]:
        """Rooms the player can move to next (unvisited children of current)."""
        return self.current.children if self.current else []

    def enter_room(self, room: Room):
        room.visited = True
        self.current = room

    # ── screen coords for rendering ───────────────────────────────────────────
    def room_screen_pos(self, room: Room, map_x: int, map_y: int,
                        map_w: int, map_h: int):
        """Return (px, py) pixel centre of a room node."""
        rows = self.ROWS
        cols = self.COLS
        col_w = map_w // (cols + 1)
        row_h = map_h // (rows + 1)
        px = map_x + (room.col + 1) * col_w
        py = map_y + map_h - (room.row + 1) * row_h
        return px, py

    def all_rooms(self):
        for row in self.rooms:
            for r in row:
                if r is not None:
                    yield r
