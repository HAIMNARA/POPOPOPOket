"""
Pokemon Red Automation v4 - PyBoy 1.6.9
Fixes from v1-v3:
  v1: screen_image() not get_screen_image()
  v2: joyIgnore(0xCDCB)=172 permanently -> removed from gate
  v3: stairs at TOP-RIGHT (y=1-2, x=6-7), NOT bottom. Walk UP then RIGHT.
  v4: correct bedroom escape path + proper 1F->Pallet routing
"""
import time, json, traceback
from pathlib import Path
from pyboy import PyBoy
from pyboy.utils import WindowEvent

ROM = r"C:\Users\하미\Downloads\Pokemon - Red Version.gb"
RUN = Path(__file__).parent / "runs" / time.strftime("%Y%m%d_%H%M%S")

A_MAP=0xD35E; A_Y=0xD361; A_X=0xD362; A_BATTLE=0xD057
A_PARTY=0xD163; A_BADGES=0xD356; A_WY=0xFF4A; A_WALK=0xD00D
M_PALLET=0; M_VIRIDIAN=1; M_ROUTE1=12; M_HOUSE1F=37; M_HOUSE2F=38; M_LAB=40

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
        self.turn=0; self.phase="init"; self.events=[]; self.bugs=[]

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
        line=f"[T{self.turn:04d}|{self.phase}] {msg} | m={s['map']} y={s['y']} x={s['x']} b={s['battle']} p={s['party']} wy={s['wy']}"
        print(line); self.events.append(dict(turn=self.turn,phase=self.phase,msg=msg,state=s,ts=time.time()))

    def bug(self, title, detail, fix=""):
        b=dict(id=len(self.bugs)+1,turn=self.turn,phase=self.phase,
               title=title,detail=detail,fix=fix,state=self.st())
        self.bugs.append(b); print(f"  [BUG#{b['id']}] {title}: {detail}")

    # === TITLE + INTRO ===
    def do_title_and_intro(self):
        self.phase="title"
        self.log("Wait 2000fr"); self.tick(2000)
        self.ss("title")
        self.press('start'); self.tick(300)
        for _ in range(3): self.a(120)

        self.phase="intro"
        self.log("Oak intro...")
        for i in range(15): self.a(100)
        self.log("Name: DOWN+A")
        self.tick(100); self.press('down'); self.tick(50); self.a(100)
        for _ in range(8): self.a(100)
        self.log("Rival: DOWN+A")
        self.tick(100); self.press('down'); self.tick(50); self.a(100)
        for _ in range(30): self.a(80)
        self.log("Wait 2000fr for bedroom load")
        self.tick(2000)
        n=self.clear_dialog(60)
        self.log(f"Cleared {n} dlg")
        self.ss("intro_done")
        self.turn+=1

    # === BEDROOM: v4 fix - walk UP then RIGHT to stairs ===
    def do_bedroom(self):
        self.phase="bedroom"
        s=self.st()
        self.log(f"Bedroom y={s['y']} x={s['x']}")
        self.ss("bed_start")
        self.clear_dialog(10)

        if s['map'] != M_HOUSE2F:
            self.log(f"Not bedroom (m={s['map']}), skip"); return

        # v4 FIX: stairs at TOP-RIGHT (y~1-2, x~6-7)
        # Step 1: Walk UP 5 tiles (y=6 -> y=1)
        self.log("Walking UP toward stairs...")
        for i in range(6):
            prev = self.r(A_Y)
            self.walk('up')
            ny = self.r(A_Y); nm = self.r(A_MAP)
            self.log(f"Up#{i}: y={prev}->{ny} m={nm}")
            if nm != M_HOUSE2F:
                self.log(f"Map changed to {nm} going UP!"); self.ss("bed_exit_up"); return
            if self.has_dialog(): self.clear_dialog(3)

        # Step 2: Walk RIGHT until stairs (x=3 -> x=7+)
        self.log("Walking RIGHT toward stair area...")
        for i in range(6):
            prev = self.r(A_X)
            self.walk('right')
            nx = self.r(A_X); nm = self.r(A_MAP)
            self.log(f"Right#{i}: x={prev}->{nx} m={nm}")
            if nm != M_HOUSE2F:
                self.log(f"Map changed to {nm} going RIGHT!"); self.ss("bed_exit_right"); return
            if self.has_dialog(): self.clear_dialog(3)

        # Step 3: Try DOWN from top-right (stair might trigger going down)
        self.log("Trying DOWN from top-right...")
        for i in range(4):
            prev_y = self.r(A_Y)
            self.walk('down')
            ny = self.r(A_Y); nm = self.r(A_MAP)
            self.log(f"Down#{i}: y={prev_y}->{ny} m={nm}")
            if nm != M_HOUSE2F:
                self.log(f"Reached 1F! m={nm}"); self.ss("bed_exit_down"); return

        # Step 4: Walk systematically around top area
        self.log("Systematic top-area scan...")
        for d in ['left','down','right','right','down','left','left','down']:
            self.walk(d)
            nm = self.r(A_MAP)
            if nm != M_HOUSE2F:
                self.log(f"Found exit! m={nm}"); self.ss("bed_exit"); return

        self.ss("bed_stuck")
        self.bug("bedroom_v4","Still stuck after UP+RIGHT+DOWN scan")
        self.turn+=1

    # === HOUSE 1F ===
    def do_house1f(self):
        self.phase="house1f"
        s=self.st()
        self.log(f"1F: m={s['map']} y={s['y']} x={s['x']}")
        self.ss("1f_start")
        self.clear_dialog(5)

        if s['map'] != M_HOUSE1F: return

        # Walk DOWN to exit door, AVOID going back UP to stairs
        for i in range(12):
            self.walk('down')
            nm = self.r(A_MAP)
            ny = self.r(A_Y)
            self.log(f"1F down#{i}: y={ny} m={nm}")
            if nm == M_PALLET:
                self.log("Exited to Pallet!"); self.ss("pallet_arrive"); return
            if nm == M_HOUSE2F:
                # Went back upstairs! Walk away from stair and try down again
                self.log("Went back to 2F! Walking left then down...")
                self.walk('left'); self.walk('left')
                self.walk('down'); self.walk('down')
            if self.has_dialog(): self.clear_dialog(3)

        self.bug("1f_stuck","Could not exit house 1F")
        self.turn+=1

    # === PALLET TOWN ===
    def do_pallet(self):
        self.phase="pallet"
        s=self.st()
        self.log(f"Pallet: m={s['map']} y={s['y']} x={s['x']}")
        self.ss("pallet")

        # Walk south to trigger Oak cutscene
        for i in range(25):
            self.walk('down')
            if self.has_dialog():
                self.log(f"Oak event at step {i}!")
                self.clear_dialog(80)
                break
            if i%5==0: self.log(f"Step {i} y={self.r(A_Y)}")

        self.tick(200); self.clear_dialog(60)
        self.ss("oak_done")
        s=self.st()
        self.log(f"After Oak: m={s['map']} y={s['y']} x={s['x']}")
        self.turn+=1

    # === LAB ===
    def do_lab(self):
        self.phase="lab"
        s=self.st()
        self.log(f"Lab: m={s['map']} y={s['y']} x={s['x']} p={s['party']}")
        if s['party']>0: self.log("Have Pokemon already"); return
        self.ss("lab_start")
        self.clear_dialog(20)

        # Walk up to pokeball table
        for _ in range(6):
            self.walk('up')
            if self.has_dialog(): self.clear_dialog(5)

        # Interact with pokeballs (try center one for Squirtle)
        for attempt in range(5):
            self.a(80); self.clear_dialog(10)
            if self.r(A_PARTY)>0:
                self.log(f"Got starter attempt#{attempt}!"); break
            self.walk('right')

        self.clear_dialog(30)
        s=self.st()
        self.log(f"Party={s['party']}")
        if s['party']==0: self.bug("no_starter","party=0")
        self.ss("lab_done"); self.turn+=1

    # === RIVAL BATTLE ===
    def do_battle(self):
        self.phase="battle"
        for _ in range(40):
            self.a(25)
            if self.r(A_BATTLE)!=0: break
        if self.r(A_BATTLE)!=0:
            self.log("Battle!"); self.ss("bstart"); t=0
            while self.r(A_BATTLE)!=0 and t<60:
                self.a(20); self.a(20)
                for _ in range(10): self.a(15)
                t+=1
                if t%10==0: self.log(f"Turn {t}")
            self.log(f"Won in {t}"); self.ss("bend")
        else: self.log("No battle")
        self.clear_dialog(20); self.turn+=1

    # === ROUTE 1 ===
    def do_route1(self):
        self.phase="route1"
        s=self.st()
        self.log(f"Route1: m={s['map']} y={s['y']} x={s['x']}")

        # Exit lab/house if needed
        while self.r(A_MAP) in (M_LAB, M_HOUSE1F, M_HOUSE2F):
            self.walk('down')
            if self.has_dialog(): self.clear_dialog(3)
            if self.r(A_MAP)==M_HOUSE2F:
                self.walk('left'); self.walk('left'); self.walk('down')

        ly,lx=self.r(A_Y),self.r(A_X); stuck=0
        for step in range(500):
            m=self.r(A_MAP)
            if m==M_VIRIDIAN:
                self.log("VIRIDIAN CITY!"); self.ss("viridian"); return True
            if self.r(A_BATTLE)!=0:
                self.log(f"Wild @{step}"); self._wild(); stuck=0; continue
            if self.has_dialog(): self.clear_dialog(5); continue

            self.walk('up')
            ny,nx=self.r(A_Y),self.r(A_X)
            if ny==ly and nx==lx:
                stuck+=1
                if stuck>=8:
                    for d in ['right','up','up','left','up','up']:
                        self.walk(d)
                        if self.r(A_MAP)==M_VIRIDIAN: return True
                        if self.r(A_BATTLE)!=0: self._wild(); break
                    stuck=0
            else: stuck=0; ly,lx=ny,nx
            if step%30==0: self.log(f"Step {step} m={m} y={ny} x={nx}")
            self.turn+=1
        self.bug("timeout","500 steps"); return False

    def _wild(self):
        self.ss("wild"); t=0
        while self.r(A_BATTLE)!=0 and t<40:
            if t==0:
                self.press('down'); self.tick(6)
                self.press('right'); self.tick(6)
                self.a(50)
                for _ in range(5): self.a(15)
                if self.r(A_BATTLE)==0: self.log("Ran!"); return
            self.a(20); self.a(20)
            for _ in range(8): self.a(15)
            t+=1
        self.log(f"Wild: {t}t")

    def save(self):
        for nm,dt in [("events.json",self.events),("bugs.json",self.bugs),("final.json",self.st())]:
            with open(RUN/nm,'w',encoding='utf-8') as f: json.dump(dt,f,ensure_ascii=False,indent=2)
        s=self.st()
        print(f"\n{'='*60}")
        print(f"T={self.turn} E={len(self.events)} B={len(self.bugs)}")
        print(f"m={s['map']} y={s['y']} x={s['x']} p={s['party']} badges={s['badges']}")
        print(f"Dir: {RUN}")
        print(f"{'='*60}")

    def run(self):
        t0=time.time()
        try:
            self.do_title_and_intro()
            s=self.st()
            self.log(f"Post-intro m={s['map']} p={s['party']}")

            if s['map']==M_HOUSE2F: self.do_bedroom()
            s=self.st()
            if s['map']==M_HOUSE1F: self.do_house1f()
            s=self.st()
            if s['map'] in (M_PALLET,0): self.do_pallet()
            s=self.st()
            if s['map']==M_LAB or s['party']==0: self.do_lab()
            s=self.st()
            if s['party']>0: self.do_battle()
            reached=self.do_route1()
            self.log(f"Done {time.time()-t0:.1f}s viridian={reached}")
        except Exception as e:
            self.bug("crash",f"{type(e).__name__}: {e}",traceback.format_exc())
        finally:
            self.save(); self.pb.stop()

if __name__=="__main__": Player().run()
