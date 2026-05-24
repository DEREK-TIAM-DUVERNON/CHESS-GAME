import pygame
import chess
import chess.engine
import json
import os
import hashlib
import webbrowser
import sys
import time

# ─────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────
pygame.init()
pygame.mixer.init()

INFO        = pygame.display.Info()
SW, SH      = INFO.current_w, INFO.current_h
screen      = pygame.display.set_mode((SW, SH), pygame.FULLSCREEN)
pygame.display.set_caption("Derek's Chess")

# ─────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────
BASE        = os.path.dirname(os.path.abspath(__file__))
PIECES_DIR  = os.path.join(BASE, "assets", "images", "pieces")
SOUNDS_DIR  = os.path.join(BASE, "assets", "sounds")
DATA_DIR    = os.path.join(BASE, "data")
PLAYERS_F   = os.path.join(DATA_DIR, "players.json")
ABOUT_F     = os.path.join(BASE, "about.html")

os.makedirs(DATA_DIR, exist_ok=True)

print("SOUNDS DIR: ", SOUNDS_DIR)
for file in os.listdir(SOUNDS_DIR):
    print(file)

# ─────────────────────────────────────────
#  COLOURS  (chess.com dark palette)
# ─────────────────────────────────────────
C_BG        = (22,  21,  18)
C_PANEL     = (38,  36,  33)
C_LIGHT_SQ  = (238, 216, 192)
C_DARK_SQ   = (101,  72,  56)
C_HIGHLIGHT = (246, 246, 105, 180)
C_MOVE_DOT  = (0,   0,   0,  60)
C_CHECK     = (220,  50,  50, 160)
C_WHITE     = (255, 255, 255)
C_GREY      = (160, 160, 160)
C_GOLD      = (212, 175,  55)
C_GREEN     = ( 81, 168,  94)
C_RED       = (200,  50,  50)
C_BTN       = ( 50,  48,  44)
C_BTN_HOV   = ( 70,  68,  62)
C_ACCENT    = (129, 182,  76)   # chess.com green accent

# ─────────────────────────────────────────
#  FONTS
# ─────────────────────────────────────────
def font(size, bold=False):
    return pygame.font.SysFont("segoeui", size, bold=bold)

F_TITLE  = font(72, bold=True)
F_BIG    = font(42, bold=True)
F_MED    = font(30)
F_MED_B  = font(30, bold=True)
F_SM     = font(22)
F_XS     = font(18)

# ─────────────────────────────────────────
#  SOUNDS
# ─────────────────────────────────────────
def load_sound(name):
    for ext in (".ogg"):
        p = os.path.join(SOUNDS_DIR, name + ext)
        if os.path.exists(p):
            return pygame.mixer.Sound(p)
    return None

SND = {k: load_sound(k) for k in ("move", "capture", "check", "checkmate", "stalemate")}
print(SND)

def play(name):
    s = SND.get(name)
    if s:
        s.play()

# ─────────────────────────────────────────
#  PIECE IMAGES
# ─────────────────────────────────────────
PIECE_MAP = {
    (chess.PAWN,   True ): "wP", (chess.PAWN,   False): "bP",
    (chess.ROOK,   True ): "wR", (chess.ROOK,   False): "bR",
    (chess.KNIGHT, True ): "wN", (chess.KNIGHT, False): "bN",
    (chess.BISHOP, True ): "wB", (chess.BISHOP, False): "bB",
    (chess.QUEEN,  True ): "wQ", (chess.QUEEN,  False): "bQ",
    (chess.KING,   True ): "wK", (chess.KING,   False): "bK",
}

