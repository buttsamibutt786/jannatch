"""
╔══════════════════════════════════════════════════════╗
║       BAKES BY AYESHA — Professional POS v2.0       ║
║   Modern Artisanal Theme · Enhanced UI · Full Stack  ║
╚══════════════════════════════════════════════════════╝
Dependencies: pip install Pillow
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
import os
import shutil
import datetime
import csv
import hashlib
import math
import threading
import time

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    PILLOW_INSTALLED = True
except ImportError:
    PILLOW_INSTALLED = False
    print("WARNING: Pillow not installed. Run: pip install Pillow")

# ─── DATABASE SETUP ─────────────────────────────────────────────────────────
DB_PATH  = "ayesha_bakery.db"
IMG_DIR  = "bakery_images"
os.makedirs(IMG_DIR, exist_ok=True)

conn   = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.executescript('''
    CREATE TABLE IF NOT EXISTS products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT UNIQUE NOT NULL,
        price       REAL NOT NULL,
        stock       INTEGER DEFAULT 0,
        category    TEXT DEFAULT 'Uncategorized',
        image_path  TEXT,
        description TEXT,
        cost_price  REAL DEFAULT 0,
        barcode     TEXT UNIQUE,
        is_active   INTEGER DEFAULT 1,
        discount_pct REAL DEFAULT 0,
        is_bestseller INTEGER DEFAULT 0,
        is_new        INTEGER DEFAULT 0,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sales (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no  TEXT UNIQUE,
        subtotal    REAL,
        discount    REAL DEFAULT 0,
        tax         REAL DEFAULT 0,
        total       REAL,
        payment_method TEXT DEFAULT 'Cash',
        cashier     TEXT DEFAULT 'Ayesha',
        notes       TEXT,
        is_return   INTEGER DEFAULT 0,
        date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sale_items (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id     INTEGER REFERENCES sales(id),
        product_id  INTEGER REFERENCES products(id),
        product_name TEXT,
        quantity    INTEGER,
        unit_price  REAL,
        discount    REAL DEFAULT 0,
        total       REAL
    );
    CREATE TABLE IF NOT EXISTS coupons (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        TEXT UNIQUE NOT NULL,
        type        TEXT DEFAULT 'percent',
        value       REAL NOT NULL,
        min_purchase REAL DEFAULT 0,
        max_uses    INTEGER DEFAULT 999,
        used_count  INTEGER DEFAULT 0,
        expiry_date TEXT,
        is_active   INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS expenses (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        category    TEXT,
        amount      REAL,
        description TEXT,
        date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS customers (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT,
        phone       TEXT UNIQUE,
        email       TEXT,
        loyalty_pts INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT UNIQUE,
        password    TEXT,
        role        TEXT DEFAULT 'cashier',
        is_active   INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS stock_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id  INTEGER,
        product_name TEXT,
        change_qty  INTEGER,
        reason      TEXT,
        date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS returns (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        return_invoice  TEXT UNIQUE,
        original_invoice TEXT,
        refund_amount   REAL,
        reason          TEXT,
        cashier         TEXT,
        date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS return_items (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        return_id   INTEGER REFERENCES returns(id),
        product_id  INTEGER,
        product_name TEXT,
        quantity    INTEGER,
        unit_price  REAL,
        refund_total REAL
    );
''')

# ─── Migration: add new columns if not exist ─────────────────────────────────
for col, definition in [
    ("discount_pct",  "REAL DEFAULT 0"),
    ("is_bestseller", "INTEGER DEFAULT 0"),
    ("is_new",        "INTEGER DEFAULT 0"),
]:
    try:
        cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {definition}")
    except sqlite3.OperationalError:
        pass
conn.commit()

def _hash(p): return hashlib.sha256(p.encode()).hexdigest()

cursor.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)",
               ("Ayesha", _hash("admin123"), "admin"))
cursor.execute("INSERT OR IGNORE INTO coupons (code,type,value,min_purchase) VALUES (?,?,?,?)",
               ("AYESHA10","percent",10,0))
cursor.execute("INSERT OR IGNORE INTO coupons (code,type,value,min_purchase) VALUES (?,?,?,?)",
               ("WELCOME5","percent",5,0))
cursor.execute("INSERT OR IGNORE INTO coupons (code,type,value,min_purchase) VALUES (?,?,?,?)",
               ("FLAT50","flat",50,500))
conn.commit()

# Seed sample products with categories/badges
SAMPLE_PRODUCTS = [
    ("Butter Croissant",     280, 40, "Pastries",      0,  0, 1, 1),
    ("Sourdough Loaf",       450, 25, "Artisan Breads",0,  0, 1, 0),
    ("Red Velvet Cupcake",   180, 60, "Cupcakes",      15, 1, 1, 0),
    ("Chocolate Truffle Cake",1800,8, "Custom Cakes",  0,  0, 1, 1),
    ("Cheese Danish",        220, 35, "Pastries",      10, 1, 0, 0),
    ("Cinnamon Roll",        250, 30, "Pastries",      0,  0, 0, 1),
    ("Almond Croissant",     320, 28, "Pastries",      0,  0, 1, 0),
    ("Blueberry Muffin",     160, 50, "Muffins",       20, 1, 0, 0),
    ("Focaccia Bread",       380, 15, "Artisan Breads",0,  0, 0, 1),
    ("Strawberry Tart",      350, 20, "Tarts",         0,  0, 1, 0),
    ("Mini Eclairs (6pc)",   480, 18, "Pastries",      0,  0, 1, 1),
    ("Samosa (per piece)",    60, 80, "Savories",      0,  0, 0, 0),
    ("Chicken Patty",        150, 45, "Savories",      0,  0, 0, 0),
    ("Brownie Fudge",        200, 55, "Desserts",      10, 1, 0, 0),
    ("Vanilla Bean Macaron", 130, 70, "Macarons",      0,  0, 1, 1),
]
for nm, pr, st, cat, disc, bs, act, new in SAMPLE_PRODUCTS:
    cursor.execute("""INSERT OR IGNORE INTO products
        (name,price,stock,category,discount_pct,is_bestseller,is_active,is_new,cost_price)
        VALUES (?,?,?,?,?,?,?,?,?)""", (nm,pr,st,cat,disc,bs,act,new, pr*0.4))
conn.commit()

# ─── COLOUR / FONT PALETTE ──────────────────────────────────────────────────
C = {
    # Primary palette – Artisanal Bakery
    "cream":    "#FDFCF0",
    "cream2":   "#F5F0DC",
    "choc":     "#3E2723",
    "choc_md":  "#5D4037",
    "choc_lt":  "#8D6E63",
    "gold":     "#C8960C",
    "gold_lt":  "#F5D26C",
    "gold_pale":"#FFF8E1",
    "rose":     "#C94B7B",
    "rose_lt":  "#FDEEF5",
    "green":    "#2E7D52",
    "red":      "#C0392B",
    "blue":     "#1A5C8A",
    "panel":    "#FFFFFF",
    "border":   "#E8E0D0",
    "text":     "#2D1B12",
    "sub":      "#7A6A5A",
    "gray":     "#9E9E9E",
    "warn":     "#E65100",
    "sidebar":  "#2A1A10",
    "sidebar_h":"#3E2723",
    "badge_bs": "#C8960C",
    "badge_new":"#2E7D52",
    "badge_off":"#C0392B",
}

FONT_TITLE = ("Georgia",    22, "bold")
FONT_H     = ("Georgia",    18, "bold")
FONT_L     = ("Georgia",    13, "bold")
FONT_M     = ("Helvetica",  11)
FONT_MB    = ("Helvetica",  11, "bold")
FONT_S     = ("Helvetica",   9)
FONT_SB    = ("Helvetica",   9, "bold")
FONT_LOGO  = ("Georgia",    16, "bold")

TAX_RATE   = 0.05

CATEGORIES = ["All","Artisan Breads","Pastries","Custom Cakes","Cupcakes",
               "Muffins","Tarts","Macarons","Savories","Desserts"]

# ─── HELPERS ────────────────────────────────────────────────────────────────
def next_invoice():
    today = datetime.date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM sales WHERE date(date)=?", (today,))
    n = cursor.fetchone()[0] + 1
    return f"INV-{datetime.date.today().strftime('%Y%m%d')}-{n:04d}"

def next_return_invoice():
    today = datetime.date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM returns WHERE date(date)=?", (today,))
    n = cursor.fetchone()[0] + 1
    return f"RET-{datetime.date.today().strftime('%Y%m%d')}-{n:04d}"

def sep(parent, color=None, h=1, padx=0, pady=4):
    tk.Frame(parent, bg=color or C["border"], height=h).pack(
        fill=tk.X, pady=pady, padx=padx)

def pill_btn(parent, text, bg, fg, cmd, w=None, font=FONT_MB, padx=14, pady=7):
    b = tk.Button(parent, text=text, bg=bg, fg=fg, font=font,
                  relief="flat", activebackground=bg, activeforeground=fg,
                  cursor="hand2", command=cmd, bd=0, padx=padx, pady=pady)
    if w:
        b.config(width=w)
    return b

def card_frame(parent, bg=None, bd=1, relief="groove", **kwargs):
    return tk.Frame(parent, bg=bg or C["panel"], relief=relief, bd=bd, **kwargs)

# ─── LOGO / IMAGE GENERATORS ────────────────────────────────────────────────
def make_logo_pill(width=260, height=70):
    """Generate gradient logo pill image."""
    img = Image.new("RGBA", (width, height), (0,0,0,0))
    d   = ImageDraw.Draw(img)
    for x in range(width):
        t = x / width
        r = int(62  + (200-62 )*t)
        g = int(39  + (150-39 )*t)
        b = int(35  + (12 -35 )*t)
        d.rectangle([(x,0),(x+1,height)], fill=(r,g,b,255))
    # Rounded mask
    mask = Image.new("L", (width, height), 0)
    dm   = ImageDraw.Draw(mask)
    dm.rounded_rectangle([0,0,width-1,height-1], radius=35, fill=255)
    img.putalpha(mask)
    d.text((width//2-4, height//2-10), "🍰", anchor="mm",
           font=ImageFont.load_default())
    d.text((width//2+16, height//2-8), "Bakes by Ayesha",
           fill=(255,248,225,255), anchor="mm", font=ImageFont.load_default())
    return img

def make_placeholder_card(w=140, h=110, category="Pastries"):
    """Generate a beautiful gradient placeholder for product images."""
    gradients = {
        "Pastries":      [(255,240,220),(240,180,100)],
        "Artisan Breads":[(245,220,180),(200,150,80)],
        "Custom Cakes":  [(255,220,230),(220,130,150)],
        "Cupcakes":      [(255,200,220),(200,100,130)],
        "Muffins":       [(230,210,255),(150,100,200)],
        "Tarts":         [(220,255,220),(100,180,100)],
        "Macarons":      [(255,210,240),(200,100,160)],
        "Savories":      [(240,240,200),(180,180,80)],
        "Desserts":      [(255,220,200),(220,140,80)],
    }
    colors = gradients.get(category, [(250,240,220),(200,160,100)])
    img = Image.new("RGB", (w, h), colors[0])
    d   = ImageDraw.Draw(img)
    for y in range(h):
        t  = y/h
        r  = int(colors[0][0]*(1-t) + colors[1][0]*t)
        g  = int(colors[0][1]*(1-t) + colors[1][1]*t)
        bv = int(colors[0][2]*(1-t) + colors[1][2]*t)
        d.rectangle([(0,y),(w,y+1)], fill=(r,g,bv))
    icons = {"Pastries":"🥐","Artisan Breads":"🍞","Custom Cakes":"🎂",
             "Cupcakes":"🧁","Muffins":"🧁","Tarts":"🥧","Macarons":"🍬",
             "Savories":"🥪","Desserts":"🍰"}
    icon = icons.get(category, "🍩")
    d.text((w//2, h//2), icon, anchor="mm", font=ImageFont.load_default())
    return img

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
class BakesByAyeshaPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Bakes by Ayesha — Professional POS v2")
        self.root.geometry("1360x860")
        self.root.minsize(1100, 700)
        self.root.configure(bg=C["cream"])

        self.current_user = None
        self.current_role = None
        self.logo_path    = ""
        self._logo_photo  = None
        self._active_nav  = None

        # Style ttk globally
        self._setup_ttk_style()
        self.login_screen()

    def _setup_ttk_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",       background=C["cream"],  borderwidth=0)
        style.configure("TNotebook.Tab",   font=FONT_MB, padding=[14,6],
                        background=C["border"], foreground=C["sub"])
        style.map("TNotebook.Tab",
                  background=[("selected", C["choc"])],
                  foreground=[("selected","white")])
        style.configure("Treeview",         font=FONT_M,  rowheight=28,
                        background=C["panel"], fieldbackground=C["panel"],
                        foreground=C["text"])
        style.configure("Treeview.Heading", font=FONT_MB, background=C["choc"],
                        foreground="white")
        style.map("Treeview", background=[("selected",C["gold_lt"])],
                  foreground=[("selected",C["choc"])])
        style.configure("TScrollbar",       background=C["border"],
                        troughcolor=C["cream2"], arrowcolor=C["choc"])

    # ══════════════════════════════ LOGIN ══════════════════════════════════════
    def login_screen(self):
        self._clear_root()

        # Full-screen gradient bg
        bg = tk.Canvas(self.root, bg=C["cream"], highlightthickness=0)
        bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Left decorative panel
        left = tk.Frame(self.root, bg=C["choc"], width=420)
        left.place(relx=0, rely=0, relwidth=0.35, relheight=1)

        # Decorative circles on left panel
        if PILLOW_INSTALLED:
            dec = Image.new("RGBA",(420,860),(62,39,35,0))
            dd  = ImageDraw.Draw(dec)
            for cx,cy,r,a in [(350,120,200,25),(80,700,180,20),(300,500,120,15)]:
                dd.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(200,150,12,a))
            if hasattr(self,'_dec_photo'):
                del self._dec_photo
            self._dec_photo = ImageTk.PhotoImage(dec)
            tk.Label(left, image=self._dec_photo, bg=C["choc"], bd=0).place(x=0,y=0)

        tk.Label(left, text="🍰", font=("Helvetica",60), bg=C["choc"],
                 fg=C["gold"]).pack(pady=(80,10))
        tk.Label(left, text="Bakes by Ayesha", font=("Georgia",22,"bold"),
                 bg=C["choc"], fg=C["cream"]).pack()
        tk.Label(left, text="Artisan Bakery & Sweets", font=("Georgia",12,"italic"),
                 bg=C["choc"], fg=C["gold_lt"]).pack(pady=(4,20))
        sep(left, C["gold"], h=1, padx=40)
        for line in ["✦  Point of Sale System","✦  Inventory Management",
                     "✦  Sales Analytics","✦  Customer Loyalty"]:
            tk.Label(left, text=line, font=FONT_M, bg=C["choc"],
                     fg=C["cream2"]).pack(pady=3)

        tk.Label(left, text="© 2025 Bakes by Ayesha", font=FONT_S,
                 bg=C["choc"], fg=C["choc_lt"]).pack(side=tk.BOTTOM, pady=20)

        # Right: login form
        right = tk.Frame(self.root, bg=C["cream"])
        right.place(relx=0.35, rely=0, relwidth=0.65, relheight=1)

        card = tk.Frame(right, bg=C["panel"], padx=50, pady=45,
                        relief="flat", bd=0)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Shadow effect
        shadow = tk.Frame(right, bg=C["border"], padx=52, pady=47)
        shadow.place(relx=0.503, rely=0.503, anchor="center")
        card.lift()

        tk.Label(card, text="Welcome Back", font=("Georgia",26,"bold"),
                 bg=C["panel"], fg=C["choc"]).pack(pady=(0,4))
        tk.Label(card, text="Sign in to your POS dashboard",
                 font=("Helvetica",11), bg=C["panel"], fg=C["sub"]).pack(pady=(0,24))

        for lbl, attr, show in [("Username","_lu",""),("Password","_lp","●")]:
            tk.Label(card, text=lbl.upper(), font=("Helvetica",8,"bold"),
                     bg=C["panel"], fg=C["sub"], anchor="w").pack(fill=tk.X)
            ef = tk.Frame(card, bg=C["border"], pady=1, padx=1)
            ef.pack(fill=tk.X, pady=(2,14))
            e = tk.Entry(ef, show=show if show else "", font=("Helvetica",13),
                         relief="flat", bd=0, bg=C["panel"],
                         fg=C["choc"], insertbackground=C["gold"])
            e.pack(fill=tk.X, ipady=9, padx=2)
            setattr(self, attr, e)

        self._lu.insert(0,"Ayesha"); self._lp.insert(0,"admin123")
        self._lp.bind("<Return>", lambda e: self._do_login())

        btn = tk.Button(card, text="SIGN IN  →", bg=C["choc"], fg=C["gold_lt"],
                        font=("Helvetica",13,"bold"), relief="flat", bd=0,
                        activebackground=C["choc_md"], activeforeground=C["gold_lt"],
                        cursor="hand2", command=self._do_login, pady=12)
        btn.pack(fill=tk.X, pady=(6,0))

        self.login_err = tk.Label(card, text="", font=FONT_S,
                                  bg=C["panel"], fg=C["red"])
        self.login_err.pack(pady=(8,0))

    def _do_login(self):
        u, p = self._lu.get().strip(), self._lp.get().strip()
        cursor.execute("SELECT role FROM users WHERE username=? AND password=? AND is_active=1",
                       (u, _hash(p)))
        row = cursor.fetchone()
        if row:
            self.current_user = u
            self.current_role = row[0]
            self._show_logout_overlay()
        else:
            self.login_err.config(text="⚠  Invalid username or password.")

    def _show_logout_overlay(self, is_logout=False):
        """Professional loading/logout overlay with spinner."""
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}"
                         f"+{self.root.winfo_x()}+{self.root.winfo_y()}")
        overlay.configure(bg=C["choc"])
        overlay.attributes("-alpha", 0.0)

        tk.Label(overlay, text="🍰", font=("Helvetica",48),
                 bg=C["choc"], fg=C["gold"]).pack(pady=(120,10))
        msg = "Logging out..." if is_logout else "Logging in..."
        tk.Label(overlay, text=msg, font=("Georgia",18,"bold"),
                 bg=C["choc"], fg=C["cream"]).pack()
        tk.Label(overlay, text="Please wait...", font=FONT_M,
                 bg=C["choc"], fg=C["choc_lt"]).pack(pady=4)

        spin_lbl = tk.Label(overlay, text="◐", font=("Helvetica",28),
                            bg=C["choc"], fg=C["gold"])
        spin_lbl.pack(pady=10)

        spin_chars = ["◐","◓","◑","◒"]
        spin_idx   = [0]

        def animate():
            if not overlay.winfo_exists():
                return
            spin_lbl.config(text=spin_chars[spin_idx[0] % 4])
            spin_idx[0] += 1
            overlay.after(120, animate)

        animate()

        # Fade in
        alpha = [0.0]
        def fade_in():
            if not overlay.winfo_exists(): return
            alpha[0] = min(alpha[0]+0.08, 0.96)
            overlay.attributes("-alpha", alpha[0])
            if alpha[0] < 0.96:
                overlay.after(30, fade_in)
            else:
                overlay.after(600, finish)

        def finish():
            overlay.destroy()
            if is_logout:
                self.login_screen()
            else:
                self.main_dashboard()

        overlay.after(50, fade_in)

    # ══════════════════════════════ LOGO ══════════════════════════════════════
    def _render_logo_on(self, label, size=(200,56)):
        if PILLOW_INSTALLED:
            if self.logo_path and os.path.exists(self.logo_path):
                img = Image.open(self.logo_path).convert("RGBA").resize(size,Image.LANCZOS)
            else:
                img = make_logo_pill(*size)
            ph = ImageTk.PhotoImage(img)
            label.config(image=ph, text="", bg=C["sidebar"])
            label.image = ph
        else:
            label.config(text="🍰 BAKES BY AYESHA", font=FONT_L,
                         bg=C["sidebar"], fg=C["gold"])

    # ══════════════════════════ MAIN DASHBOARD ════════════════════════════════
    def main_dashboard(self):
        self._clear_root()
        self.root.configure(bg=C["cream"])

        # ── SIDEBAR ──────────────────────────────────────────────────────────
        sidebar = tk.Frame(self.root, bg=C["sidebar"], width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Logo in sidebar
        logo_lbl = tk.Label(sidebar, bg=C["sidebar"])
        logo_lbl.pack(pady=(20,4), padx=20)
        self._render_logo_on(logo_lbl, (180,50))

        sep(sidebar, C["choc_md"], padx=20, pady=8)

        # Nav items
        nav_items = [
            ("🛒",  "Point of Sale",  self._tab_pos),
            ("📦",  "Inventory",      self._tab_inventory),
            ("🏷️",  "Coupons",        self._tab_coupons),
            ("📊",  "Reports",        self._tab_reports),
            ("↩",  "Returns",        self._tab_returns),
            ("👥",  "Customers",      self._tab_customers),
            ("💸",  "Expenses",       self._tab_expenses),
            ("⚙️",  "Settings",       self._tab_settings),
        ]

        self.nav_buttons = {}
        self.content_area = tk.Frame(self.root, bg=C["cream"])
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for icon, name, builder in nav_items:
            btn_f = tk.Frame(sidebar, bg=C["sidebar"], cursor="hand2")
            btn_f.pack(fill=tk.X, pady=1)
            inner = tk.Frame(btn_f, bg=C["sidebar"], padx=16, pady=11)
            inner.pack(fill=tk.X)
            tk.Label(inner, text=icon, font=("Helvetica",14),
                     bg=C["sidebar"], fg=C["gold"]).pack(side=tk.LEFT)
            lbl = tk.Label(inner, text=name, font=("Helvetica",11),
                           bg=C["sidebar"], fg=C["cream2"])
            lbl.pack(side=tk.LEFT, padx=10)

            def on_click(b=builder, bf=btn_f, n=name):
                self._nav_select(bf, n, b)

            for w in [btn_f, inner] + inner.winfo_children():
                try:
                    w.bind("<Button-1>", lambda e, f=on_click: f())
                    w.bind("<Enter>", lambda e, f=btn_f: f.winfo_children()[0].config(bg=C["sidebar_h"]) if f.winfo_children() else None)
                    w.bind("<Leave>", lambda e, f=btn_f, n2=name: self._nav_hover_out(f,n2))
                except: pass

            self.nav_buttons[name] = (btn_f, inner, lbl)

        # User info & logout at bottom
        sep(sidebar, C["choc_md"], padx=20, pady=4)
        user_f = tk.Frame(sidebar, bg=C["sidebar"])
        user_f.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=14)

        logout_btn = tk.Button(user_f, text="🔒  Logout", font=FONT_MB,
                               bg=C["choc_md"], fg=C["cream"], relief="flat",
                               activebackground=C["red"], activeforeground="white",
                               cursor="hand2", bd=0, pady=8,
                               command=lambda: self._show_logout_overlay(is_logout=True))
        logout_btn.pack(fill=tk.X, pady=(0,4))

        tk.Label(user_f, text=f"👤 {self.current_user}",
                 font=FONT_SB, bg=C["sidebar"], fg=C["gold"]).pack()
        tk.Label(user_f, text=self.current_role.upper(),
                 font=FONT_S, bg=C["sidebar"], fg=C["choc_lt"]).pack()

        # ── TOP BAR ──────────────────────────────────────────────────────────
        self._topbar = tk.Frame(self.content_area, bg=C["cream2"], height=52)
        self._topbar.pack(fill=tk.X)
        self._topbar.pack_propagate(False)

        self._topbar_title = tk.Label(self._topbar, text="Point of Sale",
                                      font=("Georgia",16,"bold"),
                                      bg=C["cream2"], fg=C["choc"])
        self._topbar_title.pack(side=tk.LEFT, padx=20)

        tk.Label(self._topbar,
                 text=datetime.datetime.now().strftime("%A, %d %B %Y · %H:%M"),
                 font=FONT_S, bg=C["cream2"], fg=C["sub"]).pack(side=tk.RIGHT, padx=20)

        self._page_frame = tk.Frame(self.content_area, bg=C["cream"])
        self._page_frame.pack(fill=tk.BOTH, expand=True)

        # Start with POS
        first_nav_key = "Point of Sale"
        bf, inf, lbl_w = self.nav_buttons[first_nav_key]
        self._nav_select(bf, first_nav_key, self._tab_pos)

    def _nav_select(self, btn_frame, name, builder):
        # Reset all
        for n, (bf, inf, lbl_w) in self.nav_buttons.items():
            bf_inner = inf
            bf_inner.config(bg=C["sidebar"])
            for w in bf_inner.winfo_children():
                w.config(bg=C["sidebar"])

        # Highlight selected
        inf = self.nav_buttons[name][1]
        inf.config(bg=C["choc_md"])
        for w in inf.winfo_children():
            w.config(bg=C["choc_md"])
        self.nav_buttons[name][2].config(fg="white")

        self._active_nav = name
        self._topbar_title.config(text=name)

        for w in self._page_frame.winfo_children():
            w.destroy()
        builder(self._page_frame)

    def _nav_hover_out(self, frame, name):
        if name != self._active_nav:
            inner = self.nav_buttons[name][1]
            inner.config(bg=C["sidebar"])
            for w in inner.winfo_children():
                w.config(bg=C["sidebar"])

    # ══════════════════════════ TAB: POINT OF SALE ════════════════════════════
    def _tab_pos(self, parent):
        self.cart = []
        self.applied_coupon = None

        # ── LEFT: product grid ────────────────────────────────────────────────
        left = tk.Frame(parent, bg=C["cream"])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12,6), pady=10)

        # Search + category tabs
        search_row = tk.Frame(left, bg=C["cream"])
        search_row.pack(fill=tk.X, pady=(0,6))

        search_box_f = tk.Frame(search_row, bg=C["panel"],
                                highlightthickness=1, highlightbackground=C["border"])
        search_box_f.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(search_box_f, text="🔍", font=("Helvetica",12),
                 bg=C["panel"], fg=C["sub"]).pack(side=tk.LEFT, padx=8)
        self.pos_search = tk.Entry(search_box_f, font=FONT_M, relief="flat",
                                   bd=0, bg=C["panel"], fg=C["choc"],
                                   insertbackground=C["gold"])
        self.pos_search.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=4)
        self.pos_search.bind("<KeyRelease>", lambda e: self._pos_load_products())
        self.pos_search.insert(0, "Search bakery items...")
        self.pos_search.bind("<FocusIn>",
            lambda e: self.pos_search.delete(0,tk.END) if self.pos_search.get()=="Search bakery items..." else None)

        # Category horizontal scroll tabs
        cat_scroll = tk.Frame(left, bg=C["cream"])
        cat_scroll.pack(fill=tk.X, pady=(0,8))

        self.pos_cat_var   = tk.StringVar(value="All")
        self._cat_buttons  = {}

        canvas_c = tk.Canvas(cat_scroll, bg=C["cream"], height=36,
                             highlightthickness=0)
        canvas_c.pack(fill=tk.X)

        self._cat_inner = tk.Frame(canvas_c, bg=C["cream"])
        canvas_c.create_window((0,0), window=self._cat_inner, anchor="nw")

        self._build_category_tabs()

        # Products canvas
        canvas = tk.Canvas(left, bg=C["cream"], highlightthickness=0)
        vsb = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.prod_frame    = tk.Frame(canvas, bg=C["cream"])
        self.prod_frame_id = canvas.create_window((0,0), window=self.prod_frame, anchor="nw")
        self.prod_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self.prod_frame_id, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self._pos_load_products()

        # ── RIGHT: Cart panel ─────────────────────────────────────────────────
        right = tk.Frame(parent, bg=C["panel"], width=360,
                         relief="flat", bd=0)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(6,12), pady=10)
        right.pack_propagate(False)

        # Cart header
        cart_hdr = tk.Frame(right, bg=C["choc"], pady=12)
        cart_hdr.pack(fill=tk.X)
        tk.Label(cart_hdr, text="🛒  Current Order", font=FONT_L,
                 bg=C["choc"], fg=C["gold"]).pack()

        # Cart treeview
        cols = ("Product","Qty","Price","Total")
        self.cart_tree = ttk.Treeview(right, columns=cols, show="headings", height=10)
        for c, w in zip(cols,[138,38,68,68]):
            self.cart_tree.heading(c, text=c)
            self.cart_tree.column(c, width=w, anchor="center")
        self.cart_tree.pack(fill=tk.X, padx=8, pady=(8,0))
        self.cart_tree.bind("<Double-1>", self._edit_cart_qty)

        sep(right, pady=6)

        # Coupon row
        cf = tk.Frame(right, bg=C["panel"])
        cf.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(cf, text="🏷️ Coupon:", font=FONT_SB, bg=C["panel"],
                 fg=C["sub"]).pack(side=tk.LEFT)
        self.coupon_ent = tk.Entry(cf, font=FONT_M, width=13, relief="flat",
                                   bd=0, bg=C["cream2"], fg=C["choc"])
        self.coupon_ent.pack(side=tk.LEFT, padx=6, ipady=5)
        pill_btn(cf,"Apply",C["gold"],C["choc"],self._apply_coupon,
                 font=FONT_SB, padx=10, pady=5).pack(side=tk.LEFT)

        sep(right, pady=4)

        # Totals
        tf = tk.Frame(right, bg=C["panel"])
        tf.pack(fill=tk.X, padx=12)
        self.lbl_sub  = self._tot_row(tf,"Subtotal:")
        self.lbl_disc = self._tot_row(tf,"Coupon Disc:", C["green"])
        self.lbl_tax  = self._tot_row(tf,f"Tax ({int(TAX_RATE*100)}%):")

        sep(right, C["choc"], h=2, pady=4)
        self.lbl_total = self._tot_row(right,"TOTAL:", C["choc"], big=True)
        sep(right, pady=4)

        # Payment
        pf = tk.Frame(right, bg=C["panel"])
        pf.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(pf, text="Payment:", font=FONT_SB, bg=C["panel"],
                 fg=C["sub"]).pack(side=tk.LEFT)
        self.pay_var = tk.StringVar(value="Cash")
        for pm in ["Cash","Card","Online","Split"]:
            tk.Radiobutton(pf, text=pm, variable=self.pay_var, value=pm,
                           bg=C["panel"], font=FONT_S, fg=C["text"],
                           selectcolor=C["gold_lt"],
                           activebackground=C["panel"]).pack(side=tk.LEFT, padx=3)

        # Customer
        cuf = tk.Frame(right, bg=C["panel"])
        cuf.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(cuf, text="📱 Phone:", font=FONT_SB, bg=C["panel"],
                 fg=C["sub"]).pack(side=tk.LEFT)
        self.cust_phone = tk.Entry(cuf, font=FONT_M, width=14, relief="flat",
                                   bd=0, bg=C["cream2"], fg=C["choc"])
        self.cust_phone.pack(side=tk.LEFT, padx=6, ipady=4)

        sep(right, pady=4)

        bf = tk.Frame(right, bg=C["panel"])
        bf.pack(fill=tk.X, padx=10, pady=6)
        complete_btn = tk.Button(bf, text="✔  Complete Sale",
                                 bg=C["green"], fg="white", font=FONT_MB,
                                 relief="flat", bd=0, cursor="hand2",
                                 pady=11, command=self._complete_sale)
        complete_btn.pack(fill=tk.X, pady=(0,6))
        clear_btn = tk.Button(bf, text="🗑  Clear Cart",
                              bg=C["cream2"], fg=C["choc_lt"], font=FONT_MB,
                              relief="flat", bd=0, cursor="hand2",
                              pady=8, command=self._clear_cart)
        clear_btn.pack(fill=tk.X)

        self._refresh_cart()

    def _build_category_tabs(self):
        for w in self._cat_inner.winfo_children():
            w.destroy()
        cursor.execute("SELECT DISTINCT category FROM products WHERE is_active=1 ORDER BY category")
        db_cats = [r[0] for r in cursor.fetchall()]
        cats = ["All"] + db_cats

        for cat in cats:
            active = (cat == self.pos_cat_var.get())
            bg   = C["choc"]    if active else C["cream2"]
            fg   = C["gold"]    if active else C["sub"]
            font = FONT_SB      if active else FONT_S
            b = tk.Button(self._cat_inner, text=cat, font=font, bg=bg, fg=fg,
                          relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
                          command=lambda c=cat: self._pos_select_cat(c))
            b.pack(side=tk.LEFT, padx=3)
            self._cat_buttons[cat] = b

    def _pos_select_cat(self, cat):
        self.pos_cat_var.set(cat)
        self._build_category_tabs()
        self._pos_load_products()

    def _pos_load_products(self):
        for w in self.prod_frame.winfo_children():
            w.destroy()

        q   = self.pos_search.get().strip()
        if q == "Search bakery items...": q = ""
        cat = self.pos_cat_var.get()

        sql = """SELECT id,name,price,stock,category,image_path,
                        discount_pct,is_bestseller,is_new
                 FROM products WHERE is_active=1"""
        params = []
        if q:
            sql += " AND name LIKE ?"
            params.append(f"%{q}%")
        if cat != "All":
            sql += " AND category=?"
            params.append(cat)
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        COLS = 4
        for i, row in enumerate(rows):
            pid, name, price, stock, pcat, imgp, disc, bs, new = row
            self._make_product_card(i, pid, name, price, stock, pcat, imgp, disc, bs, new, COLS)

    def _make_product_card(self, i, pid, name, price, stock, cat, imgp, disc, bs, new, COLS):
        """Create a beautiful product card with glassmorphism-style and badges."""
        col = i % COLS
        row_n = i // COLS

        # Outer card
        card = tk.Frame(self.prod_frame, bg=C["panel"], relief="flat", bd=0,
                        cursor="hand2" if stock > 0 else "")
        card.grid(row=row_n, column=col, padx=7, pady=7, sticky="nsew")
        self.prod_frame.columnconfigure(col, weight=1)

        # Inner with border
        inner = tk.Frame(card, bg=C["panel"], highlightthickness=1,
                         highlightbackground=C["border"])
        inner.pack(fill=tk.BOTH, expand=True)

        # Image area
        img_frame = tk.Frame(inner, bg=C["cream2"], height=110)
        img_frame.pack(fill=tk.X)
        img_frame.pack_propagate(False)

        img_lbl = tk.Label(img_frame, bg=C["cream2"])
        img_lbl.pack(fill=tk.BOTH, expand=True)

        if PILLOW_INSTALLED:
            if imgp and os.path.exists(imgp):
                try:
                    img = Image.open(imgp).resize((140,110), Image.LANCZOS)
                    ph  = ImageTk.PhotoImage(img)
                    img_lbl.config(image=ph)
                    img_lbl.image = ph
                except:
                    ph = ImageTk.PhotoImage(make_placeholder_card(140,110,cat))
                    img_lbl.config(image=ph); img_lbl.image = ph
            else:
                ph = ImageTk.PhotoImage(make_placeholder_card(140,110,cat))
                img_lbl.config(image=ph); img_lbl.image = ph
        else:
            icons = {"Pastries":"🥐","Artisan Breads":"🍞","Custom Cakes":"🎂",
                     "Cupcakes":"🧁","Savories":"🥪","Desserts":"🍰"}
            img_lbl.config(text=icons.get(cat,"🍩"), font=("Helvetica",32),
                           fg=C["gold"])

        # Badges overlay
        badge_f = tk.Frame(img_frame, bg=C["cream2"])
        badge_f.place(x=4, y=4)
        if bs:
            tk.Label(badge_f, text="★ Best Seller", font=("Helvetica",7,"bold"),
                     bg=C["badge_bs"], fg="white", padx=5, pady=2).pack(side=tk.LEFT, padx=1)
        if new:
            tk.Label(badge_f, text="✦ New", font=("Helvetica",7,"bold"),
                     bg=C["badge_new"], fg="white", padx=5, pady=2).pack(side=tk.LEFT, padx=1)
        if disc and disc > 0:
            tk.Label(badge_f, text=f"−{int(disc)}%", font=("Helvetica",7,"bold"),
                     bg=C["badge_off"], fg="white", padx=5, pady=2).pack(side=tk.LEFT, padx=1)

        # Info area
        info = tk.Frame(inner, bg=C["panel"], padx=8, pady=6)
        info.pack(fill=tk.X)

        tk.Label(info, text=name, font=("Helvetica",9,"bold"),
                 bg=C["panel"], fg=C["choc"], wraplength=120,
                 justify="left").pack(anchor="w")

        price_f = tk.Frame(info, bg=C["panel"])
        price_f.pack(anchor="w", pady=2)
        if disc and disc > 0:
            orig = price
            final = price * (1 - disc/100)
            tk.Label(price_f, text=f"Rs.{orig:.0f}", font=("Helvetica",8),
                     bg=C["panel"], fg=C["gray"]).pack(side=tk.LEFT)
            # Strikethrough effect via Canvas
            ol = tk.Label(price_f, text=f"Rs.{orig:.0f}", font=("Helvetica",8),
                          bg=C["panel"], fg=C["gray"])
            # Simple label trick: overstrike
            ol.config(font=("Helvetica",8,"overstrike"))
            price_f.winfo_children()[-1].destroy()
            tk.Label(price_f, text=f"Rs.{orig:.0f}", font=("Helvetica",8,"overstrike"),
                     bg=C["panel"], fg=C["gray"]).pack(side=tk.LEFT)
            tk.Label(price_f, text=f" Rs.{final:.0f}", font=FONT_SB,
                     bg=C["panel"], fg=C["rose"]).pack(side=tk.LEFT)
        else:
            tk.Label(price_f, text=f"Rs.{price:.0f}", font=FONT_SB,
                     bg=C["panel"], fg=C["choc"]).pack(side=tk.LEFT)

        # Stock indicator
        stk_color = C["green"] if stock > 5 else (C["warn"] if stock > 0 else C["red"])
        stk_text  = f"In Stock: {stock}" if stock > 0 else "Out of Stock"
        tk.Label(info, text=stk_text, font=("Helvetica",7),
                 bg=C["panel"], fg=stk_color).pack(anchor="w")

        # Quick Add button
        if stock > 0:
            add_btn = tk.Button(info, text="+ Quick Add",
                                bg=C["choc"], fg=C["gold"], font=("Helvetica",8,"bold"),
                                relief="flat", bd=0, cursor="hand2", pady=4,
                                command=lambda r=(pid,name,price,stock,cat,imgp): self._add_to_cart(r))
            add_btn.pack(fill=tk.X, pady=(4,0))
            add_btn.bind("<Enter>", lambda e,b=add_btn: b.config(bg=C["choc_md"]))
            add_btn.bind("<Leave>", lambda e,b=add_btn: b.config(bg=C["choc"]))
        else:
            tk.Label(info, text="Unavailable", font=("Helvetica",8),
                     bg=C["red"], fg="white", pady=4).pack(fill=tk.X, pady=(4,0))

        # Click entire card to add
        def on_click(r=(pid,name,price,stock,cat,imgp)):
            if stock > 0:
                self._add_to_cart(r)
        for w in [card, inner, img_frame, img_lbl, info]:
            w.bind("<Button-1>", lambda e,f=on_click: f())

        # Hover effect
        def on_enter(e, c=inner):
            c.config(highlightbackground=C["gold"])
        def on_leave(e, c=inner):
            c.config(highlightbackground=C["border"])
        for w in [card, inner, img_frame, img_lbl, info]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    def _add_to_cart(self, row):
        pid, name, price, stock, cat, imgp = row
        if stock <= 0:
            messagebox.showwarning("Out of Stock", f"'{name}' is out of stock!")
            return

        # Apply item-level discount if exists
        cursor.execute("SELECT discount_pct FROM products WHERE id=?", (pid,))
        r = cursor.fetchone()
        disc = r[0] if r else 0
        final_price = price * (1 - disc/100) if disc else price

        for item in self.cart:
            if item["pid"] == pid:
                if item["qty"] >= stock:
                    messagebox.showwarning("Stock Limit","Cannot exceed available stock.")
                    return
                item["qty"] += 1
                self._refresh_cart()
                return
        self.cart.append({"pid":pid,"name":name,"price":final_price,
                          "orig_price":price,"qty":1,"stock":stock})
        self._refresh_cart()

    def _edit_cart_qty(self, event):
        sel = self.cart_tree.selection()
        if not sel: return
        idx  = self.cart_tree.index(sel[0])
        item = self.cart[idx]

        win = tk.Toplevel(self.root)
        win.title("Edit Quantity")
        win.geometry("280x170")
        win.configure(bg=C["panel"])
        win.grab_set()

        tk.Label(win, text=item['name'], font=FONT_L, bg=C["panel"],
                 fg=C["choc"]).pack(pady=(14,2))
        tk.Label(win, text=f"Max: {item['stock']}", font=FONT_S,
                 bg=C["panel"], fg=C["gray"]).pack()

        qty_var = tk.IntVar(value=item["qty"])
        sf = tk.Frame(win, bg=C["panel"])
        sf.pack(pady=10)
        tk.Button(sf, text="−", font=FONT_MB, bg=C["cream2"], fg=C["choc"],
                  width=3, relief="flat", bd=0, cursor="hand2",
                  command=lambda: qty_var.set(max(0, qty_var.get()-1))).pack(side=tk.LEFT,padx=4)
        tk.Label(sf, textvariable=qty_var, font=("Georgia",18,"bold"),
                 bg=C["panel"], fg=C["choc"], width=4).pack(side=tk.LEFT)
        tk.Button(sf, text="+", font=FONT_MB, bg=C["choc"], fg=C["gold"],
                  width=3, relief="flat", bd=0, cursor="hand2",
                  command=lambda: qty_var.set(min(item["stock"],qty_var.get()+1))).pack(side=tk.LEFT,padx=4)

        def apply():
            q = qty_var.get()
            if q == 0: self.cart.pop(idx)
            else: self.cart[idx]["qty"] = q
            self._refresh_cart(); win.destroy()

        tk.Button(win, text="Update Cart", bg=C["choc"], fg=C["gold"],
                  font=FONT_MB, relief="flat", bd=0, pady=8, cursor="hand2",
                  command=apply).pack(fill=tk.X, padx=30)

    def _tot_row(self, parent, lbl, color=None, big=False):
        f = tk.Frame(parent, bg=C["panel"])
        f.pack(fill=tk.X, padx=10, pady=2)
        font = ("Georgia",14,"bold") if big else FONT_M
        tk.Label(f, text=lbl, font=font, bg=C["panel"],
                 fg=color or C["sub"]).pack(side=tk.LEFT)
        v = tk.Label(f, text="Rs. 0.00", font=font,
                     bg=C["panel"], fg=color or C["choc"])
        v.pack(side=tk.RIGHT)
        return v

    def _refresh_cart(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        subtotal = 0
        for item in self.cart:
            t = item["price"] * item["qty"]
            subtotal += t
            self.cart_tree.insert("", tk.END,
                values=(item["name"][:18], item["qty"],
                        f"{item['price']:.0f}", f"{t:.0f}"))

        disc_amt = 0
        if self.applied_coupon:
            c = self.applied_coupon
            disc_amt = (subtotal*c["value"]/100) if c["type"]=="percent" else min(c["value"],subtotal)
        tax   = (subtotal - disc_amt) * TAX_RATE
        total = subtotal - disc_amt + tax

        self.lbl_sub.config(text=f"Rs. {subtotal:.2f}")
        self.lbl_disc.config(text=f"-Rs. {disc_amt:.2f}")
        self.lbl_tax.config(text=f"Rs. {tax:.2f}")
        self.lbl_total.config(text=f"Rs. {total:.2f}")

    def _apply_coupon(self):
        code = self.coupon_ent.get().strip().upper()
        cursor.execute("""SELECT * FROM coupons WHERE code=? AND is_active=1
                          AND (expiry_date IS NULL OR expiry_date >= date('now'))
                          AND used_count < max_uses""", (code,))
        row = cursor.fetchone()
        if not row:
            messagebox.showerror("Invalid","Coupon code is invalid or expired.")
            return
        cols = [d[0] for d in cursor.description]
        self.applied_coupon = dict(zip(cols, row))
        messagebox.showinfo("Coupon Applied!",
            f"'{code}' applied — "
            f"{'%' if self.applied_coupon['type']=='percent' else 'Rs.'}"
            f"{self.applied_coupon['value']} off")
        self._refresh_cart()

    def _clear_cart(self):
        self.cart.clear()
        self.applied_coupon = None
        self.coupon_ent.delete(0, tk.END)
        self._refresh_cart()

    def _get_totals(self):
        subtotal = sum(i["price"]*i["qty"] for i in self.cart)
        disc_amt = 0
        if self.applied_coupon:
            c = self.applied_coupon
            disc_amt = (subtotal*c["value"]/100) if c["type"]=="percent" else min(c["value"],subtotal)
        tax   = (subtotal - disc_amt) * TAX_RATE
        total = subtotal - disc_amt + tax
        return subtotal, disc_amt, tax, total

    def _complete_sale(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart","Add items first."); return
        subtotal, disc_amt, tax, total = self._get_totals()
        inv = next_invoice()
        cursor.execute(
            "INSERT INTO sales (invoice_no,subtotal,discount,tax,total,payment_method,cashier) VALUES (?,?,?,?,?,?,?)",
            (inv,subtotal,disc_amt,tax,total,self.pay_var.get(),self.current_user))
        sid = cursor.lastrowid
        for item in self.cart:
            cursor.execute(
                "INSERT INTO sale_items (sale_id,product_id,product_name,quantity,unit_price,total) VALUES (?,?,?,?,?,?)",
                (sid,item["pid"],item["name"],item["qty"],item["price"],item["price"]*item["qty"]))
            cursor.execute("UPDATE products SET stock=stock-? WHERE id=?", (item["qty"],item["pid"]))
            cursor.execute(
                "INSERT INTO stock_log (product_id,product_name,change_qty,reason) VALUES (?,?,?,?)",
                (item["pid"],item["name"],-item["qty"],"Sale: "+inv))
        if self.applied_coupon:
            cursor.execute("UPDATE coupons SET used_count=used_count+1 WHERE id=?",
                           (self.applied_coupon["id"],))
        phone = self.cust_phone.get().strip()
        if phone:
            pts = int(total // 100)
            cursor.execute("""INSERT INTO customers (name,phone,loyalty_pts,total_spent)
                              VALUES (?,?,?,?) ON CONFLICT(phone) DO UPDATE SET
                              loyalty_pts=loyalty_pts+?, total_spent=total_spent+?""",
                           ("Customer",phone,pts,total,pts,total))
        conn.commit()
        receipt = self._build_receipt(inv, subtotal, disc_amt, tax, total)
        self._show_receipt(receipt)
        self._pos_load_products()
        self._build_category_tabs()
        self._clear_cart()

    def _build_receipt(self, inv, sub, disc, tax, total):
        lines = [
            "═"*40,"        Ayesha's Royal Bakes ",
            "     Artisan Bakery & Sweets","═"*40,
            f"Invoice : {inv}",
            f"Date    : {datetime.datetime.now().strftime('%d-%b-%Y %H:%M')}",
            f"Cashier : {self.current_user}",
            f"Payment : {self.pay_var.get()}","─"*40,
        ]
        for item in self.cart:
            lines.append(f"  {item['name'][:22]:<22} x{item['qty']}")
            lines.append(f"  {'Rs.'+str(int(item['price'])):>12} = Rs.{item['price']*item['qty']:.0f}")
        lines += ["─"*40,
            f"  Subtotal   : Rs. {sub:.2f}",
            f"  Discount   : -Rs. {disc:.2f}",
            f"  Tax (5%)   : Rs. {tax:.2f}","═"*40,
            f"  TOTAL      : Rs. {total:.2f}","═"*40,
            "  Thank you! Visit Again 🎂",
            "  www.Ayesha's Royal Bakes .com","═"*40,
        ]
        return "\n".join(lines)

    def _show_receipt(self, text, title="Receipt"):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("440,550".replace(",","x"))
        win.geometry("440x560")
        win.configure(bg=C["panel"])
        win.grab_set()

        hdr = tk.Frame(win, bg=C["choc"], pady=12)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"🧾 {title}", font=FONT_L,
                 bg=C["choc"], fg=C["gold"]).pack()

        txt = tk.Text(win, font=("Courier New",10), bg=C["cream"],
                      fg=C["choc"], relief="flat", bd=0, padx=14, pady=14)
        txt.pack(fill=tk.BOTH, expand=True, padx=0)
        txt.insert("1.0", text)
        txt.config(state="disabled")

        def save_txt():
            path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text","*.txt")])
            if path:
                with open(path,"w") as f: f.write(text)
                messagebox.showinfo("Saved","Receipt saved!")

        bf = tk.Frame(win, bg=C["panel"], pady=8)
        bf.pack(fill=tk.X, padx=12)
        pill_btn(bf,"💾 Save",C["choc"],C["gold"],save_txt,padx=16,pady=8).pack(side=tk.LEFT,padx=4)
        pill_btn(bf,"✖ Close",C["cream2"],C["sub"],win.destroy,padx=16,pady=8).pack(side=tk.LEFT)

    # ══════════════════════════ TAB: INVENTORY ════════════════════════════════
    def _tab_inventory(self, parent):
        # Action bar
        top = tk.Frame(parent, bg=C["cream"], pady=8)
        top.pack(fill=tk.X, padx=12)

        for txt, bg, fg, cmd in [
            ("+ Add Product",      C["choc"],   C["gold"],  self._add_product_win),
            ("✏ Edit",             C["blue"],   "white",    self._edit_product_win),
            ("🗑 Delete",           C["red"],    "white",    self._delete_product),
            ("📈 +10% Prices",      C["gold"],   C["choc"],  self._bulk_price_up),
            ("📉 -10% Prices",      C["cream2"], C["sub"],   self._bulk_price_dn),
            ("📤 Export CSV",       C["green"],  "white",    self._export_products),
        ]:
            pill_btn(top, txt, bg, fg, cmd, padx=12, pady=6).pack(side=tk.LEFT, padx=3)

        # Search
        sf = tk.Frame(parent, bg=C["cream"])
        sf.pack(fill=tk.X, padx=12, pady=(0,6))
        tk.Label(sf, text="Search:", font=FONT_SB, bg=C["cream"],
                 fg=C["sub"]).pack(side=tk.LEFT)
        self.inv_search = tk.Entry(sf, font=FONT_M, width=30, relief="flat",
                                   bd=0, bg=C["panel"], fg=C["choc"],
                                   highlightthickness=1, highlightbackground=C["border"])
        self.inv_search.pack(side=tk.LEFT, padx=8, ipady=6)
        self.inv_search.bind("<KeyRelease>", lambda e: self._load_inventory())

        # Treeview
        tree_f = tk.Frame(parent, bg=C["cream"])
        tree_f.pack(fill=tk.BOTH, expand=True, padx=12)

        cols = ("ID","Price","Cost","Stock","Discount%","Category","Status","Bestseller")
        self.inv_tree = ttk.Treeview(tree_f, columns=cols, show=("tree","headings"))
        self.inv_tree.heading("#0", text="Product Name")
        self.inv_tree.column("#0", width=200)
        widths = [40, 80, 70, 60, 80, 120, 70, 80]
        for c, w in zip(cols, widths):
            self.inv_tree.heading(c, text=c)
            self.inv_tree.column(c, width=w, anchor="center")

        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.inv_tree.pack(fill=tk.BOTH, expand=True)

        self.low_lbl = tk.Label(parent, text="", font=FONT_SB,
                                bg=C["cream"], fg=C["red"])
        self.low_lbl.pack(pady=3, anchor="w", padx=12)
        self.inv_tree.bind("<<TreeviewSelect>>", self._inv_preview)

        self.inv_img = tk.Label(parent, bg=C["cream"], text="Select a product",
                                font=FONT_S, fg=C["gray"])
        self.inv_img.pack(pady=4)

        self._load_inventory()

    def _load_inventory(self):
        for i in self.inv_tree.get_children():
            self.inv_tree.delete(i)
        q = self.inv_search.get().strip() if hasattr(self,"inv_search") else ""
        sql = """SELECT id,name,price,cost_price,stock,discount_pct,
                        category,is_active,is_bestseller FROM products"""
        params = []
        if q:
            sql += " WHERE name LIKE ?"
            params.append(f"%{q}%")
        cursor.execute(sql, params)
        low = []
        for row in cursor.fetchall():
            pid, name, price, cost, stock, disc, cat, active, bs = row
            tag = "low" if 0<stock<=5 else ("out" if stock<=0 else "")
            self.inv_tree.insert("","end", text=name, iid=str(pid),
                values=(pid, f"{price:.2f}", f"{cost:.2f}", stock,
                        f"{disc:.0f}%", cat,
                        "Active" if active else "Inactive",
                        "★ Yes" if bs else ""),
                tags=(tag,))
            if stock <= 5:
                low.append(name)
        self.inv_tree.tag_configure("low", foreground=C["warn"])
        self.inv_tree.tag_configure("out", foreground=C["red"])
        if hasattr(self,"low_lbl"):
            self.low_lbl.config(text=("⚠  Low/Out Stock: "+", ".join(low)) if low else "✔  All stock levels OK")
            self.low_lbl.config(fg=C["red"] if low else C["green"])

    def _inv_preview(self, event):
        sel = self.inv_tree.selection()
        if not sel: return
        pid = int(sel[0])
        cursor.execute("SELECT image_path FROM products WHERE id=?", (pid,))
        row = cursor.fetchone()
        if PILLOW_INSTALLED and row and row[0] and os.path.exists(row[0]):
            try:
                img = Image.open(row[0]).resize((160,110), Image.LANCZOS)
                ph  = ImageTk.PhotoImage(img)
                self.inv_img.config(image=ph, text=""); self.inv_img.image=ph
                return
            except: pass
        self.inv_img.config(image="", text="No image", font=FONT_S, fg=C["gray"])

    def _add_product_win(self, pid=None):
        data = None
        if pid:
            cursor.execute("""SELECT id,name,price,stock,category,image_path,
                                     description,cost_price,barcode,discount_pct,
                                     is_bestseller,is_new
                              FROM products WHERE id=?""", (pid,))
            data = cursor.fetchone()

        win = tk.Toplevel(self.root)
        win.title("Edit Product" if pid else "New Product")
        win.geometry("460x720")
        win.configure(bg=C["panel"])
        win.grab_set()

        hdr = tk.Frame(win, bg=C["choc"], pady=14)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="✏ Product Details" if pid else "＋ New Product",
                 font=FONT_L, bg=C["choc"], fg=C["gold"]).pack()

        scroll_canvas = tk.Canvas(win, bg=C["panel"], highlightthickness=0)
        scroll_canvas.pack(fill=tk.BOTH, expand=True)
        inner_frame = tk.Frame(scroll_canvas, bg=C["panel"])
        scroll_canvas.create_window((0,0), window=inner_frame, anchor="nw")
        inner_frame.bind("<Configure>", lambda e: scroll_canvas.configure(
            scrollregion=scroll_canvas.bbox("all")))

        def fld(lbl, attr, show=""):
            tk.Label(inner_frame, text=lbl+":", font=FONT_SB, bg=C["panel"],
                     fg=C["sub"], anchor="w").pack(fill=tk.X, padx=22, pady=(6,0))
            e = tk.Entry(inner_frame, show=show, font=FONT_M, relief="flat", bd=0,
                         bg=C["cream2"], fg=C["choc"], insertbackground=C["gold"])
            e.pack(fill=tk.X, padx=22, ipady=7, pady=(2,0))
            setattr(self, attr, e)

        fld("Product Name",     "_pn")
        fld("Unit Price (Rs.)", "_pp")
        fld("Cost Price (Rs.)", "_pc")
        fld("Stock Qty",        "_ps")
        fld("Category",         "_pcat")
        fld("Barcode",          "_pbar")
        fld("Discount %",       "_pdisc")
        fld("Description",      "_pdesc")

        if data:
            _,nm,pr,st,cat,imgp,desc,cp,bc,disc,bs,new = data
            for attr, val in [("_pn",nm),("_pp",pr),("_pc",cp),("_ps",st),
                               ("_pcat",cat),("_pbar",bc or ""),
                               ("_pdisc",disc or 0),("_pdesc",desc or "")]:
                getattr(self,attr).insert(0, val or "")

        # Checkboxes: Bestseller, New
        chk_f = tk.Frame(inner_frame, bg=C["panel"])
        chk_f.pack(fill=tk.X, padx=22, pady=8)
        self._pbs  = tk.IntVar(value=(data[10] if data else 0))
        self._pnew = tk.IntVar(value=(data[11] if data else 0))
        tk.Checkbutton(chk_f, text="★ Mark as Best Seller", variable=self._pbs,
                       bg=C["panel"], font=FONT_M, fg=C["gold"],
                       selectcolor=C["cream2"]).pack(side=tk.LEFT, padx=8)
        tk.Checkbutton(chk_f, text="✦ Mark as New", variable=self._pnew,
                       bg=C["panel"], font=FONT_M, fg=C["green"],
                       selectcolor=C["cream2"]).pack(side=tk.LEFT)

        self._temp_img = ""
        current_img   = data[5] if data else ""

        def browse():
            p = filedialog.askopenfilename(filetypes=[("Images","*.jpg *.png *.jpeg *.webp")])
            if p:
                dest = os.path.join(IMG_DIR, os.path.basename(p))
                shutil.copy2(p, dest)
                self._temp_img = dest
                messagebox.showinfo("Image Set","Image selected & copied.")

        pill_btn(inner_frame, "📷 Browse Image", C["cream2"], C["choc"],
                 browse, padx=16, pady=7).pack(padx=22, pady=4, anchor="w")

        def save():
            try:
                nm   = self._pn.get().strip()
                if not nm:
                    messagebox.showerror("Validation","Product name required."); return
                pr   = float(self._pp.get())
                cp   = float(self._pc.get() or 0)
                st   = int(self._ps.get())
                cat  = self._pcat.get().strip() or "General"
                bar  = self._pbar.get().strip() or None
                disc = float(self._pdisc.get() or 0)
                desc = self._pdesc.get().strip()
                imgp = self._temp_img or current_img
                bs   = self._pbs.get()
                new  = self._pnew.get()
                if pid:
                    cursor.execute("""UPDATE products SET name=?,price=?,cost_price=?,stock=?,
                                      category=?,barcode=?,description=?,image_path=?,
                                      discount_pct=?,is_bestseller=?,is_new=? WHERE id=?""",
                                   (nm,pr,cp,st,cat,bar,desc,imgp,disc,bs,new,pid))
                else:
                    cursor.execute("""INSERT INTO products
                                      (name,price,cost_price,stock,category,barcode,description,
                                       image_path,discount_pct,is_bestseller,is_new)
                                      VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                                   (nm,pr,cp,st,cat,bar,desc,imgp,disc,bs,new))
                conn.commit()
                self._load_inventory()
                self._pos_load_products()
                self._build_category_tabs()
                win.destroy()
                messagebox.showinfo("Saved","Product saved successfully.")
            except ValueError as ex:
                messagebox.showerror("Input Error",f"Check numeric fields: {ex}")
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate","Name or barcode already exists.")

        pill_btn(inner_frame, "💾 Save Product", C["choc"], C["gold"],
                 save, padx=20, pady=10).pack(padx=22, pady=16)

    def _edit_product_win(self):
        sel = self.inv_tree.selection()
        if not sel:
            messagebox.showwarning("Select","Select a product first."); return
        self._add_product_win(pid=int(sel[0]))

    def _delete_product(self):
        sel = self.inv_tree.selection()
        if not sel: return
        pid  = int(sel[0])
        name = self.inv_tree.item(sel[0])["text"]
        if messagebox.askyesno("Confirm Delete",f"Delete '{name}'? This cannot be undone."):
            cursor.execute("DELETE FROM products WHERE id=?", (pid,))
            conn.commit()
            self._load_inventory()

    def _bulk_price_up(self):
        if messagebox.askyesno("Confirm","Increase ALL prices by 10%?"):
            cursor.execute("UPDATE products SET price=ROUND(price*1.10,2)")
            conn.commit(); self._load_inventory()

    def _bulk_price_dn(self):
        if messagebox.askyesno("Confirm","Decrease ALL prices by 10%?"):
            cursor.execute("UPDATE products SET price=ROUND(price*0.90,2)")
            conn.commit(); self._load_inventory()

    def _export_products(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV","*.csv")])
        if not path: return
        cursor.execute("SELECT name,price,cost_price,stock,category,barcode,discount_pct FROM products")
        with open(path,"w",newline="",encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Name","Price","Cost","Stock","Category","Barcode","Discount%"])
            w.writerows(cursor.fetchall())
        messagebox.showinfo("Exported",f"Saved to {path}")

    # ══════════════════════════ TAB: COUPONS ══════════════════════════════════
    def _tab_coupons(self, parent):
        hdr = tk.Frame(parent, bg=C["cream"], pady=10)
        hdr.pack(fill=tk.X, padx=12)
        tk.Label(hdr, text="🏷️  Coupon Management", font=FONT_H,
                 bg=C["cream"], fg=C["choc"]).pack(side=tk.LEFT)
        pill_btn(hdr,"+ New Coupon",C["choc"],C["gold"],
                 self._new_coupon_win,padx=14,pady=7).pack(side=tk.RIGHT, padx=4)
        pill_btn(hdr,"🗑 Delete",C["red"],"white",
                 self._del_coupon,padx=14,pady=7).pack(side=tk.RIGHT, padx=4)

        cols = ("Code","Type","Value","Min Purchase","Max Uses","Used","Expiry","Active")
        self.coup_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols:
            self.coup_tree.heading(c, text=c)
            self.coup_tree.column(c, width=100, anchor="center")
        self.coup_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        self._load_coupons()

    def _load_coupons(self):
        for i in self.coup_tree.get_children():
            self.coup_tree.delete(i)
        cursor.execute("SELECT id,code,type,value,min_purchase,max_uses,used_count,expiry_date,is_active FROM coupons")
        for row in cursor.fetchall():
            self.coup_tree.insert("","end", iid=str(row[0]),
                values=(row[1],row[2],row[3],row[4],row[5],row[6],
                        row[7] or "Never","Yes" if row[8] else "No"))

    def _new_coupon_win(self):
        win = tk.Toplevel(self.root)
        win.title("New Coupon"); win.geometry("380x440")
        win.configure(bg=C["panel"]); win.grab_set()

        hdr = tk.Frame(win, bg=C["choc"], pady=12); hdr.pack(fill=tk.X)
        tk.Label(hdr,text="Create Coupon",font=FONT_L,bg=C["choc"],fg=C["gold"]).pack()

        def fld(lbl, attr):
            tk.Label(win,text=lbl,font=FONT_SB,bg=C["panel"],fg=C["sub"]).pack(fill=tk.X,padx=22,pady=(6,0))
            e = tk.Entry(win,font=FONT_M,relief="flat",bd=0,bg=C["cream2"],fg=C["choc"])
            e.pack(fill=tk.X,padx=22,ipady=7,pady=(2,0))
            setattr(self,attr,e)

        fld("Code (e.g. SAVE20)","_cc")
        tk.Label(win,text="Type:",font=FONT_SB,bg=C["panel"],fg=C["sub"]).pack(fill=tk.X,padx=22,pady=(6,0))
        self._ct = tk.StringVar(value="percent")
        tf = tk.Frame(win,bg=C["panel"]); tf.pack(fill=tk.X,padx=22)
        for t in ["percent","flat"]:
            tk.Radiobutton(tf,text=t.title(),variable=self._ct,value=t,
                           bg=C["panel"],font=FONT_M,selectcolor=C["cream2"]).pack(side=tk.LEFT,padx=8)
        fld("Value (% or Rs.)","_cv")
        fld("Min Purchase (Rs.)","_cmin")
        fld("Max Uses","_cmax")
        fld("Expiry (YYYY-MM-DD or blank)","_cexp")

        def save():
            try:
                cursor.execute("""INSERT INTO coupons (code,type,value,min_purchase,max_uses,expiry_date)
                                  VALUES (?,?,?,?,?,?)""",
                               (self._cc.get().upper(),self._ct.get(),
                                float(self._cv.get()),float(self._cmin.get() or 0),
                                int(self._cmax.get() or 999),
                                self._cexp.get().strip() or None))
                conn.commit(); self._load_coupons(); win.destroy()
                messagebox.showinfo("Saved","Coupon created!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error","Code already exists.")
            except ValueError:
                messagebox.showerror("Error","Invalid numeric values.")

        pill_btn(win,"💾 Save Coupon",C["choc"],C["gold"],save,padx=20,pady=10).pack(pady=14)

    def _del_coupon(self):
        sel = self.coup_tree.selection()
        if not sel: return
        cursor.execute("DELETE FROM coupons WHERE id=?", (int(sel[0]),))
        conn.commit(); self._load_coupons()

    # ══════════════════════════ TAB: REPORTS ══════════════════════════════════
    def _tab_reports(self, parent):
        hdr = tk.Frame(parent, bg=C["cream"], pady=10)
        hdr.pack(fill=tk.X, padx=12)
        tk.Label(hdr, text="📊  Sales & Financial Reports", font=FONT_H,
                 bg=C["cream"], fg=C["choc"]).pack(side=tk.LEFT)

        # Date filter
        df = tk.Frame(parent, bg=C["cream2"], pady=8)
        df.pack(fill=tk.X, padx=12, pady=(0,8))

        tk.Label(df,text="From:",font=FONT_SB,bg=C["cream2"],fg=C["sub"]).pack(side=tk.LEFT,padx=8)
        self.r_from = tk.Entry(df,font=FONT_M,width=13,relief="flat",bd=0,
                               bg=C["panel"],fg=C["choc"])
        self.r_from.insert(0, datetime.date.today().strftime("%Y-%m-01"))
        self.r_from.pack(side=tk.LEFT,padx=4,ipady=6)

        tk.Label(df,text="To:",font=FONT_SB,bg=C["cream2"],fg=C["sub"]).pack(side=tk.LEFT,padx=4)
        self.r_to = tk.Entry(df,font=FONT_M,width=13,relief="flat",bd=0,
                             bg=C["panel"],fg=C["choc"])
        self.r_to.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.r_to.pack(side=tk.LEFT,padx=4,ipady=6)

        pill_btn(df,"🔍 Load",C["choc"],C["gold"],self._load_report,padx=14,pady=6).pack(side=tk.LEFT,padx=8)
        pill_btn(df,"📤 Export",C["blue"],"white",self._export_report,padx=14,pady=6).pack(side=tk.LEFT,padx=4)

        # Summary cards
        self.rep_cards = tk.Frame(parent, bg=C["cream"])
        self.rep_cards.pack(fill=tk.X, padx=12, pady=4)

        # Treeview
        cols = ("Invoice","Date","Subtotal","Discount","Tax","Total","Payment","Cashier")
        self.rep_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols:
            self.rep_tree.heading(c, text=c)
            self.rep_tree.column(c, width=100, anchor="center")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.rep_tree.yview)
        self.rep_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,12))
        self.rep_tree.pack(fill=tk.BOTH, expand=True, padx=12)
        self._load_report()

    def _load_report(self):
        for i in self.rep_tree.get_children(): self.rep_tree.delete(i)
        for w in self.rep_cards.winfo_children(): w.destroy()
        f, t = self.r_from.get().strip(), self.r_to.get().strip()
        cursor.execute("""SELECT invoice_no,date,subtotal,discount,tax,total,
                                 payment_method,cashier,is_return
                          FROM sales WHERE date(date) BETWEEN ? AND ?
                          ORDER BY date DESC""", (f,t))
        rows  = cursor.fetchall()
        rev   = disc = tax = cnt = 0
        for row in rows:
            self.rep_tree.insert("","end", values=row[:-1])
            if not row[8]:
                rev += row[5]; disc += row[3]; tax += row[4]; cnt += 1

        cards_data = [
            ("🧾 Orders",        str(cnt),               C["choc"]),
            ("💰 Revenue",       f"Rs. {rev:,.0f}",      C["green"]),
            ("🏷️ Discounts",     f"Rs. {disc:,.0f}",     C["gold"]),
            ("🧾 Tax Collected", f"Rs. {tax:,.0f}",      C["blue"]),
        ]
        for lbl, val, col in cards_data:
            c = tk.Frame(self.rep_cards, bg=col, padx=20, pady=14,
                         relief="flat", bd=0)
            c.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            tk.Label(c, text=val,  font=("Helvetica",18,"bold"),
                     bg=col, fg="white").pack()
            tk.Label(c, text=lbl,  font=FONT_S, bg=col, fg="white").pack()

    def _export_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if not path: return
        cursor.execute("""SELECT invoice_no,date,subtotal,discount,tax,total,
                                 payment_method,cashier FROM sales WHERE date(date) BETWEEN ? AND ?""",
                       (self.r_from.get(), self.r_to.get()))
        with open(path,"w",newline="",encoding="utf-8") as fl:
            w = csv.writer(fl)
            w.writerow(["Invoice","Date","Subtotal","Discount","Tax","Total","Payment","Cashier"])
            w.writerows(cursor.fetchall())
        messagebox.showinfo("Exported",f"Saved to {path}")

    # ══════════════════════════ TAB: RETURNS ══════════════════════════════════
    def _tab_returns(self, parent):
        tk.Label(parent, text="↩  Returns & Refunds", font=FONT_H,
                 bg=C["cream"], fg=C["blue"]).pack(pady=(10,6), padx=12, anchor="w")

        # Step 1 – Look up
        lf = tk.LabelFrame(parent, text=" 1. Look Up Invoice ", font=FONT_MB,
                           bg=C["cream"], fg=C["blue"], padx=12, pady=10)
        lf.pack(fill=tk.X, padx=14, pady=(0,6))

        r1 = tk.Frame(lf, bg=C["cream"]); r1.pack(fill=tk.X)
        tk.Label(r1, text="Invoice No:", font=FONT_M, bg=C["cream"]).pack(side=tk.LEFT)
        self.ret_inv_ent = tk.Entry(r1, font=FONT_M, width=22, relief="flat", bd=0,
                                    bg=C["panel"], fg=C["choc"],
                                    highlightthickness=1, highlightbackground=C["border"])
        self.ret_inv_ent.pack(side=tk.LEFT, padx=8, ipady=6)
        pill_btn(r1,"🔍 Fetch",C["blue"],"white",
                 self._ret_fetch_invoice,padx=14,pady=6).pack(side=tk.LEFT)

        self.ret_info_lbl = tk.Label(lf, text="", font=FONT_S, bg=C["cream"], fg=C["sub"])
        self.ret_info_lbl.pack(anchor="w", pady=(6,0))

        # Step 2 – Items
        if2 = tk.LabelFrame(parent, text=" 2. Select Items to Return ", font=FONT_MB,
                            bg=C["cream"], fg=C["blue"], padx=12, pady=8)
        if2.pack(fill=tk.X, padx=14, pady=(0,6))

        item_cols = ("✓","Product","Sold Qty","Return Qty","Unit Price","Refund")
        self.ret_items_tree = ttk.Treeview(if2, columns=item_cols, show="headings",
                                           height=6, selectmode="extended")
        for c, w in zip(item_cols, [30,200,80,90,90,90]):
            self.ret_items_tree.heading(c, text=c)
            self.ret_items_tree.column(c, width=w, anchor="center")
        self.ret_items_tree.pack(fill=tk.X)

        qf = tk.Frame(if2, bg=C["cream"]); qf.pack(fill=tk.X, pady=(6,0))
        tk.Label(qf, text="Return Qty for selected:", font=FONT_S, bg=C["cream"]).pack(side=tk.LEFT)
        self.ret_qty_var = tk.IntVar(value=1)
        tk.Spinbox(qf, textvariable=self.ret_qty_var, from_=1, to=999,
                   font=FONT_M, width=5, relief="flat").pack(side=tk.LEFT, padx=6)
        pill_btn(qf,"Set Qty",C["blue"],"white",self._ret_set_qty,padx=10,pady=4,font=FONT_S).pack(side=tk.LEFT)
        pill_btn(qf,"Select All",C["cream2"],C["sub"],self._ret_select_all,padx=10,pady=4,font=FONT_S).pack(side=tk.LEFT,padx=6)

        # Step 3 – Confirm
        rf3 = tk.LabelFrame(parent, text=" 3. Reason & Confirm ", font=FONT_MB,
                            bg=C["cream"], fg=C["blue"], padx=12, pady=10)
        rf3.pack(fill=tk.X, padx=14, pady=(0,6))
        rf3a = tk.Frame(rf3, bg=C["cream"]); rf3a.pack(fill=tk.X)
        tk.Label(rf3a, text="Reason:", font=FONT_M, bg=C["cream"]).pack(side=tk.LEFT)
        self.ret_reason_var = tk.StringVar(value="Customer Request")
        ttk.Combobox(rf3a, textvariable=self.ret_reason_var,
                     values=["Customer Request","Defective Product","Wrong Item","Quality Issue","Other"],
                     state="readonly", width=22, font=FONT_M).pack(side=tk.LEFT, padx=8)

        self.ret_refund_lbl = tk.Label(rf3, text="Refund Total: Rs. 0.00",
                                       font=("Georgia",14,"bold"), bg=C["cream"], fg=C["blue"])
        self.ret_refund_lbl.pack(pady=6)
        pill_btn(rf3,"✔  Process Return & Refund",C["blue"],"white",
                 self._ret_process,padx=20,pady=10).pack(pady=4)

        sep(parent)

        # History
        tk.Label(parent, text="Return History", font=FONT_MB,
                 bg=C["cream"], fg=C["sub"]).pack(anchor="w", padx=14)
        hist_cols = ("Return Inv","Original Inv","Refund","Reason","Cashier","Date")
        self.ret_hist_tree = ttk.Treeview(parent, columns=hist_cols, show="headings", height=5)
        for c in hist_cols:
            self.ret_hist_tree.heading(c, text=c)
            self.ret_hist_tree.column(c, width=120, anchor="center")
        rhs = ttk.Scrollbar(parent, orient="vertical", command=self.ret_hist_tree.yview)
        self.ret_hist_tree.configure(yscrollcommand=rhs.set)
        rhs.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,14))
        self.ret_hist_tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)

        self._ret_sale_id   = None
        self._ret_sale_data = []
        self._ret_load_history()

    def _ret_fetch_invoice(self):
        inv = self.ret_inv_ent.get().strip().upper()
        if not inv:
            messagebox.showwarning("Input","Enter an invoice number."); return
        cursor.execute("SELECT id,date,total,cashier,is_return FROM sales WHERE invoice_no=?", (inv,))
        sale = cursor.fetchone()
        if not sale:
            messagebox.showerror("Not Found",f"Invoice '{inv}' not found."); return
        sid, sdate, stotal, scashier, is_ret = sale
        if is_ret:
            messagebox.showwarning("Already Returned","This invoice is fully returned."); return
        self._ret_sale_id = sid
        self.ret_info_lbl.config(
            text=f"Date: {sdate}  |  Cashier: {scashier}  |  Total: Rs. {stotal:.2f}",
            fg=C["green"])
        cursor.execute("""SELECT si.id,si.product_id,si.product_name,si.quantity,si.unit_price
                          FROM sale_items si WHERE si.sale_id=?""", (sid,))
        rows = cursor.fetchall()
        for i in self.ret_items_tree.get_children():
            self.ret_items_tree.delete(i)
        self._ret_sale_data = []
        for r in rows:
            item_id, pid, pname, qty, uprice = r
            self._ret_sale_data.append({"item_id":item_id,"pid":pid,"name":pname,
                                         "sold_qty":qty,"ret_qty":qty,"unit_price":uprice})
            self.ret_items_tree.insert("","end", iid=str(item_id),
                values=("✓",pname,qty,qty,f"{uprice:.2f}",f"{qty*uprice:.2f}"))
        self._ret_update_total()

    def _ret_set_qty(self):
        sel = self.ret_items_tree.selection()
        if not sel:
            messagebox.showwarning("Select","Select an item first."); return
        iid  = int(sel[0])
        item = next((x for x in self._ret_sale_data if x["item_id"]==iid), None)
        if not item: return
        q = self.ret_qty_var.get()
        if q < 0 or q > item["sold_qty"]:
            messagebox.showerror("Invalid",f"Qty must be 0–{item['sold_qty']}."); return
        item["ret_qty"] = q
        self.ret_items_tree.item(str(iid), values=(
            "✓" if q>0 else "✗", item["name"], item["sold_qty"], q,
            f"{item['unit_price']:.2f}", f"{q*item['unit_price']:.2f}"))
        self._ret_update_total()

    def _ret_select_all(self):
        for item in self._ret_sale_data:
            item["ret_qty"] = item["sold_qty"]
            self.ret_items_tree.item(str(item["item_id"]), values=(
                "✓", item["name"], item["sold_qty"], item["sold_qty"],
                f"{item['unit_price']:.2f}",
                f"{item['sold_qty']*item['unit_price']:.2f}"))
        self._ret_update_total()

    def _ret_update_total(self):
        total = sum(x["ret_qty"]*x["unit_price"] for x in self._ret_sale_data)
        self.ret_refund_lbl.config(text=f"Refund Total: Rs. {total:.2f}")

    def _ret_process(self):
        if not self._ret_sale_id:
            messagebox.showwarning("No Invoice","Fetch an invoice first."); return
        items = [x for x in self._ret_sale_data if x["ret_qty"]>0]
        if not items:
            messagebox.showwarning("Nothing Selected","Set return qty > 0."); return
        refund = sum(x["ret_qty"]*x["unit_price"] for x in items)
        reason = self.ret_reason_var.get()
        orig   = self.ret_inv_ent.get().strip().upper()
        ret_inv = next_return_invoice()
        if not messagebox.askyesno("Confirm Return",
            f"Return {len(items)} item(s)?\nRefund: Rs. {refund:.2f}\nReason: {reason}"):
            return
        cursor.execute("""INSERT INTO returns (return_invoice,original_invoice,refund_amount,reason,cashier)
                          VALUES (?,?,?,?,?)""", (ret_inv,orig,refund,reason,self.current_user))
        rid = cursor.lastrowid
        for item in items:
            cursor.execute("""INSERT INTO return_items (return_id,product_id,product_name,quantity,unit_price,refund_total)
                              VALUES (?,?,?,?,?,?)""",
                           (rid,item["pid"],item["name"],item["ret_qty"],
                            item["unit_price"],item["ret_qty"]*item["unit_price"]))
            cursor.execute("UPDATE products SET stock=stock+? WHERE id=?",
                           (item["ret_qty"],item["pid"]))
            cursor.execute("""INSERT INTO stock_log (product_id,product_name,change_qty,reason)
                              VALUES (?,?,?,?)""",
                           (item["pid"],item["name"],item["ret_qty"],f"Return: {ret_inv}"))
        total_sold = sum(x["sold_qty"] for x in self._ret_sale_data)
        total_ret  = sum(x["ret_qty"]  for x in self._ret_sale_data)
        if total_ret >= total_sold:
            cursor.execute("UPDATE sales SET is_return=1 WHERE id=?", (self._ret_sale_id,))
        conn.commit()
        receipt = self._build_return_receipt(ret_inv, orig, items, refund, reason)
        self._show_receipt(receipt, title="Refund Receipt")
        self._ret_sale_id = None; self._ret_sale_data = []
        self.ret_inv_ent.delete(0, tk.END)
        self.ret_info_lbl.config(text="")
        for i in self.ret_items_tree.get_children(): self.ret_items_tree.delete(i)
        self.ret_refund_lbl.config(text="Refund Total: Rs. 0.00")
        self._ret_load_history(); self._pos_load_products()

    def _build_return_receipt(self, ret_inv, orig_inv, items, refund_total, reason):
        lines = ["═"*40,"       Ayesha's Royal Bakes ",
                 "       *** REFUND RECEIPT ***","═"*40,
                 f"Return Inv : {ret_inv}",f"Orig. Inv  : {orig_inv}",
                 f"Date       : {datetime.datetime.now().strftime('%d-%b-%Y %H:%M')}",
                 f"Cashier    : {self.current_user}",f"Reason     : {reason}",
                 "─"*40,"Returned Items:"]
        for item in items:
            lines.append(f"  {item['name'][:22]:<22} x{item['ret_qty']}")
            lines.append(f"  @ Rs.{item['unit_price']:.2f} = Rs.{item['ret_qty']*item['unit_price']:.2f}")
        lines += ["─"*40,f"  REFUND TOTAL : Rs. {refund_total:.2f}","═"*40,
                  "  Stock restored. Apologies for the inconvenience.","═"*40]
        return "\n".join(lines)

    def _ret_load_history(self):
        for i in self.ret_hist_tree.get_children(): self.ret_hist_tree.delete(i)
        cursor.execute("""SELECT return_invoice,original_invoice,refund_amount,reason,cashier,date
                          FROM returns ORDER BY date DESC""")
        for row in cursor.fetchall():
            self.ret_hist_tree.insert("","end",
                values=(row[0],row[1],f"Rs. {row[2]:.2f}",row[3],row[4],row[5]))

    # ══════════════════════════ TAB: CUSTOMERS ════════════════════════════════
    def _tab_customers(self, parent):
        hdr = tk.Frame(parent, bg=C["cream"], pady=10); hdr.pack(fill=tk.X, padx=12)
        tk.Label(hdr, text="👥  Customer Loyalty", font=FONT_H,
                 bg=C["cream"], fg=C["choc"]).pack(side=tk.LEFT)
        pill_btn(hdr,"+ Add Customer",C["choc"],C["gold"],
                 self._add_customer_win,padx=14,pady=7).pack(side=tk.RIGHT)

        cols = ("ID","Name","Phone","Email","Loyalty Pts","Total Spent","Since")
        self.cust_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols:
            self.cust_tree.heading(c, text=c)
            self.cust_tree.column(c, width=120, anchor="center")
        self.cust_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        self._load_customers()

    def _load_customers(self):
        for i in self.cust_tree.get_children(): self.cust_tree.delete(i)
        cursor.execute("SELECT id,name,phone,email,loyalty_pts,total_spent,created_at FROM customers")
        for row in cursor.fetchall():
            self.cust_tree.insert("","end", values=row)

    def _add_customer_win(self):
        win = tk.Toplevel(self.root)
        win.title("Add Customer"); win.geometry("360,320".replace(",","x"))
        win.geometry("360x320"); win.configure(bg=C["panel"]); win.grab_set()
        hdr = tk.Frame(win, bg=C["choc"], pady=12); hdr.pack(fill=tk.X)
        tk.Label(hdr, text="New Customer", font=FONT_L, bg=C["choc"], fg=C["gold"]).pack()
        for lbl, attr in [("Name","_cname"),("Phone","_cphone"),("Email","_cemail")]:
            tk.Label(win, text=lbl, font=FONT_SB, bg=C["panel"], fg=C["sub"]).pack(fill=tk.X,padx=22,pady=(8,0))
            e = tk.Entry(win, font=FONT_M, relief="flat", bd=0, bg=C["cream2"], fg=C["choc"])
            e.pack(fill=tk.X, padx=22, ipady=7)
            setattr(self, attr, e)
        def save():
            try:
                cursor.execute("INSERT INTO customers (name,phone,email) VALUES (?,?,?)",
                               (self._cname.get(),self._cphone.get(),self._cemail.get()))
                conn.commit(); self._load_customers(); win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error","Phone already exists.")
        pill_btn(win,"💾 Save",C["choc"],C["gold"],save,padx=20,pady=10).pack(pady=14)

    # ══════════════════════════ TAB: EXPENSES ═════════════════════════════════
    def _tab_expenses(self, parent):
        hdr = tk.Frame(parent, bg=C["cream"], pady=10); hdr.pack(fill=tk.X, padx=12)
        tk.Label(hdr, text="💸  Expense Tracker", font=FONT_H,
                 bg=C["cream"], fg=C["choc"]).pack(side=tk.LEFT)
        pill_btn(hdr,"+ Add Expense",C["choc"],C["gold"],
                 self._add_expense_win,padx=14,pady=7).pack(side=tk.RIGHT)

        cols = ("ID","Category","Amount","Description","Date")
        self.exp_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols:
            self.exp_tree.heading(c, text=c)
            self.exp_tree.column(c, width=160, anchor="center")
        self.exp_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        self._load_expenses()

    def _load_expenses(self):
        for i in self.exp_tree.get_children(): self.exp_tree.delete(i)
        cursor.execute("SELECT id,category,amount,description,date FROM expenses ORDER BY date DESC")
        for row in cursor.fetchall():
            self.exp_tree.insert("","end", values=row)

    def _add_expense_win(self):
        win = tk.Toplevel(self.root); win.title("Add Expense")
        win.geometry("360x300"); win.configure(bg=C["panel"]); win.grab_set()
        hdr = tk.Frame(win, bg=C["choc"], pady=12); hdr.pack(fill=tk.X)
        tk.Label(hdr,text="Add Expense",font=FONT_L,bg=C["choc"],fg=C["gold"]).pack()
        for lbl, attr in [("Category","_ecat"),("Amount (Rs.)","_eamt"),("Description","_edesc")]:
            tk.Label(win,text=lbl,font=FONT_SB,bg=C["panel"],fg=C["sub"]).pack(fill=tk.X,padx=22,pady=(8,0))
            e = tk.Entry(win,font=FONT_M,relief="flat",bd=0,bg=C["cream2"],fg=C["choc"])
            e.pack(fill=tk.X,padx=22,ipady=7)
            setattr(self,attr,e)
        def save():
            try:
                cursor.execute("INSERT INTO expenses (category,amount,description) VALUES (?,?,?)",
                               (self._ecat.get(),float(self._eamt.get()),self._edesc.get()))
                conn.commit(); self._load_expenses(); win.destroy()
            except ValueError:
                messagebox.showerror("Error","Invalid amount.")
        pill_btn(win,"💾 Save",C["choc"],C["gold"],save,padx=20,pady=10).pack(pady=14)

    # ══════════════════════════ TAB: SETTINGS ════════════════════════════════
    def _tab_settings(self, parent):
        tk.Label(parent, text="⚙️  System Settings", font=FONT_H,
                 bg=C["cream"], fg=C["choc"]).pack(pady=(10,6), padx=12, anchor="w")

        # Logo
        logo_f = tk.LabelFrame(parent, text=" Store Logo ", font=FONT_MB,
                               bg=C["cream"], fg=C["choc"], padx=16, pady=12)
        logo_f.pack(fill=tk.X, padx=16, pady=6)
        self.logo_prev = tk.Label(logo_f, bg=C["cream"])
        self.logo_prev.pack()
        self._render_logo_on(self.logo_prev, (220,60))

        def pick_logo():
            p = filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg")])
            if p:
                dest = os.path.join(IMG_DIR, "store_logo"+os.path.splitext(p)[1])
                shutil.copy2(p, dest); self.logo_path = dest
                self._render_logo_on(self.logo_prev, (220,60))
                messagebox.showinfo("Logo Updated","Restart to apply to sidebar.")

        pill_btn(logo_f,"📷 Change Logo",C["choc"],C["gold"],pick_logo,padx=14,pady=6).pack(pady=6)

        # Users
        usr_f = tk.LabelFrame(parent, text=" User Management ", font=FONT_MB,
                              bg=C["cream"], fg=C["choc"], padx=16, pady=10)
        usr_f.pack(fill=tk.X, padx=16, pady=6)
        cols = ("Username","Role","Active")
        self.usr_tree = ttk.Treeview(usr_f, columns=cols, show="headings", height=5)
        for c in cols:
            self.usr_tree.heading(c, text=c)
            self.usr_tree.column(c, width=130, anchor="center")
        self.usr_tree.pack(fill=tk.X)
        self._load_users()
        bf = tk.Frame(usr_f, bg=C["cream"]); bf.pack(pady=6)
        pill_btn(bf,"+ Add User",C["choc"],C["gold"],self._add_user_win,padx=14,pady=6).pack(side=tk.LEFT,padx=4)
        pill_btn(bf,"🗑 Remove",C["red"],"white",self._del_user,padx=14,pady=6).pack(side=tk.LEFT,padx=4)

        # Tax
        tax_f = tk.LabelFrame(parent, text=" Tax Rate ", font=FONT_MB,
                              bg=C["cream"], fg=C["choc"], padx=16, pady=8)
        tax_f.pack(fill=tk.X, padx=16, pady=6)
        tf = tk.Frame(tax_f, bg=C["cream"]); tf.pack()
        tk.Label(tf, text="Tax %:", font=FONT_M, bg=C["cream"]).pack(side=tk.LEFT)
        self.tax_ent = tk.Entry(tf, font=FONT_M, width=8, relief="flat", bd=0,
                                bg=C["panel"], fg=C["choc"])
        self.tax_ent.insert(0, str(int(TAX_RATE*100)))
        self.tax_ent.pack(side=tk.LEFT, padx=8, ipady=5)

        def save_tax():
            global TAX_RATE
            try:
                TAX_RATE = float(self.tax_ent.get()) / 100
                messagebox.showinfo("Saved",f"Tax rate: {TAX_RATE*100:.1f}%")
            except:
                messagebox.showerror("Error","Invalid value.")

        pill_btn(tax_f,"Save Tax Rate",C["choc"],C["gold"],save_tax,padx=14,pady=6).pack(pady=4)

        # DB Backup
        db_f = tk.LabelFrame(parent, text=" Database Backup ", font=FONT_MB,
                             bg=C["cream"], fg=C["choc"], padx=16, pady=8)
        db_f.pack(fill=tk.X, padx=16, pady=6)
        pill_btn(db_f,"💾 Backup Database",C["blue"],"white",self._backup_db,padx=16,pady=8).pack()

    def _load_users(self):
        for i in self.usr_tree.get_children(): self.usr_tree.delete(i)
        cursor.execute("SELECT id,username,role,is_active FROM users")
        for row in cursor.fetchall():
            self.usr_tree.insert("","end", iid=str(row[0]),
                values=(row[1],row[2],"Yes" if row[3] else "No"))

    def _add_user_win(self):
        win = tk.Toplevel(self.root); win.title("Add User")
        win.geometry("340x320"); win.configure(bg=C["panel"]); win.grab_set()
        hdr = tk.Frame(win,bg=C["choc"],pady=12); hdr.pack(fill=tk.X)
        tk.Label(hdr,text="New User",font=FONT_L,bg=C["choc"],fg=C["gold"]).pack()
        for lbl,attr,show in [("Username","_uname",""),("Password","_upass","●")]:
            tk.Label(win,text=lbl,font=FONT_SB,bg=C["panel"],fg=C["sub"]).pack(fill=tk.X,padx=22,pady=(8,0))
            e = tk.Entry(win,show=show,font=FONT_M,relief="flat",bd=0,bg=C["cream2"],fg=C["choc"])
            e.pack(fill=tk.X,padx=22,ipady=7); setattr(self,attr,e)
        tk.Label(win,text="Role:",font=FONT_SB,bg=C["panel"],fg=C["sub"]).pack(fill=tk.X,padx=22,pady=(8,0))
        self._urole = tk.StringVar(value="cashier")
        rf = tk.Frame(win,bg=C["panel"]); rf.pack()
        for r in ["cashier","admin"]:
            tk.Radiobutton(rf,text=r.title(),variable=self._urole,value=r,
                           bg=C["panel"],font=FONT_M,selectcolor=C["cream2"]).pack(side=tk.LEFT,padx=12)
        def save():
            try:
                cursor.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                               (self._uname.get(),_hash(self._upass.get()),self._urole.get()))
                conn.commit(); self._load_users(); win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error","Username already exists.")
        pill_btn(win,"💾 Save",C["choc"],C["gold"],save,padx=20,pady=10).pack(pady=14)

    def _del_user(self):
        sel = self.usr_tree.selection()
        if not sel: return
        uname = self.usr_tree.item(sel[0])["values"][0]
        if uname == self.current_user:
            messagebox.showwarning("Error","Cannot delete yourself."); return
        cursor.execute("DELETE FROM users WHERE id=?", (int(sel[0]),))
        conn.commit(); self._load_users()

    def _backup_db(self):
        path = filedialog.asksaveasfilename(defaultextension=".db",filetypes=[("SQLite","*.db")])
        if path:
            shutil.copy2(DB_PATH, path)
            messagebox.showinfo("Backup","Database backed up!")

    # ─── Utility ─────────────────────────────────────────────────────────────
    def _clear_root(self):
        for w in self.root.winfo_children():
            w.destroy()

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = BakesByAyeshaPOS(root)
    root.mainloop()
    conn.close()