import random
from src import effects as EFF
from src.card import make_starter_deck


class Player:
    MAX_HAND = 10

    def __init__(self):
        self.max_hp     = 80
        self.hp         = 80
        self.block      = 0
        self.effects    = {}
        self.gold       = 99
        self.energy     = 3
        self.max_energy = 3

        deck = make_starter_deck()
        random.shuffle(deck)
        self.draw_pile    = deck
        self.hand         = []
        self.discard_pile = []
        self.exhaust_pile = []

    # ── damage / block ────────────────────────────────────────────────────────
    def take_damage(self, amount: int) -> int:
        """Returns HP actually lost."""
        blocked  = min(self.block, amount)
        self.block = max(0, self.block - amount)
        hp_dmg   = max(0, amount - blocked)
        self.hp  = max(0, self.hp - hp_dmg)
        return hp_dmg

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_block(self, amount: int):
        self.block += max(0, amount)

    # ── effects ───────────────────────────────────────────────────────────────
    def get_effect(self, name: str, default=0):
        return self.effects.get(name, default)

    def add_effect(self, name: str, amount: int):
        prev = self.effects.get(name, 0)
        self.effects[name] = prev + amount

    # ── card management ───────────────────────────────────────────────────────
    def draw_cards(self, n: int = 1):
        drawn = 0
        for _ in range(n):
            if len(self.hand) >= self.MAX_HAND:
                break
            if not self.draw_pile:
                if not self.discard_pile:
                    break
                self.draw_pile = self.discard_pile[:]
                self.discard_pile.clear()
                random.shuffle(self.draw_pile)
            if self.draw_pile:
                self.hand.append(self.draw_pile.pop(0))
                drawn += 1
        return drawn

    def discard_hand(self):
        self.discard_pile.extend(self.hand)
        self.hand.clear()

    def add_to_deck(self, card):
        """Add card to draw pile (shuffled in)."""
        self.discard_pile.append(card)

    # ── turn lifecycle ────────────────────────────────────────────────────────
    def start_turn(self):
        if not self.effects.get(EFF.BARRICADE):
            self.block = 0
        self.energy = self.max_energy
        # Berserk energy bonus
        if self.effects.get("berserk", 0) > 0:
            self.energy += 2
        # Demon Form strength
        if self.effects.get(EFF.DEMON_FORM, 0) > 0:
            self.add_effect(EFF.STRENGTH, self.effects[EFF.DEMON_FORM])

    def end_turn(self):
        self.discard_hand()
        # Metallicize
        if self.effects.get(EFF.METALLICIZE, 0) > 0:
            self.gain_block(self.effects[EFF.METALLICIZE])
        # Poison
        if self.effects.get(EFF.POISON, 0) > 0:
            self.hp = max(0, self.hp - self.effects[EFF.POISON])
            self.effects[EFF.POISON] = max(0, self.effects[EFF.POISON] - 1)
        # Decrement timed debuffs
        for eff in (EFF.VULNERABLE, EFF.WEAK):
            if self.effects.get(eff, 0) > 0:
                self.effects[eff] -= 1

    @property
    def is_alive(self):
        return self.hp > 0
