import copy
import random
from src import effects as EFF

# ── Card class ────────────────────────────────────────────────────────────────

class Card:
    def __init__(self, id, name, cost, kind, desc, rarity, fn,
                 exhausts=False, ethereal=False, needs_target=True, hits_all=False):
        self.id          = id
        self.name        = name
        self.cost        = cost      # -1 = X cost
        self.kind        = kind      # attack / skill / power / status / curse
        self.desc        = desc
        self.rarity      = rarity    # starter / common / uncommon / rare
        self._fn         = fn
        self.exhausts    = exhausts
        self.ethereal    = ethereal
        self.needs_target = needs_target  # False for self/all-target cards
        self.hits_all    = hits_all
        self.x_val       = 0        # filled just before play for X-cost cards

    # ── interface ─────────────────────────────────────────────────────────────
    def can_play(self, energy: int) -> bool:
        if self.cost == -1:
            return energy > 0
        return energy >= self.cost

    def play(self, combat):
        """Deduct energy and trigger effect.  combat.target must be set if needed."""
        if self.cost == -1:
            self.x_val = combat.player.energy
            combat.player.energy = 0
        else:
            combat.player.energy -= self.cost
        self._fn(self, combat)

    def copy(self):
        return copy.deepcopy(self)

    @property
    def color(self):
        from src.constants import C_ATTACK, C_SKILL, C_POWER, C_STATUS, C_CURSE
        return {
            "attack": C_ATTACK, "skill": C_SKILL, "power": C_POWER,
            "status": C_STATUS, "curse": C_CURSE,
        }.get(self.kind, (50, 50, 50))


# ── Helpers used inside effect lambdas ────────────────────────────────────────

def _dmg(c, combat, base, times=1):
    """Deal damage to combat.target (or all if hits_all)."""
    targets = combat.monsters if c.hits_all else (
        [combat.target] if combat.target else []
    )
    for t in targets:
        for _ in range(times):
            combat.deal_damage(base, combat.player, t)

def _block(c, combat, base):
    combat.gain_block(base, combat.player)

def _fx(c, combat, entity, name, amt):
    combat.apply_effect(entity, name, amt)


# ── Card factory functions ─────────────────────────────────────────────────────

def make_strike():
    def fn(c, ctx): _dmg(c, ctx, 6)
    return Card("strike","Strike",1,"attack",
                "Deal 6 damage.","starter",fn)

def make_defend():
    def fn(c, ctx): _block(c, ctx, 5)
    return Card("defend","Defend",1,"skill",
                "Gain 5 Block.","starter",fn, needs_target=False)

def make_bash():
    def fn(c, ctx):
        _dmg(c, ctx, 8)
        if ctx.target:
            _fx(c, ctx, ctx.target, EFF.VULNERABLE, 2)
    return Card("bash","Bash",2,"attack",
                "Deal 8 dmg.\nApply 2 Vulnerable.","starter",fn)

# ── common ────────────────────────────────────────────────────────────────────

def make_iron_wave():
    def fn(c, ctx):
        _dmg(c, ctx, 5)
        _block(c, ctx, 5)
    return Card("iron_wave","Iron Wave",1,"attack",
                "Deal 5 dmg.\nGain 5 Block.","common",fn)

def make_twin_strike():
    def fn(c, ctx): _dmg(c, ctx, 5, 2)
    return Card("twin_strike","Twin Strike",1,"attack",
                "Deal 5 dmg twice.","common",fn)

def make_pommel_strike():
    def fn(c, ctx):
        _dmg(c, ctx, 9)
        ctx.draw(1)
    return Card("pommel_strike","Pommel Strike",1,"attack",
                "Deal 9 dmg.\nDraw 1 card.","common",fn)

def make_anger():
    def fn(c, ctx):
        _dmg(c, ctx, 6)
        ctx.player.discard_pile.append(c.copy())
    return Card("anger","Anger",0,"attack",
                "Deal 6 dmg.\nAdd copy to discard.","common",fn)

def make_cleave():
    def fn(c, ctx): _dmg(c, ctx, 8)
    return Card("cleave","Cleave",1,"attack",
                "Deal 8 dmg to ALL enemies.","common",fn,
                needs_target=False, hits_all=True)

def make_thunderclap():
    def fn(c, ctx):
        _dmg(c, ctx, 4)
        for m in ctx.monsters:
            _fx(c, ctx, m, EFF.VULNERABLE, 1)
    return Card("thunderclap","Thunderclap",1,"attack",
                "Deal 4 dmg to ALL.\nApply 1 Vulnerable.","common",fn,
                needs_target=False, hits_all=True)

def make_shrug_it_off():
    def fn(c, ctx):
        _block(c, ctx, 8)
        ctx.draw(1)
    return Card("shrug_it_off","Shrug It Off",1,"skill",
                "Gain 8 Block.\nDraw 1 card.","common",fn, needs_target=False)

def make_flex():
    def fn(c, ctx):
        _fx(c, ctx, ctx.player, EFF.STRENGTH, 2)
        ctx.temp_strength += 2   # removed at end of turn
    return Card("flex","Flex",0,"skill",
                "Gain 2 Strength.\nLose it end of turn.","common",fn,
                needs_target=False)

def make_headbutt():
    def fn(c, ctx):
        _dmg(c, ctx, 9)
        if ctx.player.discard_pile:
            top = ctx.player.discard_pile.pop()
            ctx.player.draw_pile.insert(0, top)
            ctx.log(f"Returned {top.name} to top of draw.")
    return Card("headbutt","Headbutt",1,"attack",
                "Deal 9 dmg.\nPut top of discard\nonto draw pile.","common",fn)

