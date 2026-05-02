import pygame
import random
from src.constants import *
from src.player  import Player
from src.dungeon import DungeonMap, ROOM_MONSTER, ROOM_ELITE, ROOM_REST, ROOM_BOSS
from src.combat  import Combat
from src.monster import random_encounter, random_elite, boss_encounter
from src.card    import random_reward_cards
from src.renderer import Renderer


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen   = screen
        self.renderer = Renderer(screen)
        self.state    = ST_MENU

        # Populated on new game
        self.player:       Player       = None
        self.dungeon:      DungeonMap   = None
        self.combat:       Combat       = None
        self.reward_cards: list         = []
        self._pending_room = None       # room we just entered (for state return)

    # ─────────────────────────────────────────────────────────────────────────
    # Main loop hooks
    # ─────────────────────────────────────────────────────────────────────────

    def update(self, events: list):
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self._handle_click(ev.pos)
            if ev.type == pygame.KEYDOWN:
                self._handle_key(ev.key)

    def render(self):
        dispatch = {
            ST_MENU:     self.renderer.render_menu,
            ST_DUNGEON:  lambda: self.renderer.render_dungeon(self),
            ST_COMBAT:   lambda: self.renderer.render_combat(self),
            ST_REWARD:   lambda: self.renderer.render_reward(self),
            ST_REST:     lambda: self.renderer.render_rest(self),
            ST_GAMEOVER: self.renderer.render_game_over,
            ST_VICTORY:  self.renderer.render_victory,
        }
        fn = dispatch.get(self.state)
        if fn:
            fn()

    # ─────────────────────────────────────────────────────────────────────────
    # Click routing
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_click(self, pos):
        if self.state == ST_MENU:
            if self.renderer.menu_start_rect.collidepoint(pos):
                self._new_game()

        elif self.state == ST_DUNGEON:
            self._click_dungeon(pos)

        elif self.state == ST_COMBAT:
            self._click_combat(pos)

        elif self.state == ST_REWARD:
            self._click_reward(pos)

        elif self.state == ST_REST:
            self._click_rest(pos)

        elif self.state == ST_GAMEOVER:
            if self.renderer.go_continue_rect.collidepoint(pos):
                self.state = ST_MENU

        elif self.state == ST_VICTORY:
            if self.renderer.go_continue_rect.collidepoint(pos):
                self.state = ST_MENU

    def _handle_key(self, key):
        if self.state == ST_COMBAT and key == pygame.K_e:
            if self.combat and self.combat.phase == "player":
                self.combat.end_player_turn()
                self._check_combat_end()

    # ─────────────────────────────────────────────────────────────────────────
    # New game
    # ─────────────────────────────────────────────────────────────────────────

    def _new_game(self):
        self.player  = Player()
        self.dungeon = DungeonMap(floor=1)
        self.state   = ST_DUNGEON

    # ─────────────────────────────────────────────────────────────────────────
    # Dungeon
    # ─────────────────────────────────────────────────────────────────────────

    def _click_dungeon(self, pos):
        available = set(self.dungeon.available_rooms())
        for room, rect in self.renderer.dungeon_room_rects.items():
            if rect.collidepoint(pos) and room in available:
                self.dungeon.enter_room(room)
                self._pending_room = room
                self._resolve_room(room)
                break

    def _resolve_room(self, room):
        kind = room.kind
        if kind == ROOM_MONSTER:
            monsters = random_encounter(self.dungeon.floor)
            self._start_combat(monsters)
        elif kind == ROOM_ELITE:
            monsters = random_elite()
            self._start_combat(monsters)
        elif kind == ROOM_BOSS:
            monsters = boss_encounter()
            self._start_combat(monsters)
        elif kind == ROOM_REST:
            self.state = ST_REST
        else:
            # Treasure / Shop / Start: give reward cards
            self.reward_cards = random_reward_cards(3)
            self.state = ST_REWARD

    # ─────────────────────────────────────────────────────────────────────────
    # Combat
    # ─────────────────────────────────────────────────────────────────────────

    def _start_combat(self, monsters):
        self.player.block = 0
        # Collect all cards back into draw pile
        self.player.discard_pile.extend(self.player.hand)
        self.player.hand.clear()
        self.player.draw_pile += self.player.discard_pile
        self.player.discard_pile.clear()
        import random as _r
        _r.shuffle(self.player.draw_pile)

        self.combat = Combat(self.player, monsters)
        self.combat.start()
        self.state = ST_COMBAT

    def _click_combat(self, pos):
        combat = self.combat

        # Victory / Defeat overlay – any click advances
        if combat.phase in ("victory", "defeat"):
            if combat.phase == "victory":
                self.reward_cards = random_reward_cards(3)
                self.state = ST_REWARD
                if self._pending_room and self._pending_room.kind == ROOM_BOSS:
                    self.state = ST_VICTORY
            else:
                self.state = ST_GAMEOVER
            return

        if combat.phase != "player":
            return

        # End Turn button
        if self.renderer.combat_end_turn_rect.collidepoint(pos):
            combat.end_player_turn()
            self._check_combat_end()
            return

        # If a card is selected and waiting for target
        if combat.selected_card and combat.selected_card.needs_target:
            for m, rect in self.renderer.combat_monster_rects.items():
                if rect.collidepoint(pos) and m.is_alive:
                    combat.select_target(m)
                    self._check_combat_end()
                    return
            # Click elsewhere → deselect
            combat.selected_card = None
            return

        # Card click
        for card, rect in self.renderer.combat_card_rects:
            if rect.collidepoint(pos):
                combat.select_card(card)
                self._check_combat_end()
                return

    def _check_combat_end(self):
        if self.combat.phase in ("victory", "defeat"):
            # let the overlay render first; advance on next click
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Reward
    # ─────────────────────────────────────────────────────────────────────────

    def _click_reward(self, pos):
        # Skip button (reuses rest_heal_rect slot in renderer)
        if self.renderer.rest_heal_rect.collidepoint(pos):
            self.state = ST_DUNGEON
            return

        for card, rect in self.renderer.reward_card_rects:
            if rect.collidepoint(pos):
                self.player.add_to_deck(card)
                self.state = ST_DUNGEON
                return

    # ─────────────────────────────────────────────────────────────────────────
    # Rest
    # ─────────────────────────────────────────────────────────────────────────

    def _click_rest(self, pos):
        if self.renderer.rest_heal_rect.collidepoint(pos):
            heal = int(self.player.max_hp * 0.30)
            self.player.heal(heal)
            self.state = ST_DUNGEON
