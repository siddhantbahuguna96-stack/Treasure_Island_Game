# Treasure Island — Combat Edition
# Adds HP/hearts, simple combat, items, random events, and checkpoint snapshots.

import sys, random
from textwrap import fill

# ------------- UTIL -------------

def say(text, width=84):
    print(fill(text, width=width))

def ask(prompt, options):
    opts = {o:o for o in options}
    firsts = {}
    for o in options:
        f = o[0]
        firsts[f] = None if f in firsts else o
    while True:
        ans = input(f"{prompt} ({'/'.join(options)}): ").strip().lower()
        if ans in opts: return ans
        if len(ans) == 1 and ans in firsts and firsts[ans]: return firsts[ans]
        print("Choose:", ", ".join(options))

def clamp(a, lo, hi): return max(lo, min(hi, a))

# ------------- GAME STATE -------------

class State:
    def __init__(self):
        self.hp_max = 10
        self.hp = self.hp_max
        self.inventory = set()
        self.consumables = {"berries": 0}  # heal 3 each
        self.gold = 0
        self.weapon = "fists"  # or "spear"
        self.checkpoint_fn = None
        self.snapshot = None

    # attack ranges by weapon
    def roll_damage(self):
        if self.weapon == "spear":
            return random.randint(2, 5)
        return random.randint(1, 3)

    def save_checkpoint(self, fn):
        self.checkpoint_fn = fn
        # snapshot HP/inv so retry feel fair
        self.snapshot = (
            self.hp, self.inventory.copy(),
            self.consumables.copy(), self.gold, self.weapon
        )

    def restore_checkpoint(self):
        if self.snapshot:
            self.hp, inv, cons, self.gold, self.weapon = self.snapshot
            self.inventory = inv.copy()
            self.consumables = cons.copy()

state = State()

def show_status():
    inv = sorted(list(state.inventory))
    say(f"♥ HP {state.hp}/{state.hp_max} | Gold {state.gold} | "
        f"Weapon: {state.weapon} | Items: {inv} | Berries x{state.consumables['berries']}")

def game_over(msg="Game Over.") -> None:
    print("\n" + "-"*54)
    print(msg)
    print("-"*54)
    choice = ask("Retry from checkpoint, restart, or quit?", ["checkpoint", "restart", "quit"])
    if choice == "quit":
        sys.exit(0)
    if choice == "restart":
        play()
    else:
        state.restore_checkpoint()
        state.checkpoint_fn()

# ------------- RANDOM EVENTS -------------

def random_event(pool):
    """
    pool: list of (weight, callable or string message)
    returns True if scene should end early (e.g., combat killed you or moved you)
    """
    total = sum(w for w,_ in pool)
    r = random.uniform(0, total)
    upto = 0
    for w, ev in pool:
        if upto + w >= r:
            if callable(ev):
                return ev()
            else:
                say(ev)
                return False
        upto += w
    return False

def find_berries():
    n = random.randint(1,2)
    state.consumables["berries"] += n
    say(f"You find wild **berries** (x{n}). They smell sweet—might restore a little vigor.")
    return False

def find_spear():
    if state.weapon != "spear":
        state.weapon = "spear"
        say("You lash driftwood to a sharpened bone: **You crafted a spear** (better damage).")
    else:
        say("You find another worn pole—not better than your current spear.")
    return False

def serpent_ambush():
    say("A **lake serpent** erupts from the water!")
    enemy = {"name":"Lake Serpent", "hp": 8, "min":1, "max":4, "flee":0.35}
    combat(enemy)
    return False

def beast_attack():
    say("Shadowy **beasts** prowl from the ruins!")
    enemy = {"name":"Beasts", "hp": 7, "min":1, "max":3, "flee":0.5}
    combat(enemy)
    return False

# ------------- COMBAT -------------

