import random
from src import effects as EFF


class Combat:
    """Manages the state of one card-battle encounter."""

    HAND_SIZE = 5

    def __init__(self, player, monsters: list):
        self.player   = player
        self.monsters = [m for m in monsters]  # copy list

        self.phase    = "player"   # "player" | "monster" | "victory" | "defeat"
        self.turn_num = 1

        # Card interaction
        self.selected_card  = None   # Card currently chosen by player
        self.target         = None   # Monster currently targeted
        self.no_more_cards  = False  # Battle Trance etc.
        self.temp_strength  = 0      # Flex: tracks bonus to remove at end of turn

        self._log: list[str] = []

    # ── logging ───────────────────────────────────────────────────────────────
    def log(self, msg: str):
        self._log.append(msg)
        if len(self._log) > 30:
            self._log.pop(0)

    # ── start ─────────────────────────────────────────────────────────────────
    def start(self):
        self.log("=== Combat begins! ===")
        self._start_player_turn()

    # ── turn management ───────────────────────────────────────────────────────
    def _start_player_turn(self):
        self.phase = "player"
        self.no_more_cards = False
        self.temp_strength = 0
        self.player.start_turn()
        self.player.draw_cards(self.HAND_SIZE)
        self.log(f"--- Turn {self.turn_num}: Your turn ---")

    def end_player_turn(self):
        if self.phase != "player":
            return
        # Remove Flex's temp strength
        if self.temp_strength > 0:
            self.player.add_effect(EFF.STRENGTH, -self.temp_strength)
        self.player.end_turn()
        self.phase = "monster"
        self._run_monster_turns()

    def _run_monster_turns(self):
        for m in self.monsters:
            if not m.is_alive:
                continue
            m.start_turn()
            m.take_turn(self.player, self)
            if not self.player.is_alive:
                self._end_combat(victory=False)
                return
        for m in self.monsters:
            m.end_player_turn()
        self.monsters = [m for m in self.monsters if m.is_alive]
        if not self.monsters:
            self._end_combat(victory=True)
            return
        self.turn_num += 1
        self._start_player_turn()

    def _end_combat(self, victory: bool):
        self.phase = "victory" if victory else "defeat"
        self.log("=== You won! ===" if victory else "=== Defeat... ===")

    # ── card playing ──────────────────────────────────────────────────────────
    def select_card(self, card):
        """Called when player clicks a card in hand."""
        if self.phase != "player":
            return False
        if not card.can_play(self.player.energy):
            return False
        if card.kind == "status" and card.id == "wound":
            return False   # Wound is unplayable
        self.selected_card = card
        if not card.needs_target:
            self.target = None
            self._play_selected()
        return True

    def select_target(self, monster):
        """Called when player clicks a monster while a card is selected."""
        if self.selected_card and monster in self.monsters and monster.is_alive:
            self.target = monster
            self._play_selected()

    def _play_selected(self):
        card = self.selected_card
        self.selected_card = None
        self.log(f"Playing: {card.name}")
        exhausted = card.exhausts
        card.play(self)
        # Check rage power
        if card.kind == "attack" and self.player.get_effect(EFF.RAGE) > 0:
            self.player.gain_block(self.player.get_effect(EFF.RAGE))
        # Move card
        if exhausted:
            self.player.exhaust_pile.append(card)
        elif card in self.player.hand:
            self.player.hand.remove(card)
            self.player.discard_pile.append(card)
        else:
            # Card was drawn/added mid-play (e.g. Anger copy) – already handled
            pass
        self.target = None
        # Remove from hand if not already removed (e.g. status cards)
        if card in self.player.hand:
            self.player.hand.remove(card)
            if not exhausted:
                self.player.discard_pile.append(card)
        self._check_monsters()

    def _check_monsters(self):
        self.monsters = [m for m in self.monsters if m.is_alive]
        if not self.monsters:
            self._end_combat(victory=True)

    # ── helpers called by card effects ────────────────────────────────────────
    def deal_damage(self, base: int, attacker, target):
        """Compute final damage (Strength, Weak, Vulnerable) and apply."""
        dmg = base + attacker.get_effect(EFF.STRENGTH, 0) if hasattr(attacker, 'get_effect') else base
        if isinstance(dmg, float):
            dmg = int(dmg)
        # Weak: attacker deals 25% less
        if attacker.effects.get(EFF.WEAK, 0) > 0:
            dmg = int(dmg * 0.75)
        # Vulnerable: target takes 50% more
        if target.effects.get(EFF.VULNERABLE, 0) > 0:
            dmg = int(dmg * 1.5)
        dmg = max(0, dmg)
        actual = target.take_damage(dmg)
        # Feel No Pain (exhaust triggers)
        return actual

    def gain_block(self, base: int, entity):
        bonus = entity.get_effect(EFF.DEXTERITY, 0) if hasattr(entity, 'get_effect') else 0
        entity.gain_block(max(0, base + bonus))

    def apply_effect(self, entity, name: str, amount: int):
        if hasattr(entity, 'add_effect'):
            entity.add_effect(name, amount)

    def draw(self, n: int):
        if not self.no_more_cards:
            self.player.draw_cards(n)

    def exhaust(self, card):
        if card in self.player.hand:
            self.player.hand.remove(card)
        self.player.exhaust_pile.append(card)
        # Feel No Pain
        if self.player.get_effect(EFF.FEEL_NO_PAIN, 0) > 0:
            self.player.gain_block(self.player.get_effect(EFF.FEEL_NO_PAIN))
