import random
import copy
from src import effects as EFF

# ── Intent types ──────────────────────────────────────────────────────────────
INT_ATTACK  = "attack"
INT_DEFEND  = "defend"
INT_BUFF    = "buff"
INT_DEBUFF  = "debuff"
INT_SLEEP   = "sleep"
INT_ESCAPE  = "escape"
INT_UNKNOWN = "unknown"

INTENT_SYMBOLS = {
    INT_ATTACK:  "⚔",
    INT_DEFEND:  "🛡",
    INT_BUFF:    "⬆",
    INT_DEBUFF:  "⬇",
    INT_SLEEP:   "💤",
    INT_ESCAPE:  "💨",
    INT_UNKNOWN: "?",
}


class Monster:
    def __init__(self, name, max_hp, color=(180, 60, 60)):
        self.name       = name
        self.max_hp     = max_hp
        self.hp         = max_hp
        self.block      = 0
        self.effects    = {}
        self.color      = color
        self._turn      = 0   # internal turn counter
        self._pattern   = []  # list of (intent_type, value, action_fn)
        self._is_dead   = False

    # ── public ───────────────────────────────────────────────────────────────
    def intent_is_attack(self):
        return self.current_intent()[0] == INT_ATTACK

    def current_intent(self):
        if not self._pattern:
            return (INT_UNKNOWN, 0, None)
        return self._pattern[self._turn % len(self._pattern)]

    def take_turn(self, player, combat):
        if self._is_dead:
            return
        intent = self.current_intent()
        if intent[2]:
            intent[2](self, player, combat)
        self._turn += 1

    def take_damage(self, amount: int) -> int:
        """Returns actual HP lost."""
        blocked = min(self.block, amount)
        self.block = max(0, self.block - amount)
        hp_dmg = max(0, amount - blocked)
        self.hp = max(0, self.hp - hp_dmg)
        if self.hp <= 0:
            self._is_dead = True
        return hp_dmg

    def gain_block(self, amount: int):
        self.block += max(0, amount)

    def get_effect(self, name: str, default=0):
        return self.effects.get(name, default)

    def add_effect(self, name: str, amount: int):
        prev = self.effects.get(name, 0)
        self.effects[name] = prev + amount

    def start_turn(self):
        """Called at start of monster's turn: apply poison, etc."""
        if EFF.POISON in self.effects and self.effects[EFF.POISON] > 0:
            self.hp = max(0, self.hp - self.effects[EFF.POISON])
            self.effects[EFF.POISON] = max(0, self.effects[EFF.POISON] - 1)
        if self.hp <= 0:
            self._is_dead = True
        # Ritual
        if EFF.RITUAL in self.effects and self.effects[EFF.RITUAL] > 0:
            self.add_effect(EFF.STRENGTH, self.effects[EFF.RITUAL])

    def end_player_turn(self):
        """Called when player ends their turn (before monster acts)."""
        # Decrement timed debuffs
        for eff in (EFF.VULNERABLE, EFF.WEAK):
            if self.effects.get(eff, 0) > 0:
                self.effects[eff] -= 1
        self.block = 0   # monsters lose block end of round like player

    def copy(self):
        return copy.deepcopy(self)

    @property
    def is_alive(self):
        return self.hp > 0


# ── Shared helpers for action functions ──────────────────────────────────────

def _m_attack(monster, player, combat, base):
    combat.deal_damage(base, monster, player)

def _m_block(monster, amount):
    monster.gain_block(amount)


# ── Monster factories ─────────────────────────────────────────────────────────

def make_cultist():
    m = Monster("Cultist", random.randint(48, 54), color=(100, 50, 160))

    def incantation(self, player, combat):
        self.add_effect(EFF.RITUAL, 3)
        combat.log(f"{self.name} performs Incantation! Gains Ritual 3.")

    def dark_strike(self, player, combat):
        dmg = 6 + self.get_effect(EFF.STRENGTH)
        combat.log(f"{self.name} uses Dark Strike for {dmg}!")
        combat.deal_damage(6, self, player)

    m._pattern = [
        (INT_BUFF,   3, incantation),
        (INT_ATTACK, 6, dark_strike),
        (INT_ATTACK, 6, dark_strike),
        (INT_ATTACK, 6, dark_strike),
    ]
    return m