def heal_with_berries():
    if state.consumables["berries"] <= 0:
        print("You have no berries.")
        return False
    state.consumables["berries"] -= 1
    healed = 3
    state.hp = clamp(state.hp + healed, 0, state.hp_max)
    say(f"You eat berries and recover {healed} HP. (Now {state.hp}/{state.hp_max})")
    return True

def combat(enemy):
    # Simple loop until someone drops or you flee
    say(f"Combat begins vs **{enemy['name']}**!")
    defend_buff = False
    while state.hp > 0 and enemy["hp"] > 0:
        show_status()
        choice = ask("Action?", ["attack", "defend", "item", "flee"])
        print()
        if choice == "attack":
            dmg = state.roll_damage()
            enemy["hp"] -= dmg
            say(f"You strike with your {state.weapon} for {dmg} damage. ({enemy['name']} HP {max(0,enemy['hp'])})")
        elif choice == "defend":
            defend_buff = True
            say("You brace yourself, watching the enemy closely.")
        elif choice == "item":
            used = heal_with_berries()
            if not used:  # no item used—skip enemy free hit? no
                pass
        else:  # flee
            if random.random() < enemy["flee"]:
                say("You slip away into the shadows!")
                return
            else:
                say("You try to flee but stumble—no escape!")

        # enemy turn if still alive
        if enemy["hp"] > 0:
            edmg = random.randint(enemy["min"], enemy["max"])
            if defend_buff:
                edmg = max(0, edmg - 2)
            defend_buff = False
            state.hp -= edmg
            say(f"{enemy['name']} hits you for {edmg} damage. (HP {max(0,state.hp)}/{state.hp_max})")
        print()

    if state.hp <= 0:
        game_over("You were defeated.")
        return
    say(f"You defeated the {enemy['name']}!")
    # loot
    loot_gold = random.randint(1,2)
    state.gold += loot_gold
    say(f"You scavenge **{loot_gold} gold**.")

# ------------- SCENES -------------

def intro():
    random.seed()  # new run, new RNG
    print("\n" + "="*64)
    print("Welcome to Treasure Island — Combat Edition")
    print("Your mission is to find the treasure and live to tell the tale.")
    print("="*64 + "\n")
    state.save_checkpoint(crossroad)
    crossroad()

def crossroad():
    state.save_checkpoint(crossroad)
    say("A lonely crossroad beside an old signpost. Forest whispers to the **left**; "
        "a worn path dips to the **right**. You could also **look** around.")
    choice = ask("What do you do?", ["left", "right", "look"])
    if choice == "look":
        say("You scan the ground carefully.")
        # Random table while looking around the crossroad
        random_event([
            (5, "Nothing but ants and dust."),
            (6, find_berries),
            (6, lambda: (state.inventory.add("rope") or say("You find a sturdy **rope**."))),
            (3, beast_attack),
        ])
        return crossroad()
    if choice == "left":
        return lakeshore()
    else:
        return pitfall()

def pitfall():
    say("You follow the path to the right. The ground crumbles—")
    if "rope" in state.inventory:
        say("You anchor the rope to a root and climb out. At the bottom you noticed a glint: **+1 gold**.")
        state.gold += 1
        return crossroad()
    game_over("You fall into a deep hole. Game Over.")
    return None


def lakeshore():
    state.save_checkpoint(lakeshore)
    say("The forest thins into a moonlit **lake**. A small island rests far out.")
    # random shoreline events (low chance of serpent ambush)
    random_event([
        (8, lambda: False),
        (4, find_berries),
        (2, serpent_ambush),
    ])
    choice = ask("Do you **swim** across or **wait** by the shore?", ["swim", "wait"])
    if choice == "swim":
        # if player insists, there is a tiny chance to reach—but mostly trout/serpent
        if random.random() < 0.2 and "rope" in state.inventory:
            say("With the rope and grit, you barely make it through currents to the island.")
            return island()
        else:
            game_over("Hungry trout and icy water overwhelm you. Game Over.")
            return None
    else:
        return ferry()