def load_pieces(sq_size):
    imgs = {}
    for key, name in PIECE_MAP.items():
        path = os.path.join(PIECES_DIR, name + ".png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            imgs[key] = pygame.transform.smoothscale(img, (sq_size, sq_size))
    return imgs

# ─────────────────────────────────────────
#  PLAYERS  (JSON)
# ─────────────────────────────────────────
def load_players():
    if os.path.exists(PLAYERS_F):
        with open(PLAYERS_F) as f:
            return json.load(f)
    return {"players": {}}

def save_players(data):
    with open(PLAYERS_F, "w") as f:
        json.dump(data, f, indent=2)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def register(username, password):
    data = load_players()
    if username in data["players"]:
        return False, "Username already exists!"
    data["players"][username] = {
        "password": hash_pw(password),
        "wins": 0, "losses": 0, "draws": 0, "games_played": 0
    }
    save_players(data)
    return True, "Account created!"

def login(username, password):
    data = load_players()
    p = data["players"].get(username)
    if not p:
        return False, "User not found!"
    if p["password"] != hash_pw(password):
        return False, "Wrong password!"
    return True, p

def update_record(username, result):
    data = load_players()
    p = data["players"].get(username)
    if not p:
        return
    p["games_played"] += 1
    if result == "win":   p["wins"]   += 1
    elif result == "loss": p["losses"] += 1
    else:                  p["draws"]  += 1
    save_players(data)

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def draw_text(surf, text, fnt, color, cx, cy, anchor="center"):
    s = fnt.render(text, True, color)
    r = s.get_rect()
    if anchor == "center": r.center = (cx, cy)
    elif anchor == "topleft": r.topleft = (cx, cy)
    elif anchor == "topright": r.topright = (cx, cy)
    surf.blit(s, r)
    return r

def draw_rect_rounded(surf, color, rect, radius=12):
    pygame.draw.rect(surf, color, rect, border_radius=radius)

class Button:
    def __init__(self, text, cx, cy, w=320, h=58, fnt=None, color=None, hover=None, text_color=None, radius=10):
        self.text = text
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (cx, cy)
        self.fnt = fnt or F_MED_B
        self.color = color or C_BTN
        self.hover = hover or C_BTN_HOV
        self.text_color = text_color or C_WHITE
        self.radius = radius

    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        col = self.hover if self.rect.collidepoint(mx, my) else self.color
        draw_rect_rounded(surf, col, self.rect, self.radius)
        draw_text(surf, self.text, self.fnt, self.text_color, self.rect.centerx, self.rect.centery)

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.rect.collidepoint(event.pos)

class TextInput:
    def __init__(self, cx, cy, w=340, h=50, placeholder="", secret=False):
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (cx, cy)
        self.text = ""
        self.placeholder = placeholder
        self.secret = secret
        self.active = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_TAB):
                self.text += event.unicode

    def draw(self, surf):
        border = C_ACCENT if self.active else C_GREY
        pygame.draw.rect(surf, C_PANEL, self.rect, border_radius=8)
        pygame.draw.rect(surf, border, self.rect, 2, border_radius=8)
        display = ("●" * len(self.text)) if self.secret else self.text
        if display:
            draw_text(surf, display, F_MED, C_WHITE, self.rect.x + 12, self.rect.centery, "topleft")
        else:
            draw_text(surf, self.placeholder, F_MED, C_GREY, self.rect.x + 12, self.rect.centery, "topleft")

def format_time(secs):
    secs = max(0, int(secs))
    return f"{secs // 60:02d}:{secs % 60:02d}"

# ─────────────────────────────────────────
#  ABOUT HTML  (auto-generated if missing)
# ─────────────────────────────────────────
def ensure_about():
    if os.path.exists(ABOUT_F):
        return
    html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>About Derek's Chess</title>
