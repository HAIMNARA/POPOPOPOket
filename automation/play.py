"""
Pokemon Red Automation v5 - PyBoy 1.6.9
Strategy: Use PokemonRedExperiments save state (has_pokedex_nballs)
to skip intro/bedroom, start from Oak's Lab with Pokemon + Pokeballs.
Goal: Lab -> Pallet Town -> Route 1 -> Viridian City
"""
import time, json, traceback
from pathlib import Path
from pyboy import PyBoy
from pyboy.utils import WindowEvent

ROM = r"C:\Users\하미\Downloads\Pokemon - Red Version.gb"
SAVE_STATE = r"C:\Users\하미\AppData\Local\Temp\opencode\PokemonRedExperiments\has_pokedex_nballs.state"
RUN = Path(__file__).parent / "runs" / time.strftime("%Y%m%d_%H%M%S")

A_MAP=0xD35E; A_Y=0xD361; A_X=0xD362; A_BATTLE=0xD057
A_PARTY=0xD163; A_BADGES=0xD356; A_WY=0xFF4A; A_WALK=0xD00D
M_PALLET=0; M_VIRIDIAN=1; M_ROUTE1=12; M_LAB=40

BTN={
 'a':(WindowEvent.PRESS_BUTTON_A,WindowEvent.RELEASE_BUTTON_A),
 'b':(WindowEvent.PRESS_BUTTON_B,WindowEvent.RELEASE_BUTTON_B),
 'up':(WindowEvent.PRESS_ARROW_UP,WindowEvent.RELEASE_ARROW_UP),
 'down':(WindowEvent.PRESS_ARROW_DOWN,WindowEvent.RELEASE_ARROW_DOWN),
 'left':(WindowEvent.PRESS_ARROW_LEFT,WindowEvent.RELEASE_ARROW_LEFT),
 'right':(WindowEvent.PRESS_ARROW_RIGHT,WindowEvent.RELEASE_ARROW_RIGHT),
 'start':(WindowEvent.PRESS_BUTTON_START,WindowEvent.RELEASE_BUTTON_START),
}