def ferry():
    say("You wait. Mist rolls in. A silent skiff edges from the fog—"
        "a hooded ferryman extends a hand.")
    if state.gold > 0:
        choice = ask("**Pay** 1 gold, answer a **riddle**, or **decline**?", ["pay", "riddle", "decline"])
    else:
        choice = ask("You have no coin. Try a **riddle** or **decline**?", ["riddle", "decline"])

    if choice == "decline":
        say("You step back. The skiff glides away.")
        return lakeshore()

    if choice == "pay" and state.gold > 0:
        state.gold -= 1
        say("The ferryman nods and delivers you safely to the island.")
        return island()

    # riddle path
    say('Ferryman: "Answer true and the lake will part for you."')
    say("RIDDLE: I speak without a mouth and hear without ears. I have nobody, "
        "but I come alive with wind. What am I?")
    if "echo" in input("Your answer: ").strip().lower():
        say("Ferryman: \"Correct.\" Passage is granted.")
        return island()
    else:
        say("Ferryman: \"Incorrect.\" The skiff fades into the fog.")
        # mild punishment: small serpent nip
        if random.random() < 0.5:
            say("Something brushes your ankle—teeth! You lose 2 HP escaping the shallows.")
            state.hp = clamp(state.hp - 2, 0, state.hp_max)
            if state.hp <= 0:
                game_over("You succumb to your wounds.")
                return None
        return lakeshore()

def island():
    state.save_checkpoint(island)
    say("You arrive unharmed at the island. A path leads to a lonely **house**. "
        "You could also **explore** the beach.")
    choice = ask("Where to?", ["house", "explore"])
    if choice == "explore":
        say("You comb the shoreline.")
        random_event([
            (5, find_berries),
            (5, find_spear),
            (3, lambda: (state.inventory.add("torch") or say("You find a waterproof **torch**."))),
            (3, serpent_ambush),
        ])
        return island()
    else:
        return house()

def house():
    state.save_checkpoint(house)
    say("Inside the ruined house, a hall ends in three doors: **red**, **blue**, **yellow**.")
    # chance for beasts before you choose
    random_event([
        (9, lambda: False),
        (3, beast_attack),
    ])
    choice = ask("Which door?", ["red", "blue", "yellow"])

    if choice == "red":
        # torch can mitigate burn via defend/berries, but still lethal; keep canonical loss
        game_over("You open the red door. A wall of flame engulfs the hall. Burned by fire. Game Over.")
        return None
    elif choice == "yellow":
        return treasure_room()
    else:  # blue
        if "torch" in state.inventory:
            say("You light your torch and peek in. Eyes glitter—beasts recoil from the flame. "
                "On the wall, a scrawl: 'Gold shines where patience wins.' You back out safely.")
            return house()
        else:
            # final combat chance to survive canonical 'beasts' end
            say("Darkness and low snarls surround you...")
            enemy = {"name":"Ravenous Beasts", "hp": 8, "min":1, "max":3, "flee":0.35}
            combat(enemy)
            if state.hp <= 0:  # died inside combat -> game_over happened
                return None
            say("You stagger back into the hall, bloodied but alive.")
            return house()

def treasure_room():
    say("The yellow door opens to a skylit chamber. A chest rests on a stone plinth.")
    say("Inside lies the **Treasure of the Patient** and a note: "
        "'Those who waited earned passage; those who looked found help.'")
    print("\n✨ YOU WIN! ✨\n")
    postgame()

def postgame():
    show_status()
    choice = ask("Play again?", ["yes", "no"])
    if choice == "yes":
        play()
    else:
        say("Thanks for playing, adventurer!")
        sys.exit(0)

# ------------- RUN -------------

def play():
    # fresh state each run
    state.hp_max = 10
    state.hp = state.hp_max
    state.inventory = set()
    state.consumables = {"berries": 0}
    state.gold = 0
    state.weapon = "fists"
    state.checkpoint_fn = intro
    state.snapshot = None
    intro()

if __name__ == "__main__":
    play()