def make_jaw_worm():
    m = Monster("Jaw Worm", random.randint(40, 44), color=(80, 140, 60))

    def chomp(self, player, combat):
        combat.log(f"{self.name} uses Chomp!")
        combat.deal_damage(11, self, player)

    def bellow(self, player, combat):
        self.add_effect(EFF.STRENGTH, 3)
        self.gain_block(6)
        combat.log(f"{self.name} uses Bellow! +3 Strength, +6 Block.")

    def thrash(self, player, combat):
        combat.deal_damage(7, self, player)
        self.gain_block(5)
        combat.log(f"{self.name} uses Thrash!")

    m._pattern = [
        (INT_ATTACK, 11, chomp),
        (INT_BUFF,    0, bellow),
        (INT_ATTACK,  7, thrash),
        (INT_ATTACK,  7, thrash),
    ]
    return m


def make_louse():
    hp = random.randint(10, 15)
    m = Monster("Green Louse", hp, color=(60, 160, 60))

    def bite(self, player, combat):
        dmg = random.randint(5, 7)
        combat.log(f"{self.name} bites for {dmg}!")
        combat.deal_damage(dmg, self, player)

    def spit_web(self, player, combat):
        combat.apply_effect(player, EFF.WEAK, 1)
        combat.log(f"{self.name} spits web! Player is Weak.")

    m._pattern = [
        (INT_ATTACK, 6, bite),
        (INT_DEBUFF, 1, spit_web),
        (INT_ATTACK, 6, bite),
        (INT_ATTACK, 6, bite),
    ]
    return m


def make_acid_slime():
    m = Monster("Acid Slime", random.randint(65, 69), color=(100, 180, 60))

    def corrosive_spit(self, player, combat):
        from src.card import make_slimed
        combat.deal_damage(7, self, player)
        player.discard_pile.append(make_slimed())
        combat.log(f"{self.name} spits acid! Added Slimed to discard.")

    def tackle(self, player, combat):
        combat.deal_damage(10, self, player)
        combat.log(f"{self.name} tackles!")

    m._pattern = [
        (INT_DEBUFF, 7, corrosive_spit),
        (INT_ATTACK, 10, tackle),
        (INT_DEBUFF, 7, corrosive_spit),
        (INT_ATTACK, 10, tackle),
    ]
    return m


def make_fungal_beast():
    m = Monster("Fungal Beast", random.randint(22, 28), color=(160, 120, 50))

    def bite(self, player, combat):
        combat.deal_damage(6, self, player)
        combat.log(f"{self.name} bites!")

    def grow(self, player, combat):
        self.add_effect(EFF.STRENGTH, 3)
        combat.log(f"{self.name} grows! +3 Strength.")

    m._pattern = [
        (INT_ATTACK, 6, bite),
        (INT_BUFF,   0, grow),
        (INT_ATTACK, 6, bite),
        (INT_ATTACK, 6, bite),
    ]
    return m


def make_gremlin_nob():
    m = Monster("Gremlin Nob", random.randint(82, 86), color=(160, 80, 50))

    def bellow(self, player, combat):
        self.add_effect(EFF.STRENGTH, 2)
        combat.log(f"{self.name} bellows! +2 Strength.")

    def rush(self, player, combat):
        dmg = 14 + self.get_effect(EFF.STRENGTH)
        combat.deal_damage(14, self, player)
        combat.log(f"{self.name} rushes for {dmg}!")

    def skull_bash(self, player, combat):
        combat.deal_damage(6, self, player)
        combat.apply_effect(player, EFF.WEAK, 2)
        combat.log(f"{self.name} skull-bashes! +2 Weak.")

    m._pattern = [
        (INT_BUFF,   0, bellow),
        (INT_ATTACK, 14, rush),
        (INT_ATTACK, 6,  skull_bash),
        (INT_ATTACK, 14, rush),
    ]
    return m


def make_book_of_stabbing():
    m = Monster("Book of Stabbing", random.randint(160, 168), color=(60, 60, 160))

    def multi_stab(self, player, combat):
        times = random.randint(2, 5)
        for _ in range(times):
            combat.deal_damage(3, self, player)
        combat.log(f"{self.name} stabs {times} times!")

    def stab(self, player, combat):
        combat.deal_damage(21, self, player)
        combat.log(f"{self.name} unleashes a mega-stab!")

    m._pattern = [
        (INT_ATTACK, 9, multi_stab),
        (INT_ATTACK, 9, multi_stab),
        (INT_ATTACK, 21, stab),
    ]
    return m


# ── Elite monsters ────────────────────────────────────────────────────────────