<style>
  body{margin:0;background:#161514;color:#e0e0e0;font-family:'Segoe UI',sans-serif;display:flex;flex-direction:column;align-items:center;padding:40px 20px}
  h1{color:#81b64c;font-size:3em;margin-bottom:4px}
  h2{color:#d4af37;border-bottom:1px solid #333;padding-bottom:6px}
  .card{background:#262421;border-radius:12px;padding:24px 32px;max-width:700px;width:100%;margin:16px 0}
  .badge{display:inline-block;background:#81b64c;color:#161514;border-radius:6px;padding:2px 10px;font-weight:bold;font-size:.85em}
  a{color:#81b64c}
  table{width:100%;border-collapse:collapse}
  td,th{padding:8px 12px;border-bottom:1px solid #333;text-align:left}
  th{color:#d4af37}
</style></head>
<body>
<h1>♟ Derek's Chess</h1>
<p style="color:#81b64c">A feature-rich chess game built with Python & Pygame</p>
<div class="card">
  <h2>🎮 How to Play</h2>
  <table>
    <tr><th>Action</th><th>Control</th></tr>
    <tr><td>Select piece</td><td>Left click</td></tr>
    <tr><td>Move piece</td><td>Click destination</td></tr>
    <tr><td>Quit game</td><td>ESC or window button</td></tr>
  </table>
</div>
<div class="card">
  <h2>⚙️ Game Modes</h2>
  <p><span class="badge">SOLO</span> Play against the built-in AI at Easy, Medium or Hard difficulty.</p>
  <p><span class="badge">MULTIPLAYER</span> Local PvP — board flips each turn. Login required to track your record.</p>
</div>
<div class="card">
  <h2>👨‍💻 Credits</h2>
  <p>Made by <strong>Derek</strong></p>
  <p>Piece assets: <a href="https://github.com/lichess-org/lila">Lichess (cburnett set)</a></p>
  <p>Sound assets: <a href="https://github.com/lichess-org/lila">Lichess standard sounds</a></p>
  <p>Chess engine: <a href="https://python-chess.readthedocs.io">python-chess</a></p>
</div>
</body></html>"""
    with open(ABOUT_F, "w") as f:
        f.write(html)

# ─────────────────────────────────────────
#  BOARD LAYOUT  (computed from screen)
# ─────────────────────────────────────────
BOARD_MARGIN_TOP = int(SH * 0.08)
BOARD_SIZE       = int(min(SW * 0.60, SH * 0.80))
SQ               = BOARD_SIZE // 8
BOARD_LEFT       = (SW - BOARD_SIZE) // 2
BOARD_TOP        = BOARD_MARGIN_TOP + int(SH * 0.05)
PANEL_X          = BOARD_LEFT + BOARD_SIZE + 30
PANEL_W          = SW - PANEL_X - 20

PIECES = load_pieces(SQ)

# ─────────────────────────────────────────
#  DRAW BOARD
# ─────────────────────────────────────────
def sq_rect(sq, flipped=False):
    col = chess.square_file(sq)
    row = chess.square_rank(sq)
    if flipped:
        col = 7 - col
        row = 7 - row
    draw_row = 7 - row
    x = BOARD_LEFT + col * SQ
    y = BOARD_TOP  + draw_row * SQ
    return pygame.Rect(x, y, SQ, SQ)

def pixel_to_sq(px, py, flipped=False):
    col = (px - BOARD_LEFT) // SQ
    row = (py - BOARD_TOP)  // SQ
    if not (0 <= col < 8 and 0 <= row < 8):
        return None
    rank = 7 - row
    file = col
    if flipped:
        rank = row
        file = 7 - col
    return chess.square(file, rank)

def draw_board(surf, board, selected=None, legal_moves=None, flipped=False, check_sq=None):
    for sq in chess.SQUARES:
        r = sq_rect(sq, flipped)
        col_idx = chess.square_file(sq)
        row_idx = chess.square_rank(sq)
        light = (col_idx + row_idx) % 2 == 1
        base_col = C_LIGHT_SQ if light else C_DARK_SQ

        # check highlight
        if check_sq is not None and sq == check_sq:
            pygame.draw.rect(surf, C_CHECK[:3], r)
        else:
            pygame.draw.rect(surf, base_col, r)

        # selected highlight
        if selected is not None and sq == selected:
            hl = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
            hl.fill(C_HIGHLIGHT)
            surf.blit(hl, r.topleft)

    # legal move dots
    if legal_moves:
        for mv in legal_moves:
            r = sq_rect(mv.to_square, flipped)
            if board.piece_at(mv.to_square):
                pygame.draw.rect(surf, (180, 130, 80), r, 5)
            else:
                dot = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                pygame.draw.circle(dot, C_MOVE_DOT, (SQ//2, SQ//2), SQ//6)
                surf.blit(dot, r.topleft)

    # pieces
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            key = (piece.piece_type, piece.color)
            img = PIECES.get(key)
            if img:
                r = sq_rect(sq, flipped)
                surf.blit(img, r.topleft)

    # coords
    for i in range(8):
        rank = i if flipped else 7 - i
        file = 7 - i if flipped else i
        light_r = (0 + rank) % 2 == 1
        light_f = (file + 0) % 2 == 1
        rc = C_DARK_SQ if light_r else C_LIGHT_SQ
        fc = C_LIGHT_SQ if light_f else C_DARK_SQ
        rs = F_XS.render(str(rank + 1), True, rc)
        fs = F_XS.render(chess.FILE_NAMES[file], True, fc)
        surf.blit(rs, (BOARD_LEFT + 3, BOARD_TOP + i * SQ + 3))
        surf.blit(fs, (BOARD_LEFT + (i + 1) * SQ - 14, BOARD_TOP + BOARD_SIZE - 18))

# ─────────────────────────────────────────
#  SCREEN: MAIN MENU
# ─────────────────────────────────────────
def screen_menu():
    ensure_about()
    btns = [
        Button("♟  Solo vs AI",    SW//2, SH//2 - 80,  w=360, h=64, color=(50,100,50), hover=(70,130,70)),
        Button("👥  Multiplayer",   SW//2, SH//2 + 10,  w=360, h=64),
        Button("ℹ️   About",        SW//2, SH//2 + 100, w=360, h=64),
        Button("✕  Quit",          SW//2, SH//2 + 190, w=360, h=64, color=C_RED, hover=(230,70,70)),
    ]
    clock = pygame.time.Clock()
    while True:
        screen.fill(C_BG)
        # decorative board strip
        for i in range(8):
            for j in range(3):
                col = C_DARK_SQ if (i+j)%2==0 else C_LIGHT_SQ
                pygame.draw.rect(screen, col, (i*(SW//8), SH-80+j*30, SW//8+1, 31))

        draw_text(screen, "♟ Derek's Chess", F_TITLE, C_ACCENT, SW//2, SH//4)
        draw_text(screen, "Play. Learn. Conquer.", F_MED, C_GREY, SW//2, SH//4 + 70)

        for b in btns:
            b.draw(screen)

        draw_text(screen, "ESC to quit at any time", F_XS, C_GREY, SW//2, SH - 30)
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit(); sys.exit()
            if btns[0].clicked(e): return "solo"
            if btns[1].clicked(e): return "multi"
            if btns[2].clicked(e):
                webbrowser.open(ABOUT_F)
            if btns[3].clicked(e):
                pygame.quit(); sys.exit()
        clock.tick(60)

# ─────────────────────────────────────────
#  SCREEN: DIFFICULTY
# ─────────────────────────────────────────
def screen_difficulty():
    levels = [
        ("🟢  Easy",   1, (50,120,50),  (70,150,70)),
        ("🟡  Medium", 5, (130,110,30), (170,145,40)),
        ("🔴  Hard",   15,(130,40,40),  (170,60,60)),
    ]
    btns  = [Button(l[0], SW//2, SH//2 - 80 + i*90, w=340, h=64, color=l[2], hover=l[3]) for i,l in enumerate(levels)]
    back  = Button("← Back", SW//2, SH//2 + 200, w=220, h=50)
    clock = pygame.time.Clock()
    while True:
        screen.fill(C_BG)
        draw_text(screen, "Select Difficulty", F_BIG, C_WHITE, SW//2, SH//2 - 180)
        for i, b in enumerate(btns):
            b.draw(screen)
        back.draw(screen)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return None
            for i, b in enumerate(btns):
                if b.clicked(e): return levels[i][1]
            if back.clicked(e): return None
        clock.tick(60)

# ─────────────────────────────────────────
#  SCREEN: TIME CONTROL
# ─────────────────────────────────────────
def screen_time_control():
    options = [
        ("⚡ Bullet   1 min",  60),
        ("🔥 Blitz    3 min",  180),
        ("⏱ Blitz    5 min",  300),
        ("🚀 Rapid   10 min",  600),
        ("♟ Classical 15 min", 900),
        ("∞  No Timer",        0),
    ]
    btns = [Button(o[0], SW//2, SH//2 - 220 + i*80, w=360, h=58) for i,o in enumerate(options)]
    back = Button("← Back", SW//2, SH//2 + 270, w=220, h=50)
    clock = pygame.time.Clock()
    while True:
        screen.fill(C_BG)
        draw_text(screen, "Time Control", F_BIG, C_WHITE, SW//2, SH//2 - 300)
        for b in btns: b.draw(screen)
        back.draw(screen)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return None
            for i, b in enumerate(btns):
                if b.clicked(e): return options[i][1]
            if back.clicked(e): return None
        clock.tick(60)

# ─────────────────────────────────────────
#  SCREEN: LOGIN / REGISTER
# ─────────────────────────────────────────
def screen_auth(title="Login"):
    u_inp = TextInput(SW//2, SH//2 - 60,  placeholder="Username")
    p_inp = TextInput(SW//2, SH//2 + 10,  placeholder="Password", secret=True)
    confirm_btn = Button(title,       SW//2, SH//2 + 90,  w=280, h=54, color=(50,100,50), hover=(70,130,70))
    toggle_btn  = Button("Register" if title=="Login" else "Login", SW//2, SH//2+160, w=280, h=50)
    back_btn    = Button("← Back",   SW//2, SH//2+230, w=220, h=46)
    msg = ""
    mode = title
    clock = pygame.time.Clock()
    while True:
        screen.fill(C_BG)
        draw_text(screen, mode, F_BIG, C_WHITE, SW//2, SH//2 - 160)
        u_inp.draw(screen)
        p_inp.draw(screen)
        confirm_btn.text = mode
        confirm_btn.draw(screen)
        toggle_btn.text = "Switch to Register" if mode=="Login" else "Switch to Login"
        toggle_btn.draw(screen)
        back_btn.draw(screen)
        if msg:
            col = C_GREEN if "created" in msg or "success" in msg.lower() else C_RED
            draw_text(screen, msg, F_SM, col, SW//2, SH//2 + 290)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return None, None
            u_inp.handle(e); p_inp.handle(e)
            if confirm_btn.clicked(e):
                u, p = u_inp.text.strip(), p_inp.text.strip()
                if not u or not p:
                    msg = "Please fill in both fields."
                elif mode == "Login":
                    ok, res = login(u, p)
                    if ok: return u, res
                    else:  msg = res
                else:
                    ok, res = register(u, p)
                    msg = res
                    if ok: mode = "Login"
            if toggle_btn.clicked(e):
                mode = "Register" if mode=="Login" else "Login"
                msg = ""
            if back_btn.clicked(e): return None, None
        clock.tick(60)

# ─────────────────────────────────────────
#  SCREEN: LEADERBOARD
# ─────────────────────────────────────────
def screen_leaderboard():
    data = load_players()
    players = sorted(data["players"].items(), key=lambda x: x[1]["wins"], reverse=True)
    back = Button("← Back", SW//2, SH - 80, w=220, h=50)
    clock = pygame.time.Clock()
    while True:
        screen.fill(C_BG)
        draw_text(screen, "🏆 Leaderboard", F_BIG, C_GOLD, SW//2, 60)
        headers = ["Rank", "Player", "Wins", "Losses", "Draws", "Games"]
        col_x   = [SW//2 - 450 + i*160 for i in range(6)]
        for i, h in enumerate(headers):
            draw_text(screen, h, F_SM, C_GOLD, col_x[i], 130, "topleft")
        pygame.draw.line(screen, C_GREY, (SW//2-460, 158), (SW//2+460, 158), 1)
        for rank, (name, stats) in enumerate(players[:15], 1):
            y = 170 + rank * 38
            row_col = C_ACCENT if rank == 1 else C_WHITE
            vals = [str(rank), name, str(stats["wins"]), str(stats["losses"]), str(stats["draws"]), str(stats["games_played"])]
            for i, v in enumerate(vals):
                draw_text(screen, v, F_SM, row_col, col_x[i], y, "topleft")
        back.draw(screen)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: return
            if back.clicked(e): return
        clock.tick(60)

# ─────────────────────────────────────────
#  GAME OVER OVERLAY
# ─────────────────────────────────────────
def game_over_screen(message, sub=""):
    overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))
    box = pygame.Rect(SW//2-300, SH//2-130, 600, 260)
    draw_rect_rounded(screen, C_PANEL, box, 18)
    pygame.draw.rect(screen, C_ACCENT, box, 3, border_radius=18)
    draw_text(screen, message, F_BIG, C_WHITE, SW//2, SH//2 - 60)
    if sub:
        draw_text(screen, sub, F_MED, C_GREY, SW//2, SH//2)
    draw_text(screen, "Press any key or click to continue", F_SM, C_GREY, SW//2, SH//2 + 70)
    pygame.display.flip()
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

# ─────────────────────────────────────────
#  PROMOTION DIALOG
# ─────────────────────────────────────────
def promotion_dialog(color):
    choices = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    names   = ["Queen", "Rook", "Bishop", "Knight"]
    btns    = [Button(names[i], SW//2 - 220 + i*150, SH//2, w=130, h=54) for i in range(4)]
    clock   = pygame.time.Clock()
    overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
    overlay.fill((0,0,0,160))
    while True:
        screen.blit(overlay, (0,0))
        draw_text(screen, "Promote Pawn", F_BIG, C_WHITE, SW//2, SH//2 - 70)
        for i, b in enumerate(btns):
            b.draw(screen)
            key = (choices[i], color == chess.WHITE)
            img = PIECES.get(key)
            if img:
                small = pygame.transform.smoothscale(img, (40,40))
                screen.blit(small, (b.rect.x + 10, b.rect.y + 7))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            for i, b in enumerate(btns):
                if b.clicked(e): return choices[i]
        clock.tick(60)

# ─────────────────────────────────────────
#  DRAW SIDE PANEL
# ─────────────────────────────────────────
def draw_panel(surf, board, times, turn, players, mode, captured):
    # background
    panel = pygame.Rect(PANEL_X - 10, BOARD_TOP - 10, PANEL_W, BOARD_SIZE + 20)
    draw_rect_rounded(surf, C_PANEL, panel, 14)

    # player info
    labels = [("⬛ Black", 0), ("⬜ White", 1)]
    for label, idx in labels:
        y = BOARD_TOP + 20 + idx * (BOARD_SIZE - 80)
        name = players[idx] if players[idx] else ("You" if idx == 1 else "AI" if mode=="solo" else "Player")
        draw_text(surf, label + "  " + name, F_MED_B, C_WHITE, PANEL_X + PANEL_W//2, y)
        # timer
        if times[idx] is not None:
            t_str = format_time(times[idx])
            t_col = C_RED if times[idx] < 30 else (C_ACCENT if turn == (idx == 1) else C_GREY)
            t_surf = F_BIG.render(t_str, True, t_col)
            surf.blit(t_surf, (PANEL_X + PANEL_W//2 - t_surf.get_width()//2, y + 36))

    # turn indicator
    cy = BOARD_TOP + BOARD_SIZE//2
    draw_text(surf, "Your turn" if (turn and mode=="solo") or mode=="multi" else "AI thinking...",
              F_MED_B, C_ACCENT, PANEL_X + PANEL_W//2, cy - 20)
    turn_label = "⬜ White" if board.turn == chess.WHITE else "⬛ Black"
    draw_text(surf, turn_label, F_MED, C_WHITE, PANEL_X + PANEL_W//2, cy + 20)

    # move count
    draw_text(surf, f"Move {board.fullmove_number}", F_SM, C_GREY, PANEL_X + PANEL_W//2, cy + 60)

# ─────────────────────────────────────────
#  CORE GAME LOOP
# ─────────────────────────────────────────
def run_game(mode="solo", depth=5, time_ctrl=300, p1=None, p2=None, p1_data=None, p2_data=None):
    board    = chess.Board()
    selected = None
    legal    = []
    flipped  = False
    clock    = pygame.time.Clock()

    # times: [black_secs, white_secs]  (None = no timer)
    if time_ctrl > 0:
        times = [float(time_ctrl), float(time_ctrl)]
    else:
        times = [None, None]

    last_tick = time.time()

    engine = None
    if mode == "solo":
        try:
            engine = chess.engine.SimpleEngine.popen_uci("stockfish")
        except Exception:
            engine = None   # fall back to python-chess built-in if stockfish missing

    def get_ai_move():
        if engine:
            limit = chess.engine.Limit(depth=depth)
            result = engine.play(board, limit)
            return result.move
        else:
            # fallback: random legal move
            import random
            moves = list(board.legal_moves)
            return random.choice(moves) if moves else None

    def check_sq():
        if board.is_check():
            return board.king(board.turn)
        return None

    running = True
    result_msg = ""

    while running:
        now  = time.time()
        dt   = now - last_tick
        last_tick = now

        # tick timer for current player
        turn_idx = 1 if board.turn == chess.WHITE else 0
        if times[turn_idx] is not None and not board.is_game_over():
            times[turn_idx] -= dt
            if times[turn_idx] <= 0:
                times[turn_idx] = 0
                winner = "White" if turn_idx == 0 else "Black"
                play("checkmate")
                game_over_screen(f"⏰ Time's up! {winner} wins on time!")
                running = False
                break

        # ── events ──
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                if e.key == pygame.K_f:
                    flipped = not flipped

            if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                # only allow human input when it's their turn
                human_turn = (mode == "multi") or (mode == "solo" and board.turn == chess.WHITE)
                if human_turn and not board.is_game_over():
                    sq = pixel_to_sq(e.pos[0], e.pos[1], flipped)
                    if sq is not None:
                        if selected is None:
                            piece = board.piece_at(sq)
                            if piece and piece.color == board.turn:
                                selected = sq
                                legal = [m for m in board.legal_moves if m.from_square == sq]
                        else:
                            move = None
                            for m in legal:
                                if m.to_square == sq:
                                    move = m
                                    break
                            if move:
                                # promotion
                                if board.piece_at(selected) and board.piece_at(selected).piece_type == chess.PAWN:
                                    rank = chess.square_rank(sq)
                                    if rank in (0, 7):
                                        promo = promotion_dialog(board.turn)
                                        move = chess.Move(selected, sq, promotion=promo)

                                captured_piece = board.piece_at(sq)
                                board.push(move)

                                if captured_piece:
                                    play("capture")
                                else:
                                    play("move")

                                if board.is_check():
                                    play("check")

                                # flip board in multiplayer
                                if mode == "multi":
                                    flipped = not flipped

                                selected = None
                                legal    = []
                            elif board.piece_at(sq) and board.piece_at(sq).color == board.turn:
                                selected = sq
                                legal = [m for m in board.legal_moves if m.from_square == sq]
                            else:
                                selected = None
                                legal    = []

        # ── AI move ──
        if mode == "solo" and board.turn == chess.BLACK and not board.is_game_over():
            ai_move = get_ai_move()
            if ai_move:
                captured_piece = board.piece_at(ai_move.to_square)
                board.push(ai_move)
                if captured_piece: play("capture")
                else:              play("move")
                if board.is_check(): play("check")

        # ── game over check ──
        if board.is_game_over() and not result_msg:
            outcome = board.outcome()
            if board.is_checkmate():
                winner = "White" if outcome.winner == chess.WHITE else "Black"
                play("checkmate")
                result_msg = f"♚ Checkmate! {winner} wins!"
                if mode == "multi":
                    if outcome.winner == chess.WHITE and p1:
                        update_record(p1, "win")
                        if p2: update_record(p2, "loss")
                    elif p2:
                        update_record(p2, "win")
                        if p1: update_record(p1, "loss")
            elif board.is_stalemate():
                play("stalemate")
                result_msg = "🤝 Stalemate! It's a draw."
                if mode == "multi":
                    if p1: update_record(p1, "draw")
                    if p2: update_record(p2, "draw")
            else:
                play("stalemate")
                result_msg = "🤝 Draw!"
                if mode == "multi":
                    if p1: update_record(p1, "draw")
                    if p2: update_record(p2, "draw")
            game_over_screen(result_msg)
            running = False

        # ── draw ──
        screen.fill(C_BG)
        draw_board(screen, board, selected, legal, flipped, check_sq())
        draw_panel(screen, board, times,
                   board.turn == chess.WHITE,
                   [p2 or "Black", p1 or "White"],
                   mode, [])
        draw_text(screen, "F = flip board  |  ESC = quit", F_XS, C_GREY, BOARD_LEFT + BOARD_SIZE//2, BOARD_TOP + BOARD_SIZE + 20)
        pygame.display.flip()
        clock.tick(60)

    if engine:
        engine.quit()

# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
def main():
    ensure_about()
    while True:
        choice = screen_menu()

        if choice == "solo":
            depth = screen_difficulty()
            if depth is None: continue
            tc    = screen_time_control()
            if tc  is None: continue
            run_game(mode="solo", depth=depth, time_ctrl=tc)

        elif choice == "multi":
            # login player 1
            draw_text(screen, "Player 1 — Login", F_BIG, C_WHITE, SW//2, SH//2 - 200)
            p1, p1d = screen_auth("Login")
            if p1 is None: continue
            # login player 2
            p2, p2d = screen_auth("Login")
            if p2 is None: continue
            tc = screen_time_control()
            if tc is None: continue
            run_game(mode="multi", time_ctrl=tc, p1=p1, p2=p2, p1_data=p1d, p2_data=p2d)
            screen_leaderboard()

if __name__ == "__main__":
    main()