class Player:
    def __init__(self):
        RUN.mkdir(parents=True, exist_ok=True)
        (RUN/"ss").mkdir(exist_ok=True)
        self.pb = PyBoy(ROM, window_type='headless')
        self.pb.tick()
        # Load save state
        with open(SAVE_STATE, 'rb') as f:
            self.pb.load_state(f)
        for _ in range(60): self.pb.tick()
        self.turn=0; self.phase="init"; self.events=[]; self.bugs=[]
        s = self.st()
        self.log(f"Loaded save: map={s['map']} y={s['y']} x={s['x']} party={s['party']}")

    def r(self, a): return self.pb.get_memory_value(a)
    def tick(self, n=1):
        for _ in range(n): self.pb.tick()
    def st(self):
        return dict(map=self.r(A_MAP),y=self.r(A_Y),x=self.r(A_X),
                    battle=self.r(A_BATTLE),party=self.r(A_PARTY),
                    badges=self.r(A_BADGES),wy=self.r(A_WY),
                    walk=self.r(A_WALK),fr=self.pb.frame_count)

    def press(self, btn, hold=10, settle=8):
        p, rl = BTN[btn]
        self.pb.send_input(p); self.tick(hold)
        self.pb.send_input(rl); self.tick(settle)

    def a(self, wait=40): self.press('a'); self.tick(wait)
    def b(self, wait=20): self.press('b'); self.tick(wait)

    def walk(self, d, hold=18):
        p, rl = BTN[d]
        self.pb.send_input(p); self.tick(hold)
        self.pb.send_input(rl)
        for _ in range(60):
            self.pb.tick()
            if self.r(A_WALK)==0: break
        self.tick(4)

    def has_dialog(self): return self.r(A_WY) < 144
    def clear_dialog(self, mx=60):
        for i in range(mx):
            if not self.has_dialog(): return i
            self.a(30)
        for i in range(10):
            if not self.has_dialog(): return mx
            self.b(20)
        return mx+10

    def ss(self, tag=""):
        n=f"{self.turn:04d}_{self.phase}_{tag}.png"
        self.pb.screen_image().save(str(RUN/"ss"/n)); return n

    def log(self, msg):
        s=self.st()
        line=f"[T{self.turn:04d}|{self.phase}] {msg} | m={s['map']} y={s['y']} x={s['x']} b={s['battle']} p={s['party']}"
        print(line); self.events.append(dict(turn=self.turn,phase=self.phase,msg=msg,state=s,ts=time.time()))

    def bug(self, title, detail, fix=""):
        b=dict(id=len(self.bugs)+1,turn=self.turn,phase=self.phase,
               title=title,detail=detail,fix=fix,state=self.st())
        self.bugs.append(b); print(f"  [BUG#{b['id']}] {title}: {detail}")

    # === EXIT LAB ===
    def do_exit_lab(self):
        self.phase = "exit_lab"
        s = self.st()
        self.log(f"Lab: y={s['y']} x={s['x']}")
        self.ss("lab_start")
        self.clear_dialog(10)

        # Walk down to exit lab door
        for i in range(15):
            self.walk('down')
            nm = self.r(A_MAP)
            ny = self.r(A_Y)
            if nm != M_LAB:
                self.log(f"Exited lab! map={nm} y={ny}")
                for _ in range(3):
                    self.walk('down')
                self.ss("lab_exit")
                return True
            if self.has_dialog():
                self.clear_dialog(5)
            if i % 3 == 0:
                self.log(f"Down#{i} y={ny} map={nm}")

        self.bug("lab_exit_fail", "Could not exit lab in 15 steps")
        return False

    # === PALLET TOWN -> ROUTE 1 ===
    def do_pallet_north(self):
        self.phase = "pallet"
        s = self.st()
        self.log(f"Pallet: y={s['y']} x={s['x']}")
        self.ss("pallet")

        # v6 finding: Lab blocks direct north. Walk LEFT to clear buildings first.
        self.log("Walking to town center then UP...")
        for _ in range(3):
            self.walk('left')
        self.log("Walking UP from center...")
        for i in range(25):
            self.walk('up')
            nm = self.r(A_MAP)
            ny = self.r(A_Y)
            if nm == M_ROUTE1 or nm == M_VIRIDIAN:
                self.log(f"Reached map={nm}! y={ny}")
                self.ss("route1_enter")
                return True
            if self.has_dialog():
                self.clear_dialog(10)
            if i % 5 == 0:
                self.log(f"North#{i} y={ny} x={self.r(A_X)} map={nm}")

        # Broader exploration if still stuck
        self.log("Still in Pallet, broader search...")
        for d_seq in [
            ['right','up','up','up','right','up','up'],
            ['left','up','up','left','up','up','up'],
            ['right','right','right','up','up','up','up','up'],
        ]:
            for d in d_seq:
                self.walk(d)
                nm = self.r(A_MAP)
                if nm != M_PALLET and nm != 0:
                    self.log(f"Found exit! map={nm}")
                    return True
                if self.has_dialog(): self.clear_dialog(5)

        self.bug("pallet_north_fail", f"y={self.r(A_Y)} x={self.r(A_X)}")
        return False

    # === ROUTE 1: auto-north to Viridian ===
    def do_route1(self):
        self.phase = "route1"
        s = self.st()
        self.log(f"Route 1: map={s['map']} y={s['y']} x={s['x']}")
        self.ss("route1_start")

        ly, lx = self.r(A_Y), self.r(A_X)
        stuck = 0
        battles = 0

        for step in range(500):
            m = self.r(A_MAP)

            # Victory check
            if m == M_VIRIDIAN:
                self.log(f"VIRIDIAN CITY REACHED! Step {step}, battles={battles}")
                self.ss("viridian_arrived")
                return True

            # Wild battle
            if self.r(A_BATTLE) != 0:
                battles += 1
                self.log(f"Wild battle #{battles} at step {step}")
                if battles <= 3:
                    self.ss(f"battle_{battles}")
                self._handle_battle()
                stuck = 0
                continue

            # Dialog
            if self.has_dialog():
                self.clear_dialog(5)
                continue

            # Walk north (main direction)
            self.walk('up')
            ny, nx = self.r(A_Y), self.r(A_X)

            # Stuck detection
            if ny == ly and nx == lx:
                stuck += 1
                if stuck >= 5:
                    pats=[
                        ['right','up','up','up','left','up'],
                        ['left','up','up','up','right','up'],
                        ['right','right','up','up','left','left','up','up'],
                        ['left','left','up','up','right','right','up','up'],
                        ['right','right','right','up','up','up','left','left','left','up'],
                    ]
                    pat=pats[(stuck//5)%len(pats)]
                    self.log(f"Stuck y={ny} x={nx}, pattern #{(stuck//5)%len(pats)}")
                    for d in pat:
                        self.walk(d)
                        if self.r(A_MAP)==M_VIRIDIAN:
                            self.log("Viridian via detour!")
                            self.ss("viridian_detour")
                            return True
                        if self.r(A_BATTLE)!=0:
                            self._handle_battle()
                            break
                    stuck = 0
            else:
                stuck = 0
                ly, lx = ny, nx

            if step % 25 == 0:
                self.log(f"Step {step}: m={m} y={ny} x={nx} battles={battles}")

            self.turn += 1

        self.bug("route1_timeout", f"500 steps, {battles} battles, no Viridian")
        return False

    def _handle_battle(self):
        """Handle wild battle: try RUN first, then FIGHT."""
        turns = 0
        while self.r(A_BATTLE) != 0 and turns < 50:
            if turns < 3:
                # Try to RUN (bottom-right option in battle menu)
                self.press('down'); self.tick(4)
                self.press('right'); self.tick(4)
                self.a(50)
                # Advance any narration
                for _ in range(6):
                    self.a(15)
                if self.r(A_BATTLE) == 0:
                    return  # Escaped!

            # FIGHT: press A twice (FIGHT menu -> first move)
            self.a(25)
            self.a(25)
            # Advance battle narration
            for _ in range(10):
                self.a(15)
            turns += 1

    # === SAVE ===
    def save(self):
        for nm, dt in [("events.json", self.events), ("bugs.json", self.bugs), ("final.json", self.st())]:
            with open(RUN/nm, 'w', encoding='utf-8') as f:
                json.dump(dt, f, ensure_ascii=False, indent=2)
        s = self.st()
        print(f"\n{'='*60}")
        print(f"Turns={self.turn} Events={len(self.events)} Bugs={len(self.bugs)}")
        print(f"map={s['map']} y={s['y']} x={s['x']} party={s['party']} badges={s['badges']}")
        print(f"Dir: {RUN}")
        print(f"{'='*60}")

    # === MAIN ===
    def run(self):
        t0 = time.time()
        try:
            # Phase 1: Exit Lab
            if self.r(A_MAP) == M_LAB:
                self.do_exit_lab()

            # Phase 2: Pallet Town -> north
            s = self.st()
            if s['map'] == M_PALLET or s['map'] == M_LAB:
                self.do_pallet_north()

            # Phase 3: Route 1 -> Viridian
            reached = self.do_route1()

            elapsed = time.time() - t0
            self.log(f"DONE: {elapsed:.1f}s | Viridian={reached}")
            self.ss("final")

        except Exception as e:
            self.bug("crash", f"{type(e).__name__}: {e}", traceback.format_exc())
            self.log(f"CRASH: {e}")
        finally:
            self.save()
            self.pb.stop()

if __name__ == "__main__":
    Player().run()