def make_lagavulin():
    m = Monster("Lagavulin", random.randint(112, 116), color=(180, 140, 50))

    def sleep(self, player, combat):
        combat.log(f"{self.name} sleeps soundly...")

    def debilitate(self, player, combat):
        combat.apply_effect(player, EFF.STRENGTH, -2)
        combat.apply_effect(player, EFF.DEXTERITY, -2)
        combat.log(f"{self.name} wakes up! -2 Strength, -2 Dexterity.")

    def attack(self, player, combat):
        combat.deal_damage(18, self, player)
        combat.log(f"{self.name} smashes for 18!")

    m._pattern = [
        (INT_SLEEP, 0, sleep),
        (INT_SLEEP, 0, sleep),
        (INT_SLEEP, 0, sleep),
        (INT_DEBUFF, 0, debilitate),
        (INT_ATTACK, 18, attack),
        (INT_ATTACK, 18, attack),
    ]
    return m


def make_sentries():
    """Returns a list of 3 Sentry monsters."""
    sentries = []
    for i in range(3):
        m = Monster(f"Sentry {i+1}", random.randint(38, 42), color=(140, 140, 180))

        def beam(self, player, combat):
            combat.deal_damage(9, self, player)
            combat.log(f"{self.name} fires a beam!")

        def bolt(self, player, combat):
            from src.card import make_wound
            combat.deal_damage(18, self, player)
            player.discard_pile.append(make_wound())
            player.discard_pile.append(make_wound())
            combat.log(f"{self.name} fires a bolt! Added 2 Wounds.")

        turn_offset = i  # stagger their actions
        pat_full = [
            (INT_ATTACK, 9,  beam),
            (INT_ATTACK, 18, bolt),
        ]
        m._turn = turn_offset
        m._pattern = pat_full
        sentries.append(m)
    return sentries


# ── Boss ──────────────────────────────────────────────────────────────────────

def make_guardian():
    m = Monster("The Guardian", 250, color=(200, 200, 60))
    m._mode = "defensive"  # switches to "offensive" after taking enough damage

    def fierce_bash(self, player, combat):
        combat.deal_damage(36, self, player)
        combat.log(f"{self.name} uses Fierce Bash for 36!")

    def vent_steam(self, player, combat):
        combat.deal_damage(5, self, player)
        combat.apply_effect(player, EFF.WEAK, 2)
        combat.apply_effect(player, EFF.VULNERABLE, 2)
        combat.log(f"{self.name} vents steam! Deals 5, Weak+Vuln.")

    def whirlwind(self, player, combat):
        for _ in range(4):
            combat.deal_damage(5, self, player)
        combat.log(f"{self.name} whirls! 4×5 damage.")

    def roll_attack(self, player, combat):
        for _ in range(3):
            combat.deal_damage(9, self, player)
        combat.log(f"{self.name} rolls! 3×9 damage.")

    def charging_up(self, player, combat):
        combat.log(f"{self.name} charges up...")

    # Pattern alternates based on mode (offensive/defensive)
    m._defensive_pattern = [
        (INT_ATTACK, 5, vent_steam),
        (INT_UNKNOWN, 0, charging_up),
        (INT_ATTACK, 20, whirlwind),
        (INT_ATTACK, 5, vent_steam),
    ]
    m._offensive_pattern = [
        (INT_ATTACK, 36, fierce_bash),
        (INT_ATTACK, 27, roll_attack),
        (INT_ATTACK, 36, fierce_bash),
    ]
    m._pattern = m._defensive_pattern

    # Override take_damage to trigger mode switch
    original_take_damage = m.take_damage

    def guardian_take_damage(amount):
        result = original_take_damage(amount)
        if m._mode == "defensive" and m.hp < m.max_hp * 0.5:
            m._mode = "offensive"
            m._pattern = m._offensive_pattern
            m.gain_block(20)
            m._turn = 0
        return result

    m.take_damage = guardian_take_damage
    return m


# ── Encounter tables (room type → list of monster groups) ─────────────────────

FLOOR1_ENCOUNTERS = [
    lambda: [make_cultist()],
    lambda: [make_jaw_worm()],
    lambda: [make_louse(), make_louse()],
    lambda: [make_acid_slime()],
    lambda: [make_fungal_beast(), make_fungal_beast()],
]

FLOOR2_ENCOUNTERS = [
    lambda: [make_gremlin_nob()],
    lambda: [make_book_of_stabbing()],
    lambda: [make_jaw_worm(), make_louse()],
    lambda: [make_acid_slime(), make_acid_slime()],
]

ELITE_ENCOUNTERS = [
    lambda: [make_lagavulin()],
    lambda: make_sentries(),
]

BOSS_ENCOUNTER = lambda: [make_guardian()]


def random_encounter(floor: int):
    if floor == 1:
        return random.choice(FLOOR1_ENCOUNTERS)()
    return random.choice(FLOOR2_ENCOUNTERS)()


def random_elite():
    return random.choice(ELITE_ENCOUNTERS)()


def boss_encounter():
    return BOSS_ENCOUNTER()