# ── uncommon ──────────────────────────────────────────────────────────────────

def make_clothesline():
    def fn(c, ctx):
        _dmg(c, ctx, 12)
        if ctx.target:
            _fx(c, ctx, ctx.target, EFF.WEAK, 2)
    return Card("clothesline","Clothesline",2,"attack",
                "Deal 12 dmg.\nApply 2 Weak.","uncommon",fn)

def make_wild_strike():
    def fn(c, ctx):
        _dmg(c, ctx, 12)
        ctx.player.draw_pile.append(make_wound())
        random.shuffle(ctx.player.draw_pile)
        ctx.log("Shuffled Wound into draw pile.")
    return Card("wild_strike","Wild Strike",1,"attack",
                "Deal 12 dmg.\nShuffle a Wound\ninto your deck.","uncommon",fn)

def make_disarm():
    def fn(c, ctx):
        if ctx.target:
            _fx(c, ctx, ctx.target, EFF.STRENGTH, -2)
    return Card("disarm","Disarm",1,"skill",
                "Enemy loses 2 Strength.\nExhaust.","uncommon",fn, exhausts=True)

def make_spot_weakness():
    def fn(c, ctx):
        if ctx.target and ctx.target.intent_is_attack():
            _fx(c, ctx, ctx.player, EFF.STRENGTH, 3)
            ctx.log("Gained 3 Strength from Spot Weakness!")
        else:
            ctx.log("Enemy not attacking – no effect.")
    return Card("spot_weakness","Spot Weakness",1,"skill",
                "If enemy intends\nto attack, gain\n3 Strength.","uncommon",fn,
                needs_target=False)

def make_armaments():
    def fn(c, ctx):
        _block(c, ctx, 5)
        upgradeable = [cd for cd in ctx.player.hand if cd is not c and not cd.upgraded]
        if upgradeable:
            target_card = random.choice(upgradeable)
            target_card.upgraded = True
            target_card.name += "+"
            ctx.log(f"Upgraded {target_card.name}!")
    return Card("armaments","Armaments",1,"skill",
                "Gain 5 Block.\nUpgrade a random\ncard in hand.","uncommon",fn,
                needs_target=False)

def make_seeing_red():
    def fn(c, ctx):
        ctx.player.energy += 2
    return Card("seeing_red","Seeing Red",1,"skill",
                "Gain 2 Energy.\nExhaust.","uncommon",fn,
                needs_target=False, exhausts=True)

def make_battle_trance():
    def fn(c, ctx):
        ctx.draw(3)
        ctx.no_more_cards = True
    return Card("battle_trance","Battle Trance",0,"skill",
                "Draw 3 cards.\nCan't draw more\ncards this turn.","uncommon",fn,
                needs_target=False, exhausts=True)

# ── rare ──────────────────────────────────────────────────────────────────────

def make_whirlwind():
    def fn(c, ctx):
        for m in ctx.monsters:
            for _ in range(c.x_val):
                ctx.deal_damage(5, ctx.player, m)
    return Card("whirlwind","Whirlwind",-1,"attack",
                "Deal 5 dmg to ALL\nenemies X times.","rare",fn,
                needs_target=False, hits_all=True)

def make_demon_form():
    def fn(c, ctx):
        _fx(c, ctx, ctx.player, EFF.DEMON_FORM, 2)
    return Card("demon_form","Demon Form",3,"power",
                "At the start of\neach turn gain\n2 Strength.","rare",fn,
                needs_target=False)

def make_metallicize():
    def fn(c, ctx):
        _fx(c, ctx, ctx.player, EFF.METALLICIZE, 3)
    return Card("metallicize","Metallicize",1,"power",
                "At the end of\neach turn gain\n3 Block.","rare",fn,
                needs_target=False)

def make_inflame():
    def fn(c, ctx):
        _fx(c, ctx, ctx.player, EFF.STRENGTH, 2)
    return Card("inflame","Inflame",1,"power",
                "Gain 2 Strength.","rare",fn,
                needs_target=False)

# ── status cards (added to deck as penalty) ───────────────────────────────────

def make_wound():
    return Card("wound","Wound",1,"status",
                "Unplayable.","special", lambda c,ctx: None,
                needs_target=False)

def make_slimed():
    def fn(c, ctx):
        ctx.exhaust(c)
    return Card("slimed","Slimed",1,"status",
                "Exhaust.","special",fn, needs_target=False, exhausts=True)


# ── Reward pool (cards offered after combat) ──────────────────────────────────

COMMON_POOL = [
    make_iron_wave, make_twin_strike, make_pommel_strike,
    make_anger, make_cleave, make_thunderclap,
    make_shrug_it_off, make_flex, make_headbutt,
]
UNCOMMON_POOL = [
    make_clothesline, make_wild_strike, make_disarm,
    make_spot_weakness, make_armaments, make_seeing_red, make_battle_trance,
]
RARE_POOL = [
    make_whirlwind, make_demon_form, make_metallicize, make_inflame,
]


def make_starter_deck():
    deck = []
    for _ in range(5): deck.append(make_strike())
    for _ in range(4): deck.append(make_defend())
    deck.append(make_bash())
    return deck


def random_reward_cards(n=3):
    """Return n distinct Card instances for a post-combat reward."""
    roll = random.random()
    if roll < 0.55:
        pool = COMMON_POOL
    elif roll < 0.85:
        pool = UNCOMMON_POOL
    else:
        pool = RARE_POOL
    chosen = random.sample(pool, min(n, len(pool)))
    return [fn() for fn in chosen]
