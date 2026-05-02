import pygame
import math
from src.constants import *
from src import effects as EFF
from src.dungeon import ROOM_COLORS, ROOM_ICONS


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Renderer:
    """Handles all pygame drawing for every game state."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        pygame.font.init()
        self._load_fonts()

        # State for click detection (updated each frame)
        self.dungeon_room_rects:  dict = {}   # Room → pygame.Rect
        self.combat_card_rects:   list = []   # [(Card, Rect), ...]
        self.combat_monster_rects: dict = {}  # Monster → Rect
        self.combat_end_turn_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.reward_card_rects:   list = []   # [(Card, Rect), ...]
        self.rest_heal_rect:      pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.rest_upgrade_rect:   pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.menu_start_rect:     pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.go_continue_rect:    pygame.Rect = pygame.Rect(0, 0, 0, 0)

        self._hover_card_idx = -1

    def _load_fonts(self):
        candidates = ["Segoe UI", "Ubuntu", "DejaVu Sans", "Arial", ""]
        def try_font(size):
            for name in candidates:
                try:
                    return pygame.font.SysFont(name, size)
                except Exception:
                    pass
            return pygame.font.Font(None, size)

        self.f_title  = try_font(56)
        self.f_large  = try_font(30)
        self.f_med    = try_font(22)
        self.f_small  = try_font(17)
        self.f_tiny   = try_font(13)

    # ─────────────────────────────────────────────────────────────────────────
    # Shared primitives
    # ─────────────────────────────────────────────────────────────────────────

    def _text(self, surf, txt, font, color, x, y, center=False, right=False):
        s = font.render(str(txt), True, color)
        r = s.get_rect()
        if center:  r.center = (x, y)
        elif right: r.topright = (x, y)
        else:       r.topleft  = (x, y)
        surf.blit(s, r)
        return r

    def _text_wrap(self, surf, txt, font, color, rect: pygame.Rect):
        """Render multi-line text (split by \\n) inside rect."""
        lines = txt.split("\n")
        y = rect.y
        for line in lines:
            if y + font.get_height() > rect.bottom:
                break
            s = font.render(line, True, color)
            surf.blit(s, (rect.x, y))
            y += font.get_height() + 2

    def _rect(self, surf, color, r, radius=6, border=0, border_color=None):
        if radius:
            pygame.draw.rect(surf, color, r, border_radius=radius)
        else:
            pygame.draw.rect(surf, color, r)
        if border and border_color:
            if radius:
                pygame.draw.rect(surf, border_color, r, border, border_radius=radius)
            else:
                pygame.draw.rect(surf, border_color, r, border)

    def _bar(self, surf, x, y, w, h, value, maximum, fg, bg=DGRAY, label=""):
        self._rect(surf, bg, pygame.Rect(x, y, w, h), radius=4)
        if maximum > 0:
            fill_w = int(w * max(0, value) / maximum)
            if fill_w > 0:
                self._rect(surf, fg, pygame.Rect(x, y, fill_w, h), radius=4)
        self._rect(surf, GRAY, pygame.Rect(x, y, w, h), radius=4, border=1, border_color=GRAY)
        if label:
            self._text(surf, label, self.f_tiny, WHITE, x + w // 2, y + h // 2, center=True)

    def _button(self, surf, label, rect: pygame.Rect,
                fg=WHITE, bg=DGRAY, hover=False, active=True):
        col = _lerp_color(bg, WHITE, 0.15) if hover else bg
        if not active:
            col = (40, 40, 50)
        self._rect(surf, col, rect, radius=8, border=2,
                   border_color=LGRAY if active else GRAY)
        self._text(surf, label, self.f_med,
                   WHITE if active else GRAY,
                   rect.centerx, rect.centery, center=True)

    def _energy_orb(self, surf, cx, cy, r, value, maximum):
        for i in range(maximum):
            ox = cx + i * (r * 2 + 4)
            col = YELLOW if i < value else DGRAY
            pygame.draw.circle(surf, col, (ox, cy), r)
            pygame.draw.circle(surf, LGRAY, (ox, cy), r, 1)
            self._text(surf, str(i + 1) if i < value else "·",
                       self.f_tiny, BLACK if i < value else GRAY,
                       ox, cy, center=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Card rendering
    # ─────────────────────────────────────────────────────────────────────────

    def _draw_card(self, surf, card, x, y, hovered=False, selected=False, grayed=False):
        w, h = CARD_W, CARD_H
        if hovered:
            y -= 18
            w = int(w * 1.05)
            h = int(h * 1.05)

        r = pygame.Rect(x, y, w, h)

        # Shadow
        shadow = pygame.Rect(x + 4, y + 4, w, h)
        shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 90))
        surf.blit(shadow_surf, shadow)

        # Body
        base_color = card.color
        if grayed:
            base_color = (45, 45, 55)
        self._rect(surf, base_color, r, radius=8,
                   border=2, border_color=YELLOW if selected else LGRAY)

        # Header bar (type color, lighter)
        header = pygame.Rect(x + 2, y + 2, w - 4, 28)
        hcol   = _lerp_color(base_color, WHITE, 0.25)
        self._rect(surf, hcol, header, radius=6)

        # Cost circle
        pygame.draw.circle(surf, YELLOW if card.cost >= 0 else PURPLE,
                           (x + 16, y + 16), 12)
        pygame.draw.circle(surf, WHITE, (x + 16, y + 16), 12, 1)
        cost_txt = str(card.cost) if card.cost >= 0 else "X"
        self._text(surf, cost_txt, self.f_small, BLACK, x + 16, y + 16, center=True)

        # Name
        name_color = WHITE if not grayed else GRAY
        self._text(surf, card.name, self.f_tiny, name_color,
                   x + w // 2, y + 16, center=True)

        # Divider
        pygame.draw.line(surf, GRAY, (x + 6, y + 32), (x + w - 6, y + 32))

        # Description (wrapped)
        desc_rect = pygame.Rect(x + 6, y + 36, w - 12, h - 50)
        self._text_wrap(surf, card.desc, self.f_tiny,
                        name_color, desc_rect)

        # Type tag
        tag_txt = card.kind.upper()
        tag_col = _lerp_color(base_color, LGRAY, 0.5)
        self._text(surf, tag_txt, self.f_tiny, tag_col,
                   x + w // 2, y + h - 12, center=True)

        return r

    # ─────────────────────────────────────────────────────────────────────────
    # Effect badges
    # ─────────────────────────────────────────────────────────────────────────

    def _draw_effects(self, surf, entity, x, y, max_width=200):
        cx = x
        for name, val in entity.effects.items():
            if val == 0:
                continue
            col = EFF.EFFECT_COLORS.get(name, GRAY)
            label = EFF.EFFECT_LABELS.get(name, name)
            badge = pygame.Rect(cx, y, 60, 20)
            self._rect(surf, col, badge, radius=4)
            self._text(surf, f"{label[:6]}:{val}", self.f_tiny, WHITE,
                       badge.centerx, badge.centery, center=True)
            cx += 64
            if cx - x > max_width:
                break

    # ─────────────────────────────────────────────────────────────────────────
    # MENU SCREEN
    # ─────────────────────────────────────────────────────────────────────────

    def render_menu(self, _game=None):
        s = self.screen
        s.fill(BG)

        # Title
        self._text(s, "G R I M D E C K", self.f_title, GOLD,
                   SCREEN_W // 2, 200, center=True)
        self._text(s, "A Dungeon Crawler Card Game", self.f_med, LGRAY,
                   SCREEN_W // 2, 270, center=True)

        # Start button
        btn = pygame.Rect(SCREEN_W // 2 - 120, 360, 240, 55)
        mpos = pygame.mouse.get_pos()
        self._button(s, "Begin Your Journey", btn,
                     hover=btn.collidepoint(mpos))
        self.menu_start_rect = btn

        # Controls hint
        self._text(s, "Click cards to play  •  Click monster to target  •  End Turn button to pass",
                   self.f_small, GRAY, SCREEN_W // 2, 500, center=True)

        pygame.display.flip()

    # ─────────────────────────────────────────────────────────────────────────
    # DUNGEON MAP SCREEN
    # ─────────────────────────────────────────────────────────────────────────

    def render_dungeon(self, game):
        s = self.screen
        s.fill(BG)

        dungeon = game.dungeon
        player  = game.player

        # Map area
        MAP_X, MAP_Y = 80, 60
        MAP_W, MAP_H = 700, 620
        map_rect = pygame.Rect(MAP_X, MAP_Y, MAP_W, MAP_H)
        self._rect(s, PANEL, map_rect, radius=10)
        self._text(s, f"Floor {dungeon.floor}  –  The Dungeon",
                   self.f_large, GOLD, MAP_X + MAP_W // 2, MAP_Y + 20, center=True)

        available = set(dungeon.available_rooms())
        mpos = pygame.mouse.get_pos()
        self.dungeon_room_rects = {}

        # Pre-compute positions
        pos = {}
        for room in dungeon.all_rooms():
            px, py = dungeon.room_screen_pos(room,
                                             MAP_X + 20, MAP_Y + 40,
                                             MAP_W - 40, MAP_H - 60)
            pos[id(room)] = (px, py)

        # Draw connection lines first
        for room in dungeon.all_rooms():
            px, py = pos[id(room)]
            for child in room.children:
                cx, cy = pos[id(child)]
                col = LGRAY if room.visited else DGRAY
                pygame.draw.line(s, col, (px, py), (cx, cy), 2)

        # Draw rooms
        for room in dungeon.all_rooms():
            px, py = pos[id(room)]
            radius = 22
            is_current   = (room is dungeon.current)
            is_available = (room in available)

            if is_current:
                pygame.draw.circle(s, YELLOW, (px, py), radius + 5)
            elif is_available:
                t = (math.sin(pygame.time.get_ticks() / 400) + 1) / 2
                glow = _lerp_color(room.color, WHITE, t * 0.4)
                pygame.draw.circle(s, glow, (px, py), radius + 3)

            col = room.color if room.visited or is_available else DGRAY
            pygame.draw.circle(s, col, (px, py), radius)
            pygame.draw.circle(s, LGRAY, (px, py), radius, 2)
            self._text(s, room.label, self.f_med, WHITE, px, py, center=True)

            rect = pygame.Rect(px - radius, py - radius, radius * 2, radius * 2)
            self.dungeon_room_rects[room] = rect

        # Side panel
        px2, py2 = 840, 80
        pw, ph = 360, 580
        panel = pygame.Rect(px2, py2, pw, ph)
        self._rect(s, PANEL, panel, radius=10)

        self._text(s, "The Wanderer", self.f_large, WHITE, px2 + pw // 2, py2 + 20, center=True)
        pygame.draw.line(s, GRAY, (px2 + 20, py2 + 52), (px2 + pw - 20, py2 + 52))

        # HP
        self._text(s, "HP", self.f_med, LGRAY, px2 + 25, py2 + 70)
        self._bar(s, px2 + 80, py2 + 72, pw - 100, 22,
                  player.hp, player.max_hp, RED,
                  label=f"{player.hp}/{player.max_hp}")

        # Gold
        self._text(s, f"Gold:  {player.gold}", self.f_med, GOLD, px2 + 25, py2 + 115)

        # Deck info
        total = (len(player.draw_pile) + len(player.hand) +
                 len(player.discard_pile) + len(player.exhaust_pile))
        self._text(s, f"Deck:  {total} cards", self.f_med, LGRAY, px2 + 25, py2 + 148)

        # Legend
        legend_y = py2 + 200
        self._text(s, "Room Legend", self.f_med, LGRAY, px2 + 25, legend_y)
        for i, (kind, icon) in enumerate(ROOM_ICONS.items()):
            ly = legend_y + 30 + i * 28
            col = ROOM_COLORS[kind]
            pygame.draw.circle(s, col, (px2 + 40, ly + 10), 10)
            labels = {
                "start": "Start", "monster": "Monster (fight!)",
                "elite": "Elite (hard fight)", "rest": "Rest Site",
                "treasure": "Treasure", "shop": "Shop",
                "boss": "Boss (final fight)",
            }
            self._text(s, f" {icon}  {labels.get(kind,kind)}", self.f_small, WHITE,
                       px2 + 55, ly)

        # Instruction
        if available:
            self._text(s, "Click a highlighted room to enter.",
                       self.f_small, YELLOW, px2 + pw // 2, py2 + ph - 35, center=True)
        else:
            self._text(s, "No moves available.",
                       self.f_small, GRAY, px2 + pw // 2, py2 + ph - 35, center=True)

        pygame.display.flip()

    # ─────────────────────────────────────────────────────────────────────────
    # COMBAT SCREEN
    # ─────────────────────────────────────────────────────────────────────────

    def render_combat(self, game):
        s = self.screen
        combat  = game.combat
        player  = game.player
        monsters = combat.monsters

        s.fill(BG)
        mpos = pygame.mouse.get_pos()

        # Top bar
        top = pygame.Rect(0, 0, SCREEN_W, 50)
        self._rect(s, PANEL, top, radius=0)
        self._text(s, f"Turn {combat.turn_num}", self.f_med, LGRAY, 20, 14)

        # Energy orbs
        self._text(s, "Energy:", self.f_small, GRAY, SCREEN_W // 2 - 90, 18)
        self._energy_orb(s, SCREEN_W // 2 + 10, 25, 14,
                         player.energy, player.max_energy)

        # Deck / Discard / Exhaust counts
        draw_c    = len(player.draw_pile)
        discard_c = len(player.discard_pile)
        exhaust_c = len(player.exhaust_pile)
        self._text(s, f"Draw:{draw_c}  Disc:{discard_c}  Exh:{exhaust_c}",
                   self.f_small, LGRAY, SCREEN_W - 220, 16)

        # Phase indicator
        if combat.phase == "monster":
            self._text(s, "⚔ ENEMY TURN", self.f_med, RED,
                       SCREEN_W // 2, 25, center=True)

        # ── Player area ──
        self._draw_player_area(s, player, mpos)

        # ── Monster area(s) ──
        self.combat_monster_rects = {}
        n = len(monsters)
        for i, m in enumerate(monsters):
            mx = 960 + (i - n // 2) * 200 + (100 if n % 2 == 0 else 0)
            my = 140
            rect = self._draw_monster(s, m, mx, my, combat, mpos,
                                      selectable=combat.selected_card is not None)
            self.combat_monster_rects[m] = rect

        # ── Combat log ──
        log_rect = pygame.Rect(380, 55, 360, 200)
        self._rect(s, PANEL, log_rect, radius=6)
        visible = combat._log[-8:]
        for i, line in enumerate(visible):
            self._text(s, line, self.f_tiny, LGRAY if i < len(visible) - 1 else WHITE,
                       log_rect.x + 8, log_rect.y + 6 + i * 24)

        # ── Card hand ──
        self._draw_hand(s, player, combat, mpos)

        # ── End Turn button ──
        btn = pygame.Rect(SCREEN_W - 170, SCREEN_H - 70, 148, 48)
        active = combat.phase == "player"
        self._button(s, "End Turn", btn, bg=DRED,
                     hover=btn.collidepoint(mpos) and active, active=active)
        self.combat_end_turn_rect = btn

        # Victory / Defeat overlay
        if combat.phase in ("victory", "defeat"):
            self._draw_combat_overlay(s, combat.phase)

        pygame.display.flip()

    def _draw_player_area(self, s, player, mpos):
        # Character silhouette
        char_x, char_y = 120, 130
        # Body
        self._rect(s, (60, 80, 120), pygame.Rect(char_x - 28, char_y, 56, 80), radius=6)
        # Head
        pygame.draw.circle(s, (90, 120, 160), (char_x, char_y - 20), 24)
        # Sword
        pygame.draw.line(s, LGRAY, (char_x + 28, char_y + 10),
                         (char_x + 55, char_y - 25), 4)
        # Shield
        self._rect(s, (60, 100, 180), pygame.Rect(char_x - 60, char_y + 5, 28, 36), radius=4)
        pygame.draw.rect(s, LGRAY, pygame.Rect(char_x - 60, char_y + 5, 28, 36), 2)

        info_x, info_y = 30, 260
        # HP bar
        self._text(s, "HP", self.f_small, LGRAY, info_x, info_y)
        self._bar(s, info_x + 30, info_y + 2, 200, 20,
                  player.hp, player.max_hp, RED,
                  label=f"{player.hp}/{player.max_hp}")

        # Block
        if player.block:
            self._text(s, f"🛡 {player.block}", self.f_med, BLUE, info_x, info_y + 28)

        # Effects
        self._draw_effects(s, player, info_x, info_y + 56)

    def _draw_monster(self, s, monster, cx, cy, combat, mpos, selectable=False):
        # Body shape
        w, h = 80, 100
        rx, ry = cx - w // 2, cy
        body_r = pygame.Rect(rx, ry, w, h)

        # Glow if selectable
        if selectable:
            t = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2
            glow_col = _lerp_color(monster.color, (255, 255, 50), t * 0.5)
            self._rect(s, glow_col, body_r.inflate(8, 8), radius=10)

        self._rect(s, monster.color, body_r, radius=8,
                   border=2, border_color=LGRAY if selectable else DGRAY)

        # Eyes
        pygame.draw.circle(s, RED, (cx - 18, cy + 28), 8)
        pygame.draw.circle(s, RED, (cx + 18, cy + 28), 8)
        pygame.draw.circle(s, BLACK, (cx - 18, cy + 28), 4)
        pygame.draw.circle(s, BLACK, (cx + 18, cy + 28), 4)

        # Name
        self._text(s, monster.name, self.f_small, WHITE, cx, ry - 16, center=True)

        # HP bar
        self._bar(s, rx - 10, ry + h + 6, w + 20, 16,
                  monster.hp, monster.max_hp, RED,
                  label=f"{monster.hp}/{monster.max_hp}")

        # Block
        if monster.block:
            self._text(s, f"🛡 {monster.block}", self.f_small, BLUE,
                       cx, ry + h + 30, center=True)

        # Intent bubble
        intent_type, intent_val, _ = monster.current_intent()
        from src.monster import (INT_ATTACK, INT_DEFEND, INT_BUFF,
                                 INT_DEBUFF, INT_SLEEP, INTENT_SYMBOLS)
        symbol = INTENT_SYMBOLS.get(intent_type, "?")
        icol = {
            INT_ATTACK: RED, INT_DEFEND: BLUE, INT_BUFF: ORANGE,
            INT_DEBUFF: PURPLE, INT_SLEEP: CYAN,
        }.get(intent_type, GRAY)

        bubble_r = pygame.Rect(cx - 36, ry - 60, 72, 36)
        self._rect(s, PANEL, bubble_r, radius=8,
                   border=2, border_color=icol)
        icon_str = f"{symbol}"
        if intent_type == INT_ATTACK and intent_val:
            # Compute real damage accounting for strength
            dmg = intent_val + monster.get_effect(EFF.STRENGTH, 0)
            icon_str = f"⚔ {dmg}"
        self._text(s, icon_str, self.f_small, icol,
                   bubble_r.centerx, bubble_r.centery, center=True)

        # Effects
        self._draw_effects(s, monster, rx - 10, ry + h + 52, max_width=w + 20)

        click_r = body_r.inflate(20, 20)
        return click_r

    def _draw_hand(self, s, player, combat, mpos):
        hand = player.hand
        n = len(hand)
        if n == 0:
            return

        total_w = n * CARD_W + (n - 1) * 12
        start_x = (SCREEN_W - total_w) // 2
        hand_y   = SCREEN_H - CARD_H - 18

        self.combat_card_rects = []
        for i, card in enumerate(hand):
            cx = start_x + i * (CARD_W + 12)
            cy = hand_y
            hovered = False
            cr = pygame.Rect(cx, cy, CARD_W, CARD_H)
            if cr.collidepoint(mpos):
                hovered = True

            grayed = not card.can_play(player.energy) or combat.phase != "player"
            selected = (card is combat.selected_card)
            r = self._draw_card(s, card, cx, cy, hovered=hovered,
                                selected=selected, grayed=grayed)
            self.combat_card_rects.append((card, r))

    def _draw_combat_overlay(self, s, phase):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        s.blit(overlay, (0, 0))
        if phase == "victory":
            self._text(s, "VICTORY!", self.f_title, GOLD,
                       SCREEN_W // 2, SCREEN_H // 2 - 40, center=True)
            self._text(s, "Click anywhere to continue", self.f_med, LGRAY,
                       SCREEN_W // 2, SCREEN_H // 2 + 30, center=True)
        else:
            self._text(s, "DEFEAT", self.f_title, RED,
                       SCREEN_W // 2, SCREEN_H // 2 - 40, center=True)
            self._text(s, "Click anywhere to return to menu", self.f_med, LGRAY,
                       SCREEN_W // 2, SCREEN_H // 2 + 30, center=True)

    # ─────────────────────────────────────────────────────────────────────────
    # REWARD SCREEN
    # ─────────────────────────────────────────────────────────────────────────

    def render_reward(self, game):
        s = self.screen
        s.fill(BG)
        mpos = pygame.mouse.get_pos()

        self._text(s, "Choose a Card Reward", self.f_title, GOLD,
                   SCREEN_W // 2, 80, center=True)
        self._text(s, "Click a card to add it to your deck, or Skip.",
                   self.f_med, LGRAY, SCREEN_W // 2, 140, center=True)

        cards = game.reward_cards
        n = len(cards)
        spacing = CARD_W + 30
        start_x = SCREEN_W // 2 - spacing * (n // 2) - (CARD_W // 2 if n % 2 == 0 else 0)
        cy = 220

        self.reward_card_rects = []
        for i, card in enumerate(cards):
            cx = start_x + i * spacing
            hovered = pygame.Rect(cx, cy, CARD_W, CARD_H).collidepoint(mpos)
            r = self._draw_card(s, card, cx, cy, hovered=hovered)
            self.reward_card_rects.append((card, r))

        # Skip button
        skip = pygame.Rect(SCREEN_W // 2 - 80, 440, 160, 46)
        self._button(s, "Skip Reward", skip, bg=DGRAY,
                     hover=skip.collidepoint(mpos))
        self.rest_heal_rect = skip   # reuse rect slot as "skip"

        pygame.display.flip()

    # ─────────────────────────────────────────────────────────────────────────
    # REST SCREEN
    # ─────────────────────────────────────────────────────────────────────────

    def render_rest(self, game):
        s = self.screen
        player = game.player
        s.fill(BG)
        mpos = pygame.mouse.get_pos()

        self._text(s, "Rest Site", self.f_title, GOLD,
                   SCREEN_W // 2, 100, center=True)

        # Campfire icon (simple)
        fc = (SCREEN_W // 2, 230)
        for i in range(5):
            h2 = 40 + i * 8
            col = _lerp_color((220, 80, 30), (220, 200, 50), i / 5)
            pygame.draw.polygon(s, col, [
                (fc[0] + (-20 + i * 4), fc[1] + 20),
                (fc[0], fc[1] - h2 + i * 5),
                (fc[0] + (20 - i * 4), fc[1] + 20),
            ])

        heal_btn = pygame.Rect(SCREEN_W // 2 - 180, 320, 340, 64)
        heal_pct  = int(player.max_hp * 0.30)
        new_hp    = min(player.max_hp, player.hp + heal_pct)
        self._button(s, f"Rest  (+{heal_pct} HP  →  {new_hp}/{player.max_hp})",
                     heal_btn, bg=DGREEN, hover=heal_btn.collidepoint(mpos))
        self.rest_heal_rect = heal_btn

        pygame.display.flip()

    # ─────────────────────────────────────────────────────────────────────────
    # GAME OVER
    # ─────────────────────────────────────────────────────────────────────────

    def render_game_over(self, _game=None):
        s = self.screen
        s.fill((8, 0, 0))
        mpos = pygame.mouse.get_pos()

        self._text(s, "YOU DIED", self.f_title, RED,
                   SCREEN_W // 2, 240, center=True)
        self._text(s, "The dungeon claims another soul...", self.f_med, GRAY,
                   SCREEN_W // 2, 320, center=True)

        btn = pygame.Rect(SCREEN_W // 2 - 120, 410, 240, 54)
        self._button(s, "Try Again", btn, bg=DRED, hover=btn.collidepoint(mpos))
        self.go_continue_rect = btn

        pygame.display.flip()

    # ─────────────────────────────────────────────────────────────────────────
    # VICTORY
    # ─────────────────────────────────────────────────────────────────────────

    def render_victory(self, _game=None):
        s = self.screen
        s.fill((0, 8, 0))
        mpos = pygame.mouse.get_pos()

        t = pygame.time.get_ticks() / 1000
        col = _lerp_color(GOLD, WHITE, (math.sin(t * 2) + 1) / 2)
        self._text(s, "VICTORY!", self.f_title, col,
                   SCREEN_W // 2, 230, center=True)
        self._text(s, "You have conquered the dungeon!", self.f_large, WHITE,
                   SCREEN_W // 2, 310, center=True)

        btn = pygame.Rect(SCREEN_W // 2 - 120, 410, 240, 54)
        self._button(s, "Play Again", btn, bg=DGREEN, hover=btn.collidepoint(mpos))
        self.go_continue_rect = btn

        pygame.display.flip()
