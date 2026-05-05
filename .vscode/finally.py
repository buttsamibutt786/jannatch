"""
╔══════════════════════════════════════════════════════════╗
║       BAKES BY AYESHA — Modern POS v3.0                 ║
║   Baby Pink & White · Horizontal Nav · Pillow Images    ║
╚══════════════════════════════════════════════════════════╝
Dependencies: pip install Pillow
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3, os, shutil, datetime, csv, hashlib, math, io

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    PILLOW_INSTALLED = True
except ImportError:
    PILLOW_INSTALLED = False
    print("WARNING: Pillow not installed. Run: pip install Pillow")

# ─── DATABASE SETUP ─────────────────────────────────────────────────────────
DB_PATH = "ayesha_bakery.db"
IMG_DIR = "bakery_images"
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
        subtotal    REAL, discount REAL DEFAULT 0, tax REAL DEFAULT 0,
        total       REAL, payment_method TEXT DEFAULT 'Cash',
        cashier     TEXT DEFAULT 'Ayesha', notes TEXT,
        is_return   INTEGER DEFAULT 0,
        date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sale_items (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id     INTEGER REFERENCES sales(id),
        product_id  INTEGER REFERENCES products(id),
        product_name TEXT, quantity INTEGER,
        unit_price  REAL, discount REAL DEFAULT 0, total REAL
    );
    CREATE TABLE IF NOT EXISTS coupons (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        TEXT UNIQUE NOT NULL,
        type        TEXT DEFAULT 'percent',
        value       REAL NOT NULL, min_purchase REAL DEFAULT 0,
        max_uses    INTEGER DEFAULT 999, used_count INTEGER DEFAULT 0,
        expiry_date TEXT, is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT, amount REAL, description TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT UNIQUE, email TEXT,
        loyalty_pts INTEGER DEFAULT 0, total_spent REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE, password TEXT,
        role TEXT DEFAULT 'cashier', is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS stock_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER, product_name TEXT,
        change_qty INTEGER, reason TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_invoice TEXT UNIQUE, original_invoice TEXT,
        refund_amount REAL, reason TEXT, cashier TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS return_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_id INTEGER REFERENCES returns(id),
        product_id INTEGER, product_name TEXT,
        quantity INTEGER, unit_price REAL, refund_total REAL
    );
''')

for col, defn in [("discount_pct","REAL DEFAULT 0"),
                   ("is_bestseller","INTEGER DEFAULT 0"),
                   ("is_new","INTEGER DEFAULT 0")]:
    try: cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {defn}")
    except sqlite3.OperationalError: pass
conn.commit()

def _hash(p): return hashlib.sha256(p.encode()).hexdigest()

cursor.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)",
               ("Ayesha", _hash("admin123"), "admin"))
for code, typ, val, mn in [("AYESHA10","percent",10,0),
                             ("WELCOME5","percent",5,0),
                             ("FLAT50","flat",50,500)]:
    cursor.execute("INSERT OR IGNORE INTO coupons (code,type,value,min_purchase) VALUES (?,?,?,?)",
                   (code,typ,val,mn))

SAMPLE_PRODUCTS = [
    ("Butter Croissant",280,40,"Pastries",0,0,1,1),
    ("Sourdough Loaf",450,25,"Artisan Breads",0,0,1,0),
    ("Red Velvet Cupcake",180,60,"Cupcakes",15,1,1,0),
    ("Chocolate Truffle Cake",1800,8,"Custom Cakes",0,0,1,1),
    ("Cheese Danish",220,35,"Pastries",10,1,0,0),
    ("Cinnamon Roll",250,30,"Pastries",0,0,0,1),
    ("Almond Croissant",320,28,"Pastries",0,0,1,0),
    ("Blueberry Muffin",160,50,"Muffins",20,1,0,0),
    ("Focaccia Bread",380,15,"Artisan Breads",0,0,0,1),
    ("Strawberry Tart",350,20,"Tarts",0,0,1,0),
    ("Mini Eclairs (6pc)",480,18,"Pastries",0,0,1,1),
    ("Mango Juice",120,60,"Juices",0,0,0,1),
    ("Strawberry Milkshake",180,40,"Juices",0,1,1,0),
    ("Samosa (per piece)",60,80,"Savories",0,0,0,0),
    ("Brownie Fudge",200,55,"Desserts",10,1,0,0),
    ("Vanilla Bean Macaron",130,70,"Macarons",0,0,1,1),
    ("Lemon Tart",320,22,"Tarts",0,0,1,0),
    ("Chicken Patty",150,45,"Savories",0,0,0,0),
]
for nm,pr,st,cat,disc,bs,act,new in SAMPLE_PRODUCTS:
    cursor.execute("""INSERT OR IGNORE INTO products
        (name,price,stock,category,discount_pct,is_bestseller,is_active,is_new,cost_price)
        VALUES (?,?,?,?,?,?,?,?,?)""", (nm,pr,st,cat,disc,bs,act,new,pr*0.4))
conn.commit()

# ─── BABY PINK & WHITE COLOUR PALETTE ───────────────────────────────────────
P = {
    "white":       "#FFFFFF",
    "snow":        "#FFF8FA",
    "pink_pale":   "#FFF0F5",
    "pink_light":  "#FFD6E7",
    "pink":        "#FFB3CE",
    "pink_mid":    "#FF8FB1",
    "pink_deep":   "#E8527A",
    "pink_dark":   "#C23B65",
    "rose":        "#FF6B9D",
    "lilac":       "#F0E6FF",
    "mauve":       "#DDB8D4",
    "cream":       "#FFF9F0",
    "text_dark":   "#3D1A2E",
    "text_mid":    "#7A3F5A",
    "text_soft":   "#B07090",
    "text_gray":   "#C4A0B0",
    "green":       "#4CAF82",
    "green_lt":    "#E8F8F0",
    "red":         "#E84B6A",
    "red_lt":      "#FFE8ED",
    "blue":        "#7B9ED9",
    "blue_lt":     "#EEF3FF",
    "gold":        "#F5B85A",
    "border":      "#FFE0EC",
    "shadow":      "#F5D0E0",
    "nav_bg":      "#FFFFFF",
    "card_bg":     "#FFFFFF",
    "hover":       "#FFF0F5",
    "selected":    "#FFD6E7",
    "badge_bs":    "#F5B85A",
    "badge_new":   "#4CAF82",
    "badge_off":   "#E84B6A",
}

FONT_HERO  = ("Georgia", 26, "bold")
FONT_H     = ("Georgia", 18, "bold")
FONT_L     = ("Georgia", 14, "bold")
FONT_M     = ("Helvetica", 11)
FONT_MB    = ("Helvetica", 11, "bold")
FONT_S     = ("Helvetica", 9)
FONT_SB    = ("Helvetica", 9, "bold")
FONT_TINY  = ("Helvetica", 8)

TAX_RATE = 0.05

# ─── PILLOW IMAGE GENERATORS ─────────────────────────────────────────────────
def _lerp_color(c1, c2, t):
    return tuple(int(c1[i]*(1-t)+c2[i]*t) for i in range(3))

def make_product_image(category="Pastries", w=160, h=130):
    """Generate beautiful gradient placeholder images per category."""
    themes = {
        "Pastries":       ([(255,220,235),(255,180,210)], "🥐"),
        "Artisan Breads": ([(255,235,200),(240,190,130)], "🍞"),
        "Custom Cakes":   ([(255,200,220),(230,140,170)], "🎂"),
        "Cupcakes":       ([(255,210,230),(255,160,190)], "🧁"),
        "Muffins":        ([(230,210,255),(190,155,220)], "🫐"),
        "Tarts":          ([(215,255,215),(140,210,150)], "🥧"),
        "Macarons":       ([(255,210,245),(220,160,200)], "🍬"),
        "Savories":       ([(240,240,210),(190,190,140)], "🥪"),
        "Desserts":       ([(255,220,200),(230,160,120)], "🍰"),
        "Juices":         ([(210,255,230),(130,220,180)], "🥤"),
    }
    (c1, c2), icon = themes.get(category, ([(255,220,230),(220,160,180)], "🍩"))

    img = Image.new("RGB", (w, h), c1)
    draw = ImageDraw.Draw(img)

    # Soft diagonal gradient
    for y in range(h):
        for x in range(w):
            t = (x/w * 0.4 + y/h * 0.6)
            r,g,b = _lerp_color(c1, c2, t)
            draw.point((x, y), fill=(r, g, b))

    # Decorative circles (soft bokeh)
    for (cx, cy, cr, alpha) in [(int(w*0.75), int(h*0.2), 28, 40),
                                  (int(w*0.15), int(h*0.8), 22, 35),
                                  (int(w*0.5),  int(h*0.5), 15, 25)]:
        overlay = Image.new("RGBA", (w, h), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], fill=(255,255,255,alpha))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # Center icon (large emoji via font)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", 42)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 42)
        except:
            font = ImageFont.load_default()
    draw.text((w//2, h//2), icon, fill=(80,30,50,220), anchor="mm", font=font)

    # Soft vignette
    vign = Image.new("RGBA", (w,h), (0,0,0,0))
    vd = ImageDraw.Draw(vign)
    for i in range(20):
        alpha = int(i * 1.5)
        vd.rectangle([i, i, w-i, h-i], outline=(200,120,150, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), vign).convert("RGB")

    return img


def make_login_banner(w=500, h=600):
    img = Image.new("RGB", (w, h), (255, 220, 235))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y/h
        r = int(255*(1-t) + 230*t)
        g = int(220*(1-t) + 150*t)
        b = int(235*(1-t) + 190*t)
        draw.line([(0,y),(w,y)], fill=(r,g,b))
    # Decorative circles
    for cx,cy,cr,col in [
        (int(w*0.8), int(h*0.1), 100, (255,255,255,35)),
        (int(w*0.1), int(h*0.4), 80,  (255,255,255,25)),
        (int(w*0.6), int(h*0.7), 130, (255,255,255,20)),
        (int(w*0.9), int(h*0.85),70,  (255,255,255,30)),
    ]:
        ov = Image.new("RGBA",(w,h),(0,0,0,0))
        od = ImageDraw.Draw(ov)
        od.ellipse([cx-cr,cy-cr,cx+cr,cy+cr], fill=col)
        img = Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    return img


def make_topbar_gradient(w=1400, h=70):
    img = Image.new("RGB", (w, h), (255, 240, 248))
    draw = ImageDraw.Draw(img)
    for x in range(w):
        t = x/w
        r = int(255*(1-t) + 255*t)
        g = int(240*(1-t) + 210*t)
        b = int(248*(1-t) + 235*t)
        draw.line([(x,0),(x,h)], fill=(r,g,b))
    return img


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════
class BakesByAyeshaPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Bakes by Ayesha — POS v3")
        self.root.geometry("1380x880")
        self.root.minsize(1100, 700)
        self.root.configure(bg=P["snow"])

        self.current_user = None
        self.current_role = None
        self.logo_path = ""
        self._active_nav = None
        self._nav_btns = {}

        self._setup_styles()
        self.login_screen()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TNotebook", background=P["snow"], borderwidth=0)
        s.configure("TNotebook.Tab", font=FONT_MB, padding=[14,6],
                    background=P["pink_light"], foreground=P["text_mid"])
        s.map("TNotebook.Tab",
              background=[("selected", P["pink_deep"])],
              foreground=[("selected", "white")])
        s.configure("Treeview", font=FONT_M, rowheight=30,
                    background=P["white"], fieldbackground=P["white"],
                    foreground=P["text_dark"])
        s.configure("Treeview.Heading", font=FONT_SB,
                    background=P["pink_light"], foreground=P["text_dark"])
        s.map("Treeview",
              background=[("selected", P["pink_light"])],
              foreground=[("selected", P["pink_dark"])])
        s.configure("TScrollbar", background=P["pink_light"],
                    troughcolor=P["snow"], arrowcolor=P["pink_dark"])
        s.configure("Pink.TCombobox", fieldbackground=P["pink_pale"],
                    background=P["pink_light"])

    # ── HELPERS ──────────────────────────────────────────────────────────────
    def _pill(self, parent, text, bg, fg, cmd, padx=14, pady=7, font=FONT_MB, w=None):
        b = tk.Button(parent, text=text, bg=bg, fg=fg, font=font,
                      relief="flat", activebackground=bg, activeforeground=fg,
                      cursor="hand2", command=cmd, bd=0, padx=padx, pady=pady)
        if w: b.config(width=w)
        b.bind("<Enter>", lambda e: b.config(bg=self._darken(bg)))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    def _darken(self, hex_color, amt=15):
        try:
            h = hex_color.lstrip("#")
            r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
            return f"#{max(0,r-amt):02x}{max(0,g-amt):02x}{max(0,b-amt):02x}"
        except: return hex_color

    def _sep(self, parent, color=None, h=1, padx=0, pady=4):
        tk.Frame(parent, bg=color or P["border"], height=h).pack(
            fill=tk.X, pady=pady, padx=padx)

    def _card(self, parent, **kwargs):
        return tk.Frame(parent, bg=P["card_bg"],
                        highlightthickness=1,
                        highlightbackground=P["border"], **kwargs)

    def _label_field(self, parent, label, attr, show=""):
        tk.Label(parent, text=label, font=FONT_SB, bg=P["white"],
                 fg=P["text_mid"]).pack(fill=tk.X, padx=22, pady=(8,1))
        e = tk.Entry(parent, show=show, font=FONT_M, relief="flat", bd=0,
                     bg=P["pink_pale"], fg=P["text_dark"],
                     insertbackground=P["pink_deep"],
                     highlightthickness=1, highlightbackground=P["border"])
        e.pack(fill=tk.X, padx=22, ipady=8)
        setattr(self, attr, e)

    # ── LOGIN ─────────────────────────────────────────────────────────────────
    def login_screen(self):
        self._clear_root()
        self.root.configure(bg=P["pink_pale"])

        # Left pink panel
        left = tk.Frame(self.root, bg=P["pink_pale"], width=480)
        left.place(relx=0, rely=0, relwidth=0.38, relheight=1)

        if PILLOW_INSTALLED:
            banner = make_login_banner(480, 880)
            self._login_banner = ImageTk.PhotoImage(banner)
            tk.Label(left, image=self._login_banner, bd=0).place(x=0,y=0,relwidth=1,relheight=1)

        # Overlay content on left
        overlay = tk.Frame(left, bg="", bd=0)
        overlay.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(overlay, text="🎀", font=("Helvetica",56),
                 bg=P["pink_light"]).pack(pady=(0,8))
        tk.Label(overlay, text="Bakes by Ayesha",
                 font=("Georgia",26,"bold"),
                 bg=P["pink_light"], fg=P["text_dark"]).pack()
        tk.Label(overlay, text="Artisan Bakery & Sweets",
                 font=("Georgia",12,"italic"),
                 bg=P["pink_light"], fg=P["text_mid"]).pack(pady=(2,20))

        tk.Frame(overlay, bg=P["pink_mid"], height=2, width=200).pack(pady=6)

        for line in ["✦  Point of Sale System",
                     "✦  Inventory & Stock",
                     "✦  Sales Analytics",
                     "✦  Customer Loyalty"]:
            tk.Label(overlay, text=line, font=("Helvetica",11),
                     bg=P["pink_light"], fg=P["text_dark"]).pack(pady=3)

        # Right login form
        right = tk.Frame(self.root, bg=P["white"])
        right.place(relx=0.38, rely=0, relwidth=0.62, relheight=1)

        form = tk.Frame(right, bg=P["white"], padx=60, pady=50)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="Welcome Back 🌸",
                 font=("Georgia",28,"bold"),
                 bg=P["white"], fg=P["text_dark"]).pack(pady=(0,6))
        tk.Label(form, text="Sign in to your dashboard",
                 font=("Helvetica",12),
                 bg=P["white"], fg=P["text_soft"]).pack(pady=(0,30))

        for lbl, attr, show in [("USERNAME","_lu",""),("PASSWORD","_lp","●")]:
            tk.Label(form, text=lbl, font=("Helvetica",9,"bold"),
                     bg=P["white"], fg=P["text_soft"]).pack(anchor="w")
            ef = tk.Frame(form, bg=P["border"], pady=1)
            ef.pack(fill=tk.X, pady=(2,16))
            e = tk.Entry(ef, show=show, font=("Helvetica",14),
                         relief="flat", bd=0, bg=P["white"],
                         fg=P["text_dark"], insertbackground=P["pink_deep"])
            e.pack(fill=tk.X, ipady=10, padx=2)
            setattr(self, attr, e)

        self._lu.insert(0,"Ayesha")
        self._lp.insert(0,"admin123")
        self._lp.bind("<Return>", lambda e: self._do_login())

        login_btn = tk.Button(form, text="  SIGN IN  →  ",
                              bg=P["pink_deep"], fg="white",
                              font=("Helvetica",13,"bold"),
                              relief="flat", bd=0, cursor="hand2",
                              activebackground=P["pink_dark"],
                              activeforeground="white",
                              command=self._do_login, pady=14)
        login_btn.pack(fill=tk.X, pady=(8,0))

        self._login_err = tk.Label(form, text="", font=FONT_S,
                                   bg=P["white"], fg=P["red"])
        self._login_err.pack(pady=(8,0))

    def _do_login(self):
        u, p = self._lu.get().strip(), self._lp.get().strip()
        cursor.execute("SELECT role FROM users WHERE username=? AND password=? AND is_active=1",
                       (u, _hash(p)))
        row = cursor.fetchone()
        if row:
            self.current_user = u
            self.current_role = row[0]
            self._loading_overlay(callback=self.main_dashboard)
        else:
            self._login_err.config(text="⚠  Invalid username or password.")

    def _loading_overlay(self, callback=None, message="Loading..."):
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}"
                         f"+{self.root.winfo_x()}+{self.root.winfo_y()}")
        overlay.configure(bg=P["pink_pale"])
        overlay.attributes("-alpha", 0.0)

        tk.Label(overlay, text="🎀", font=("Helvetica",52),
                 bg=P["pink_pale"]).pack(pady=(160,8))
        tk.Label(overlay, text="Bakes by Ayesha",
                 font=("Georgia",20,"bold"),
                 bg=P["pink_pale"], fg=P["text_dark"]).pack()
        tk.Label(overlay, text=message, font=("Helvetica",11),
                 bg=P["pink_pale"], fg=P["text_soft"]).pack(pady=4)

        spin_lbl = tk.Label(overlay, text="◐", font=("Helvetica",26),
                            bg=P["pink_pale"], fg=P["pink_deep"])
        spin_lbl.pack(pady=10)
        spin_idx = [0]

        def animate():
            if not overlay.winfo_exists(): return
            spin_lbl.config(text=["◐","◓","◑","◒"][spin_idx[0]%4])
            spin_idx[0] += 1
            overlay.after(100, animate)

        animate()
        alpha = [0.0]
        def fade():
            if not overlay.winfo_exists(): return
            alpha[0] = min(alpha[0]+0.1, 0.97)
            overlay.attributes("-alpha", alpha[0])
            if alpha[0] < 0.97: overlay.after(25, fade)
            else: overlay.after(500, finish)

        def finish():
            overlay.destroy()
            if callback: callback()

        overlay.after(30, fade)

    # ── MAIN DASHBOARD ────────────────────────────────────────────────────────
    def main_dashboard(self):
        self._clear_root()
        self.root.configure(bg=P["snow"])

        # ── TOP HEADER BAR ───────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=P["white"], height=68)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # Pink accent line at very top
        tk.Frame(self.root, bg=P["pink_mid"], height=3).pack(fill=tk.X, side=tk.TOP)
        header.pack(fill=tk.X, side=tk.TOP)

        # Logo area
        logo_f = tk.Frame(header, bg=P["white"])
        logo_f.pack(side=tk.LEFT, padx=20)
        tk.Label(logo_f, text="🎀", font=("Helvetica",26),
                 bg=P["white"]).pack(side=tk.LEFT)
        name_f = tk.Frame(logo_f, bg=P["white"])
        name_f.pack(side=tk.LEFT, padx=6)
        tk.Label(name_f, text="Bakes by Ayesha",
                 font=("Georgia",15,"bold"),
                 bg=P["white"], fg=P["text_dark"]).pack(anchor="w")
        tk.Label(name_f, text="Artisan Bakery & Sweets",
                 font=("Helvetica",8),
                 bg=P["white"], fg=P["text_soft"]).pack(anchor="w")

        # Right: user + clock
        right_f = tk.Frame(header, bg=P["white"])
        right_f.pack(side=tk.RIGHT, padx=20)

        self._clock_lbl = tk.Label(right_f,
                                    text=datetime.datetime.now().strftime("%a, %d %b %Y  %H:%M"),
                                    font=("Helvetica",9),
                                    bg=P["white"], fg=P["text_soft"])
        self._clock_lbl.pack(anchor="e")
        self._tick_clock()

        user_pill = tk.Frame(right_f, bg=P["pink_pale"],
                             highlightthickness=1, highlightbackground=P["pink_mid"])
        user_pill.pack(anchor="e", pady=3)
        tk.Label(user_pill, text=f"👤  {self.current_user}  ·  {self.current_role.upper()}",
                 font=FONT_SB, bg=P["pink_pale"], fg=P["text_dark"],
                 padx=12, pady=5).pack(side=tk.LEFT)
        tk.Button(user_pill, text="Logout", font=FONT_TINY,
                  bg=P["pink_mid"], fg="white", relief="flat", bd=0,
                  padx=8, pady=5, cursor="hand2",
                  command=lambda: self._loading_overlay(
                      callback=self.login_screen, message="Logging out...")).pack(side=tk.LEFT)

        # ── HORIZONTAL NAV BAR ───────────────────────────────────────────────
        nav_outer = tk.Frame(self.root, bg=P["pink_pale"], pady=10)
        nav_outer.pack(fill=tk.X, side=tk.TOP)

        nav_inner = tk.Frame(nav_outer, bg=P["pink_pale"])
        nav_inner.pack()

        nav_items = [
            ("🛒", "Point of Sale",  self._tab_pos),
            ("📦", "Inventory",      self._tab_inventory),
            ("🏷️", "Coupons",        self._tab_coupons),
            ("📊", "Reports",        self._tab_reports),
            ("↩",  "Returns",        self._tab_returns),
            ("👥", "Customers",      self._tab_customers),
            ("💸", "Expenses",       self._tab_expenses),
            ("⚙️", "Settings",       self._tab_settings),
        ]

        # Content area
        self._content = tk.Frame(self.root, bg=P["snow"])
        self._content.pack(fill=tk.BOTH, expand=True)

        self._page = tk.Frame(self._content, bg=P["snow"])
        self._page.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self._nav_btns = {}
        for icon, name, builder in nav_items:
            btn_f = tk.Frame(nav_inner, bg=P["pink_pale"])
            btn_f.pack(side=tk.LEFT, padx=5)

            btn = tk.Button(btn_f,
                            text=f"  {icon}  {name}  ",
                            font=("Helvetica",10,"bold"),
                            bg=P["white"], fg=P["text_mid"],
                            relief="flat", bd=0, cursor="hand2",
                            pady=9, padx=4,
                            activebackground=P["pink_light"],
                            activeforeground=P["text_dark"],
                            command=lambda n=name, b=builder: self._nav_go(n, b))
            btn.pack()

            self._nav_btns[name] = btn

        # Start with POS
        self._nav_go("Point of Sale", self._tab_pos)

    def _tick_clock(self):
        if hasattr(self, '_clock_lbl') and self._clock_lbl.winfo_exists():
            self._clock_lbl.config(
                text=datetime.datetime.now().strftime("%a, %d %b %Y  %H:%M"))
            self.root.after(30000, self._tick_clock)

    def _nav_go(self, name, builder):
        # Reset all buttons
        for n, btn in self._nav_btns.items():
            btn.config(bg=P["white"], fg=P["text_mid"],
                       font=("Helvetica",10,"bold"))

        # Activate selected
        self._nav_btns[name].config(
            bg=P["pink_deep"], fg="white",
            font=("Helvetica",10,"bold"))
        self._active_nav = name

        for w in self._page.winfo_children():
            w.destroy()
        builder(self._page)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB: POINT OF SALE
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_pos(self, parent):
        self.cart = []
        self.applied_coupon = None

        # Left: products
        left = tk.Frame(parent, bg=P["snow"])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(14,6), pady=10)

        # Search row
        sr = tk.Frame(left, bg=P["snow"]); sr.pack(fill=tk.X, pady=(0,8))
        sf = tk.Frame(sr, bg=P["white"],
                      highlightthickness=1, highlightbackground=P["pink_mid"])
        sf.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(sf, text="🔍", font=("Helvetica",13), bg=P["white"],
                 fg=P["text_soft"]).pack(side=tk.LEFT, padx=10)
        self.pos_search = tk.Entry(sf, font=("Helvetica",12), relief="flat", bd=0,
                                   bg=P["white"], fg=P["text_dark"],
                                   insertbackground=P["pink_deep"])
        self.pos_search.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=9)
        self.pos_search.insert(0,"Search bakery items...")
        self.pos_search.bind("<FocusIn>",
            lambda e: self.pos_search.delete(0,tk.END)
            if self.pos_search.get()=="Search bakery items..." else None)
        self.pos_search.bind("<KeyRelease>", lambda e: self._pos_load())

        # Category pills
        cat_f = tk.Frame(left, bg=P["snow"]); cat_f.pack(fill=tk.X, pady=(0,8))
        self._pos_cat = tk.StringVar(value="All")
        self._cat_frame = tk.Frame(cat_f, bg=P["snow"])
        self._cat_frame.pack(fill=tk.X)
        self._build_cat_tabs()

        # Product grid canvas
        canvas = tk.Canvas(left, bg=P["snow"], highlightthickness=0)
        vsb = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(fill=tk.BOTH, expand=True)
        self._prod_frame = tk.Frame(canvas, bg=P["snow"])
        self._prod_wid = canvas.create_window((0,0), window=self._prod_frame, anchor="nw")
        self._prod_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self._prod_wid, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units"))
        self._pos_load()

        # Right: Cart
        right = tk.Frame(parent, bg=P["white"], width=360)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(6,14), pady=10)
        right.pack_propagate(False)

        cart_hdr = tk.Frame(right, bg=P["pink_deep"], pady=14)
        cart_hdr.pack(fill=tk.X)
        tk.Label(cart_hdr, text="🛒  Current Order",
                 font=("Georgia",14,"bold"),
                 bg=P["pink_deep"], fg="white").pack()

        cols = ("Product","Qty","Price","Total")
        self.cart_tree = ttk.Treeview(right, columns=cols, show="headings", height=10)
        for c,w in zip(cols,[138,38,72,72]):
            self.cart_tree.heading(c, text=c)
            self.cart_tree.column(c, width=w, anchor="center")
        self.cart_tree.pack(fill=tk.X, padx=8, pady=(10,0))
        self.cart_tree.bind("<Double-1>", self._edit_qty)

        self._sep(right, pady=6)

        # Coupon
        cf = tk.Frame(right, bg=P["white"]); cf.pack(fill=tk.X, padx=12, pady=4)
        tk.Label(cf, text="🏷️ Coupon:", font=FONT_SB,
                 bg=P["white"], fg=P["text_soft"]).pack(side=tk.LEFT)
        self.coupon_ent = tk.Entry(cf, font=FONT_M, width=12, relief="flat", bd=0,
                                   bg=P["pink_pale"], fg=P["text_dark"])
        self.coupon_ent.pack(side=tk.LEFT, padx=6, ipady=5)
        self._pill(cf,"Apply",P["pink_deep"],"white",self._apply_coupon,
                   font=FONT_SB,padx=10,pady=5).pack(side=tk.LEFT)

        self._sep(right, pady=4)

        # Totals
        tf = tk.Frame(right, bg=P["white"]); tf.pack(fill=tk.X, padx=14)
        self._lbl_sub  = self._tot_row(tf,"Subtotal:")
        self._lbl_disc = self._tot_row(tf,"Discount:",P["green"])
        self._lbl_tax  = self._tot_row(tf,f"Tax ({int(TAX_RATE*100)}%):")
        self._sep(right, P["pink_mid"], h=2, pady=4)
        self._lbl_total = self._tot_row(right,"TOTAL:", P["pink_dark"], big=True)
        self._sep(right, pady=4)

        # Payment
        pf = tk.Frame(right, bg=P["white"]); pf.pack(fill=tk.X, padx=12, pady=2)
        tk.Label(pf, text="Payment:", font=FONT_SB,
                 bg=P["white"], fg=P["text_soft"]).pack(side=tk.LEFT)
        self.pay_var = tk.StringVar(value="Cash")
        for pm in ["Cash","Card","Online","Split"]:
            tk.Radiobutton(pf, text=pm, variable=self.pay_var, value=pm,
                           bg=P["white"], font=FONT_S, fg=P["text_dark"],
                           selectcolor=P["pink_light"],
                           activebackground=P["white"]).pack(side=tk.LEFT, padx=3)

        # Customer phone
        cuf = tk.Frame(right, bg=P["white"]); cuf.pack(fill=tk.X, padx=12, pady=3)
        tk.Label(cuf, text="📱 Phone:", font=FONT_SB,
                 bg=P["white"], fg=P["text_soft"]).pack(side=tk.LEFT)
        self.cust_phone = tk.Entry(cuf, font=FONT_M, width=14, relief="flat", bd=0,
                                   bg=P["pink_pale"], fg=P["text_dark"])
        self.cust_phone.pack(side=tk.LEFT, padx=6, ipady=4)

        self._sep(right, pady=4)

        bf = tk.Frame(right, bg=P["white"]); bf.pack(fill=tk.X, padx=12, pady=6)
        tk.Button(bf, text="✔  Complete Sale",
                  bg=P["green"], fg="white", font=FONT_MB,
                  relief="flat", bd=0, cursor="hand2",
                  pady=12, activebackground="#3a9e6e",
                  activeforeground="white",
                  command=self._complete_sale).pack(fill=tk.X, pady=(0,6))
        tk.Button(bf, text="🗑  Clear Cart",
                  bg=P["pink_pale"], fg=P["text_soft"], font=FONT_MB,
                  relief="flat", bd=0, cursor="hand2",
                  pady=8, command=self._clear_cart).pack(fill=tk.X)

        self._refresh_cart()

    def _build_cat_tabs(self):
        for w in self._cat_frame.winfo_children(): w.destroy()
        cursor.execute("SELECT DISTINCT category FROM products WHERE is_active=1 ORDER BY category")
        cats = ["All"] + [r[0] for r in cursor.fetchall()]
        for cat in cats:
            active = (cat == self._pos_cat.get())
            btn = tk.Button(self._cat_frame,
                            text=cat,
                            font=FONT_SB if active else FONT_S,
                            bg=P["pink_deep"] if active else P["white"],
                            fg="white" if active else P["text_mid"],
                            relief="flat", bd=0, padx=12, pady=6,
                            cursor="hand2",
                            highlightthickness=1,
                            highlightbackground=P["pink_mid"] if active else P["border"],
                            command=lambda c=cat: self._sel_cat(c))
            btn.pack(side=tk.LEFT, padx=3)

    def _sel_cat(self, cat):
        self._pos_cat.set(cat)
        self._build_cat_tabs()
        self._pos_load()

    def _pos_load(self):
        for w in self._prod_frame.winfo_children(): w.destroy()
        q = self.pos_search.get().strip()
        if q == "Search bakery items...": q = ""
        cat = self._pos_cat.get()
        sql = """SELECT id,name,price,stock,category,image_path,
                        discount_pct,is_bestseller,is_new
                 FROM products WHERE is_active=1"""
        params = []
        if q: sql += " AND name LIKE ?"; params.append(f"%{q}%")
        if cat != "All": sql += " AND category=?"; params.append(cat)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        COLS = 4
        for i, row in enumerate(rows):
            self._make_card(i, *row, COLS)

    def _make_card(self, i, pid, name, price, stock, cat, imgp, disc, bs, new, COLS):
        col = i % COLS
        row_n = i // COLS
        card = tk.Frame(self._prod_frame, bg=P["white"],
                        highlightthickness=1, highlightbackground=P["border"],
                        cursor="hand2" if stock>0 else "")
        card.grid(row=row_n, column=col, padx=7, pady=7, sticky="nsew")
        self._prod_frame.columnconfigure(col, weight=1)

        # Image
        img_f = tk.Frame(card, bg=P["pink_pale"], height=115)
        img_f.pack(fill=tk.X)
        img_f.pack_propagate(False)
        img_lbl = tk.Label(img_f, bg=P["pink_pale"])
        img_lbl.pack(fill=tk.BOTH, expand=True)

        if PILLOW_INSTALLED:
            if imgp and os.path.exists(imgp):
                try:
                    im = Image.open(imgp).resize((155,115), Image.LANCZOS)
                    ph = ImageTk.PhotoImage(im)
                    img_lbl.config(image=ph); img_lbl.image = ph
                except:
                    im = make_product_image(cat, 155, 115)
                    ph = ImageTk.PhotoImage(im)
                    img_lbl.config(image=ph); img_lbl.image = ph
            else:
                im = make_product_image(cat, 155, 115)
                ph = ImageTk.PhotoImage(im)
                img_lbl.config(image=ph); img_lbl.image = ph

        # Badges
        badge_f = tk.Frame(img_f, bg=P["pink_pale"])
        badge_f.place(x=4, y=4)
        if bs:
            tk.Label(badge_f, text="★ Best",
                     font=("Helvetica",7,"bold"),
                     bg=P["badge_bs"], fg="white", padx=5, pady=2).pack(side=tk.LEFT, padx=1)
        if new:
            tk.Label(badge_f, text="New",
                     font=("Helvetica",7,"bold"),
                     bg=P["badge_new"], fg="white", padx=5, pady=2).pack(side=tk.LEFT, padx=1)
        if disc and disc > 0:
            tk.Label(badge_f, text=f"−{int(disc)}%",
                     font=("Helvetica",7,"bold"),
                     bg=P["badge_off"], fg="white", padx=5, pady=2).pack(side=tk.LEFT, padx=1)

        # Info
        info = tk.Frame(card, bg=P["white"], padx=8, pady=6)
        info.pack(fill=tk.X)
        tk.Label(info, text=name, font=("Helvetica",9,"bold"),
                 bg=P["white"], fg=P["text_dark"],
                 wraplength=130, justify="left").pack(anchor="w")

        price_f = tk.Frame(info, bg=P["white"]); price_f.pack(anchor="w", pady=2)
        if disc and disc > 0:
            tk.Label(price_f, text=f"Rs.{price:.0f}",
                     font=("Helvetica",8,"overstrike"),
                     bg=P["white"], fg=P["text_gray"]).pack(side=tk.LEFT)
            tk.Label(price_f, text=f" Rs.{price*(1-disc/100):.0f}",
                     font=("Helvetica",9,"bold"),
                     bg=P["white"], fg=P["pink_deep"]).pack(side=tk.LEFT)
        else:
            tk.Label(price_f, text=f"Rs.{price:.0f}",
                     font=("Helvetica",9,"bold"),
                     bg=P["white"], fg=P["text_dark"]).pack(side=tk.LEFT)

        stk_c = P["green"] if stock>5 else (P["gold"] if stock>0 else P["red"])
        tk.Label(info, text=f"Stock: {stock}" if stock>0 else "Out of Stock",
                 font=("Helvetica",7), bg=P["white"], fg=stk_c).pack(anchor="w")

        if stock > 0:
            add = tk.Button(info, text="+ Add to Cart",
                            bg=P["pink_deep"], fg="white",
                            font=("Helvetica",8,"bold"),
                            relief="flat", bd=0, cursor="hand2", pady=5,
                            activebackground=P["pink_dark"],
                            activeforeground="white",
                            command=lambda r=(pid,name,price,stock,cat,imgp): self._add_to_cart(r))
            add.pack(fill=tk.X, pady=(4,0))
        else:
            tk.Label(info, text="Unavailable", font=("Helvetica",8),
                     bg=P["red"], fg="white", pady=4).pack(fill=tk.X, pady=(4,0))

        # Click whole card
        def on_click(r=(pid,name,price,stock,cat,imgp)):
            if stock > 0: self._add_to_cart(r)
        for w in [card, img_f, img_lbl, info]:
            w.bind("<Button-1>", lambda e,f=on_click: f())
            w.bind("<Enter>", lambda e,c=card: c.config(highlightbackground=P["pink_mid"]))
            w.bind("<Leave>", lambda e,c=card: c.config(highlightbackground=P["border"]))

    def _add_to_cart(self, row):
        pid, name, price, stock, cat, imgp = row
        if stock <= 0:
            messagebox.showwarning("Out of Stock", f"'{name}' is out of stock!")
            return
        cursor.execute("SELECT discount_pct FROM products WHERE id=?", (pid,))
        r = cursor.fetchone()
        disc = r[0] if r else 0
        fp = price * (1 - disc/100) if disc else price
        for item in self.cart:
            if item["pid"] == pid:
                if item["qty"] >= stock:
                    messagebox.showwarning("Stock Limit","Cannot exceed available stock.")
                    return
                item["qty"] += 1
                self._refresh_cart(); return
        self.cart.append({"pid":pid,"name":name,"price":fp,"orig_price":price,"qty":1,"stock":stock})
        self._refresh_cart()

    def _edit_qty(self, event):
        sel = self.cart_tree.selection()
        if not sel: return
        idx = self.cart_tree.index(sel[0])
        item = self.cart[idx]
        win = tk.Toplevel(self.root); win.title("Edit Quantity")
        win.geometry("300x180"); win.configure(bg=P["white"]); win.grab_set()
        tk.Frame(win, bg=P["pink_deep"], height=4).pack(fill=tk.X)
        tk.Label(win, text=item['name'], font=FONT_L,
                 bg=P["white"], fg=P["text_dark"]).pack(pady=(14,2))
        tk.Label(win, text=f"Max available: {item['stock']}", font=FONT_S,
                 bg=P["white"], fg=P["text_soft"]).pack()
        qty_var = tk.IntVar(value=item["qty"])
        sf2 = tk.Frame(win, bg=P["white"]); sf2.pack(pady=10)
        tk.Button(sf2, text="−", font=FONT_MB, bg=P["pink_pale"],
                  fg=P["text_dark"], width=3, relief="flat", bd=0, cursor="hand2",
                  command=lambda: qty_var.set(max(0,qty_var.get()-1))).pack(side=tk.LEFT,padx=6)
        tk.Label(sf2, textvariable=qty_var, font=("Georgia",20,"bold"),
                 bg=P["white"], fg=P["pink_deep"], width=4).pack(side=tk.LEFT)
        tk.Button(sf2, text="+", font=FONT_MB, bg=P["pink_deep"],
                  fg="white", width=3, relief="flat", bd=0, cursor="hand2",
                  command=lambda: qty_var.set(min(item['stock'],qty_var.get()+1))).pack(side=tk.LEFT,padx=6)

        def apply():
            q = qty_var.get()
            if q == 0: self.cart.pop(idx)
            else: self.cart[idx]["qty"] = q
            self._refresh_cart(); win.destroy()

        tk.Button(win, text="Update", bg=P["pink_deep"], fg="white",
                  font=FONT_MB, relief="flat", bd=0, pady=8, cursor="hand2",
                  command=apply).pack(fill=tk.X, padx=40)

    def _tot_row(self, parent, lbl, color=None, big=False):
        f = tk.Frame(parent, bg=P["white"]); f.pack(fill=tk.X, padx=12, pady=2)
        font = ("Georgia",14,"bold") if big else FONT_M
        tk.Label(f, text=lbl, font=font, bg=P["white"],
                 fg=color or P["text_soft"]).pack(side=tk.LEFT)
        v = tk.Label(f, text="Rs. 0.00", font=font,
                     bg=P["white"], fg=color or P["text_dark"])
        v.pack(side=tk.RIGHT)
        return v

    def _refresh_cart(self):
        for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
        sub = 0
        for item in self.cart:
            t = item["price"]*item["qty"]; sub += t
            self.cart_tree.insert("","end",
                values=(item['name'][:18], item['qty'],
                        f"{item['price']:.0f}", f"{t:.0f}"))
        disc = 0
        if self.applied_coupon:
            c = self.applied_coupon
            disc = (sub*c["value"]/100) if c["type"]=="percent" else min(c["value"],sub)
        tax = (sub-disc)*TAX_RATE
        total = sub-disc+tax
        self._lbl_sub.config(text=f"Rs. {sub:.2f}")
        self._lbl_disc.config(text=f"-Rs. {disc:.2f}")
        self._lbl_tax.config(text=f"Rs. {tax:.2f}")
        self._lbl_total.config(text=f"Rs. {total:.2f}")

    def _apply_coupon(self):
        code = self.coupon_ent.get().strip().upper()
        cursor.execute("""SELECT * FROM coupons WHERE code=? AND is_active=1
                          AND (expiry_date IS NULL OR expiry_date>=date('now'))
                          AND used_count<max_uses""", (code,))
        row = cursor.fetchone()
        if not row:
            messagebox.showerror("Invalid","Coupon is invalid or expired."); return
        cols = [d[0] for d in cursor.description]
        self.applied_coupon = dict(zip(cols, row))
        messagebox.showinfo("Applied!",
            f"Coupon '{code}' applied — "
            f"{'%' if self.applied_coupon['type']=='percent' else 'Rs.'}"
            f"{self.applied_coupon['value']} off")
        self._refresh_cart()

    def _clear_cart(self):
        self.cart.clear(); self.applied_coupon = None
        self.coupon_ent.delete(0,tk.END)
        self._refresh_cart()

    def _get_totals(self):
        sub = sum(i["price"]*i["qty"] for i in self.cart)
        disc = 0
        if self.applied_coupon:
            c = self.applied_coupon
            disc = (sub*c["value"]/100) if c["type"]=="percent" else min(c["value"],sub)
        tax = (sub-disc)*TAX_RATE
        return sub, disc, tax, sub-disc+tax

    def _complete_sale(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart","Add items first."); return
        sub, disc, tax, total = self._get_totals()
        inv = self._next_inv()
        cursor.execute(
            "INSERT INTO sales (invoice_no,subtotal,discount,tax,total,payment_method,cashier) VALUES (?,?,?,?,?,?,?)",
            (inv,sub,disc,tax,total,self.pay_var.get(),self.current_user))
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
            pts = int(total//100)
            cursor.execute("""INSERT INTO customers (name,phone,loyalty_pts,total_spent)
                              VALUES (?,?,?,?) ON CONFLICT(phone) DO UPDATE SET
                              loyalty_pts=loyalty_pts+?, total_spent=total_spent+?""",
                           ("Customer",phone,pts,total,pts,total))
        conn.commit()
        receipt = self._build_receipt(inv,sub,disc,tax,total)
        self._show_receipt(receipt)
        self._pos_load(); self._build_cat_tabs(); self._clear_cart()

    def _next_inv(self):
        today = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM sales WHERE date(date)=?", (today,))
        n = cursor.fetchone()[0]+1
        return f"INV-{datetime.date.today().strftime('%Y%m%d')}-{n:04d}"

    def _next_ret_inv(self):
        today = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM returns WHERE date(date)=?", (today,))
        n = cursor.fetchone()[0]+1
        return f"RET-{datetime.date.today().strftime('%Y%m%d')}-{n:04d}"

    def _build_receipt(self, inv, sub, disc, tax, total):
        lines = ["═"*42,"         BAKES BY AYESHA",
                 "      Artisan Bakery & Sweets","═"*42,
                 f"Invoice : {inv}",
                 f"Date    : {datetime.datetime.now().strftime('%d-%b-%Y %H:%M')}",
                 f"Cashier : {self.current_user}",
                 f"Payment : {self.pay_var.get()}","─"*42]
        for item in self.cart:
            lines.append(f"  {item['name'][:24]:<24} x{item['qty']}")
            lines.append(f"  Rs.{item['price']:.0f} x {item['qty']} = Rs.{item['price']*item['qty']:.0f}")
        lines += ["─"*42,
            f"  Subtotal   : Rs. {sub:.2f}",
            f"  Discount   : -Rs. {disc:.2f}",
            f"  Tax (5%)   : Rs. {tax:.2f}","═"*42,
            f"  TOTAL      : Rs. {total:.2f}","═"*42,
            "    Thank you! 🌸 Visit Again 🎂",
            "    www.bakesbyayesha.com","═"*42]
        return "\n".join(lines)

    def _show_receipt(self, text, title="Receipt 🧾"):
        win = tk.Toplevel(self.root)
        win.title(title); win.geometry("460x580")
        win.configure(bg=P["white"]); win.grab_set()
        tk.Frame(win, bg=P["pink_deep"], height=4).pack(fill=tk.X)
        tk.Label(win, text=title, font=("Georgia",16,"bold"),
                 bg=P["pink_pale"], fg=P["text_dark"], pady=12).pack(fill=tk.X)
        txt = tk.Text(win, font=("Courier New",10), bg=P["cream"],
                      fg=P["text_dark"], relief="flat", bd=0, padx=16, pady=14)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", text); txt.config(state="disabled")
        bf = tk.Frame(win, bg=P["white"], pady=10); bf.pack(fill=tk.X, padx=14)
        def save():
            path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text","*.txt")])
            if path:
                with open(path,"w") as f: f.write(text)
                messagebox.showinfo("Saved","Receipt saved!")
        self._pill(bf,"💾 Save",P["pink_deep"],"white",save,padx=16,pady=8).pack(side=tk.LEFT,padx=4)
        self._pill(bf,"✖ Close",P["pink_pale"],P["text_soft"],win.destroy,padx=16,pady=8).pack(side=tk.LEFT)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB: INVENTORY
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_inventory(self, parent):
        top = tk.Frame(parent, bg=P["snow"], pady=10)
        top.pack(fill=tk.X, padx=14)
        btns = [("+ Add Product",P["pink_deep"],"white",self._add_product_win),
                ("✏ Edit",P["blue"],"white",self._edit_product),
                ("🗑 Delete",P["red"],"white",self._del_product),
                ("📈 +10% Prices",P["gold"],P["text_dark"],self._bulk_up),
                ("📉 −10% Prices",P["pink_pale"],P["text_soft"],self._bulk_dn),
                ("📤 Export CSV",P["green"],"white",self._export_inv)]
        for txt,bg,fg,cmd in btns:
            self._pill(top,txt,bg,fg,cmd,padx=12,pady=7,font=FONT_SB).pack(side=tk.LEFT,padx=3)

        sf = tk.Frame(parent, bg=P["snow"]); sf.pack(fill=tk.X, padx=14, pady=(0,6))
        tk.Label(sf,"Search:", font=FONT_SB, bg=P["snow"], fg=P["text_soft"]).pack(side=tk.LEFT)
        self.inv_search = tk.Entry(sf, font=FONT_M, width=32, relief="flat", bd=0,
                                   bg=P["white"], fg=P["text_dark"],
                                   highlightthickness=1, highlightbackground=P["border"])
        self.inv_search.pack(side=tk.LEFT, padx=8, ipady=7)
        self.inv_search.bind("<KeyRelease>", lambda e: self._load_inv())

        tree_f = tk.Frame(parent, bg=P["snow"])
        tree_f.pack(fill=tk.BOTH, expand=True, padx=14)
        cols = ("ID","Price","Cost","Stock","Disc%","Category","Status","Best Seller")
        self.inv_tree = ttk.Treeview(tree_f, columns=cols, show=("tree","headings"))
        self.inv_tree.heading("#0", text="Product Name")
        self.inv_tree.column("#0", width=200)
        for c,w in zip(cols,[40,80,70,60,60,120,70,80]):
            self.inv_tree.heading(c, text=c)
            self.inv_tree.column(c, width=w, anchor="center")
        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.inv_tree.pack(fill=tk.BOTH, expand=True)
        self.inv_tree.bind("<<TreeviewSelect>>", self._inv_preview)

        self.low_lbl = tk.Label(parent, text="", font=FONT_SB,
                                bg=P["snow"], fg=P["red"])
        self.low_lbl.pack(pady=3, anchor="w", padx=14)
        self.inv_img_lbl = tk.Label(parent, bg=P["snow"], text="Select a product",
                                    font=FONT_S, fg=P["text_gray"])
        self.inv_img_lbl.pack(pady=4)
        self._load_inv()

    def _load_inv(self):
        for i in self.inv_tree.get_children(): self.inv_tree.delete(i)
        q = self.inv_search.get().strip() if hasattr(self,"inv_search") else ""
        sql = """SELECT id,name,price,cost_price,stock,discount_pct,
                        category,is_active,is_bestseller FROM products"""
        params = []
        if q: sql += " WHERE name LIKE ?"; params.append(f"%{q}%")
        cursor.execute(sql, params)
        low = []
        for row in cursor.fetchall():
            pid,name,price,cost,stock,disc,cat,active,bs = row
            tag = "low" if 0<stock<=5 else ("out" if stock<=0 else "")
            self.inv_tree.insert("","end", text=name, iid=str(pid),
                values=(pid,f"{price:.2f}",f"{cost:.2f}",stock,
                        f"{disc:.0f}%",cat,
                        "Active" if active else "Inactive",
                        "★" if bs else ""),
                tags=(tag,))
            if stock<=5: low.append(name)
        self.inv_tree.tag_configure("low", foreground=P["gold"])
        self.inv_tree.tag_configure("out", foreground=P["red"])
        if hasattr(self,"low_lbl"):
            self.low_lbl.config(
                text=("⚠  Low/Out: "+", ".join(low)) if low else "✔  All stock OK",
                fg=P["red"] if low else P["green"])

    def _inv_preview(self, event):
        sel = self.inv_tree.selection()
        if not sel: return
        pid = int(sel[0])
        cursor.execute("SELECT image_path,category FROM products WHERE id=?", (pid,))
        row = cursor.fetchone()
        if not row: return
        imgp, cat = row
        if PILLOW_INSTALLED:
            if imgp and os.path.exists(imgp):
                try:
                    im = Image.open(imgp).resize((160,110),Image.LANCZOS)
                    ph = ImageTk.PhotoImage(im)
                    self.inv_img_lbl.config(image=ph,text=""); self.inv_img_lbl.image=ph; return
                except: pass
            im = make_product_image(cat, 160, 110)
            ph = ImageTk.PhotoImage(im)
            self.inv_img_lbl.config(image=ph,text=""); self.inv_img_lbl.image=ph

    def _add_product_win(self, pid=None):
        data = None
        if pid:
            cursor.execute("""SELECT id,name,price,stock,category,image_path,
                                     description,cost_price,barcode,discount_pct,
                                     is_bestseller,is_new FROM products WHERE id=?""", (pid,))
            data = cursor.fetchone()

        win = tk.Toplevel(self.root)
        win.title("Edit Product" if pid else "New Product")
        win.geometry("460x740"); win.configure(bg=P["white"]); win.grab_set()
        tk.Frame(win, bg=P["pink_deep"], height=4).pack(fill=tk.X)
        tk.Label(win, text="✏ Edit Product" if pid else "＋ New Product",
                 font=("Georgia",16,"bold"),
                 bg=P["pink_pale"], fg=P["text_dark"], pady=14).pack(fill=tk.X)

        sc = tk.Canvas(win, bg=P["white"], highlightthickness=0)
        sc.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(sc, bg=P["white"])
        sc.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: sc.configure(scrollregion=sc.bbox("all")))

        self._temp_img = ""
        cur_img = data[5] if data else ""

        for lbl, attr in [("Product Name","_pn"),("Unit Price (Rs.)","_pp"),
                           ("Cost Price (Rs.)","_pc"),("Stock Qty","_ps"),
                           ("Category","_pcat"),("Barcode","_pbar"),
                           ("Discount %","_pdisc"),("Description","_pdesc")]:
            tk.Label(inner, text=lbl, font=FONT_SB, bg=P["white"],
                     fg=P["text_mid"]).pack(fill=tk.X, padx=22, pady=(8,1))
            e = tk.Entry(inner, font=FONT_M, relief="flat", bd=0,
                         bg=P["pink_pale"], fg=P["text_dark"],
                         highlightthickness=1, highlightbackground=P["border"])
            e.pack(fill=tk.X, padx=22, ipady=8)
            setattr(self, attr, e)

        if data:
            _,nm,pr,st,cat,imgp,desc,cp,bc,disc,bs,new = data
            for attr, val in [("_pn",nm),("_pp",pr),("_pc",cp),("_ps",st),
                               ("_pcat",cat),("_pbar",bc or ""),
                               ("_pdisc",disc or 0),("_pdesc",desc or "")]:
                getattr(self,attr).insert(0, val or "")

        chk_f = tk.Frame(inner, bg=P["white"]); chk_f.pack(fill=tk.X, padx=22, pady=8)
        self._pbs = tk.IntVar(value=(data[10] if data else 0))
        self._pnew = tk.IntVar(value=(data[11] if data else 0))
        tk.Checkbutton(chk_f, text="★ Best Seller", variable=self._pbs,
                       bg=P["white"], font=FONT_M, fg=P["gold"],
                       selectcolor=P["pink_pale"]).pack(side=tk.LEFT, padx=8)
        tk.Checkbutton(chk_f, text="✦ New", variable=self._pnew,
                       bg=P["white"], font=FONT_M, fg=P["green"],
                       selectcolor=P["pink_pale"]).pack(side=tk.LEFT)

        def browse():
            p = filedialog.askopenfilename(filetypes=[("Images","*.jpg *.png *.jpeg *.webp")])
            if p:
                dest = os.path.join(IMG_DIR, os.path.basename(p))
                shutil.copy2(p, dest); self._temp_img = dest
                messagebox.showinfo("Image Set","Product image updated.")

        self._pill(inner,"📷 Browse Image",P["pink_pale"],P["text_dark"],
                   browse,padx=16,pady=7).pack(padx=22,pady=6,anchor="w")

        def save():
            try:
                nm = self._pn.get().strip()
                if not nm:
                    messagebox.showerror("Validation","Product name required."); return
                pr   = float(self._pp.get())
                cp   = float(self._pc.get() or 0)
                st   = int(self._ps.get())
                cat  = self._pcat.get().strip() or "General"
                bar  = self._pbar.get().strip() or None
                disc = float(self._pdisc.get() or 0)
                desc = self._pdesc.get().strip()
                imgp = self._temp_img or cur_img
                bs   = self._pbs.get(); new = self._pnew.get()
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
                conn.commit(); self._load_inv(); win.destroy()
                messagebox.showinfo("Saved","Product saved successfully.")
            except ValueError as ex:
                messagebox.showerror("Input Error",f"Check numeric fields: {ex}")
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate","Name or barcode already exists.")

        self._pill(inner,"💾 Save Product",P["pink_deep"],"white",
                   save,padx=20,pady=10).pack(padx=22,pady=16)

    def _edit_product(self):
        sel = self.inv_tree.selection()
        if not sel:
            messagebox.showwarning("Select","Select a product first."); return
        self._add_product_win(pid=int(sel[0]))

    def _del_product(self):
        sel = self.inv_tree.selection()
        if not sel: return
        pid = int(sel[0]); name = self.inv_tree.item(sel[0])["text"]
        if messagebox.askyesno("Confirm Delete",f"Delete '{name}'?"):
            cursor.execute("DELETE FROM products WHERE id=?", (pid,))
            conn.commit(); self._load_inv()

    def _bulk_up(self):
        if messagebox.askyesno("Confirm","Increase ALL prices by 10%?"):
            cursor.execute("UPDATE products SET price=ROUND(price*1.10,2)")
            conn.commit(); self._load_inv()

    def _bulk_dn(self):
        if messagebox.askyesno("Confirm","Decrease ALL prices by 10%?"):
            cursor.execute("UPDATE products SET price=ROUND(price*0.90,2)")
            conn.commit(); self._load_inv()

    def _export_inv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV","*.csv")])
        if not path: return
        cursor.execute("SELECT name,price,cost_price,stock,category,barcode,discount_pct FROM products")
        with open(path,"w",newline="",encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Name","Price","Cost","Stock","Category","Barcode","Discount%"])
            w.writerows(cursor.fetchall())
        messagebox.showinfo("Exported",f"Saved to {path}")

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB: COUPONS
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_coupons(self, parent):
        hdr = tk.Frame(parent, bg=P["snow"], pady=10)
        hdr.pack(fill=tk.X, padx=14)
        tk.Label(hdr, text="🏷️  Coupon Management", font=FONT_H,
                 bg=P["snow"], fg=P["text_dark"]).pack(side=tk.LEFT)
        self._pill(hdr,"+ New Coupon",P["pink_deep"],"white",
                   self._new_coupon,padx=14,pady=7).pack(side=tk.RIGHT,padx=4)
        self._pill(hdr,"🗑 Delete",P["red"],"white",
                   self._del_coupon,padx=14,pady=7).pack(side=tk.RIGHT,padx=4)

        cols = ("Code","Type","Value","Min Purchase","Max Uses","Used","Expiry","Active")
        self.coup_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols:
            self.coup_tree.heading(c, text=c)
            self.coup_tree.column(c, width=110, anchor="center")
        self.coup_tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)
        self._load_coupons()

    def _load_coupons(self):
        for i in self.coup_tree.get_children(): self.coup_tree.delete(i)
        cursor.execute("SELECT id,code,type,value,min_purchase,max_uses,used_count,expiry_date,is_active FROM coupons")
        for row in cursor.fetchall():
            self.coup_tree.insert("","end", iid=str(row[0]),
                values=(row[1],row[2],row[3],row[4],row[5],row[6],
                        row[7] or "Never","Yes" if row[8] else "No"))

    def _new_coupon(self):
        win = tk.Toplevel(self.root); win.title("New Coupon")
        win.geometry("380x460"); win.configure(bg=P["white"]); win.grab_set()
        tk.Frame(win, bg=P["pink_deep"], height=4).pack(fill=tk.X)
        tk.Label(win, text="Create Coupon", font=("Georgia",16,"bold"),
                 bg=P["pink_pale"], fg=P["text_dark"], pady=14).pack(fill=tk.X)
        for lbl, attr in [("Code (e.g. SAVE20)","_cc"),
                           ("Value (% or Rs.)","_cv"),
                           ("Min Purchase (Rs.)","_cmin"),
                           ("Max Uses","_cmax"),
                           ("Expiry (YYYY-MM-DD or blank)","_cexp")]:
            self._label_field(win, lbl, attr)
        tk.Label(win, text="Type:", font=FONT_SB,
                 bg=P["white"], fg=P["text_mid"]).pack(fill=tk.X, padx=22, pady=(8,1))
        self._ct = tk.StringVar(value="percent")
        tf = tk.Frame(win, bg=P["white"]); tf.pack(fill=tk.X, padx=22)
        for t in ["percent","flat"]:
            tk.Radiobutton(tf, text=t.title(), variable=self._ct, value=t,
                           bg=P["white"], font=FONT_M,
                           selectcolor=P["pink_pale"]).pack(side=tk.LEFT, padx=10)
        def save():
            try:
                cursor.execute("""INSERT INTO coupons (code,type,value,min_purchase,max_uses,expiry_date)
                                  VALUES (?,?,?,?,?,?)""",
                               (self._cc.get().upper(), self._ct.get(),
                                float(self._cv.get()), float(self._cmin.get() or 0),
                                int(self._cmax.get() or 999),
                                self._cexp.get().strip() or None))
                conn.commit(); self._load_coupons(); win.destroy()
                messagebox.showinfo("Saved","Coupon created!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error","Code already exists.")
            except ValueError:
                messagebox.showerror("Error","Invalid numeric values.")
        self._pill(win,"💾 Save Coupon",P["pink_deep"],"white",save,padx=20,pady=10).pack(pady=14)

    def _del_coupon(self):
        sel = self.coup_tree.selection()
        if not sel: return
        cursor.execute("DELETE FROM coupons WHERE id=?", (int(sel[0]),))
        conn.commit(); self._load_coupons()

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB: REPORTS
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_reports(self, parent):
        hdr = tk.Frame(parent, bg=P["snow"], pady=10)
        hdr.pack(fill=tk.X, padx=14)
        tk.Label(hdr, text="📊  Sales Reports", font=FONT_H,
                 bg=P["snow"], fg=P["text_dark"]).pack(side=tk.LEFT)

        df = tk.Frame(parent, bg=P["pink_pale"], pady=10)
        df.pack(fill=tk.X, padx=14, pady=(0,8))
        for lbl, attr, default in [
            ("From:", "r_from", datetime.date.today().strftime("%Y-%m-01")),
            ("To:",   "r_to",   datetime.date.today().strftime("%Y-%m-%d"))]:
            tk.Label(df, text=lbl, font=FONT_SB,
                     bg=P["pink_pale"], fg=P["text_mid"]).pack(side=tk.LEFT, padx=8)
            e = tk.Entry(df, font=FONT_M, width=13, relief="flat", bd=0,
                         bg=P["white"], fg=P["text_dark"])
            e.insert(0, default)
            e.pack(side=tk.LEFT, padx=4, ipady=6)
            setattr(self, attr, e)
        self._pill(df,"🔍 Load",P["pink_deep"],"white",self._load_report,padx=14,pady=6).pack(side=tk.LEFT,padx=8)
        self._pill(df,"📤 Export",P["blue"],"white",self._export_report,padx=14,pady=6).pack(side=tk.LEFT,padx=4)

        self._rep_cards_f = tk.Frame(parent, bg=P["snow"])
        self._rep_cards_f.pack(fill=tk.X, padx=14, pady=4)

        cols = ("Invoice","Date","Subtotal","Discount","Tax","Total","Payment","Cashier")
        self.rep_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols:
            self.rep_tree.heading(c, text=c)
            self.rep_tree.column(c, width=110, anchor="center")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.rep_tree.yview)
        self.rep_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,14))
        self.rep_tree.pack(fill=tk.BOTH, expand=True, padx=14)
        self._load_report()

    def _load_report(self):
        for i in self.rep_tree.get_children(): self.rep_tree.delete(i)
        for w in self._rep_cards_f.winfo_children(): w.destroy()
        f, t = self.r_from.get().strip(), self.r_to.get().strip()
        cursor.execute("""SELECT invoice_no,date,subtotal,discount,tax,total,
                                 payment_method,cashier,is_return
                          FROM sales WHERE date(date) BETWEEN ? AND ? ORDER BY date DESC""", (f,t))
        rows = cursor.fetchall()
        rev = disc = tax = cnt = 0
        for row in rows:
            self.rep_tree.insert("","end", values=row[:-1])
            if not row[8]: rev+=row[5]; disc+=row[3]; tax+=row[4]; cnt+=1

        for lbl,val,col in [("🧾 Orders",str(cnt),P["pink_deep"]),
                              ("💰 Revenue",f"Rs. {rev:,.0f}",P["green"]),
                              ("🏷️ Discounts",f"Rs. {disc:,.0f}",P["gold"]),
                              ("🧾 Tax",f"Rs. {tax:,.0f}",P["blue"])]:
            c = tk.Frame(self._rep_cards_f, bg=col, padx=20, pady=14)
            c.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            tk.Label(c, text=val, font=("Helvetica",18,"bold"),
                     bg=col, fg="white").pack()
            tk.Label(c, text=lbl, font=FONT_S, bg=col, fg="white").pack()

    def _export_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV","*.csv")])
        if not path: return
        cursor.execute("""SELECT invoice_no,date,subtotal,discount,tax,total,
                                 payment_method,cashier FROM sales
                          WHERE date(date) BETWEEN ? AND ?""",
                       (self.r_from.get(), self.r_to.get()))
        with open(path,"w",newline="",encoding="utf-8") as fl:
            w = csv.writer(fl)
            w.writerow(["Invoice","Date","Subtotal","Discount","Tax","Total","Payment","Cashier"])
            w.writerows(cursor.fetchall())
        messagebox.showinfo("Exported",f"Saved to {path}")

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB: RETURNS
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_returns(self, parent):
        tk.Label(parent, text="↩  Returns & Refunds", font=FONT_H,
                 bg=P["snow"], fg=P["text_dark"]).pack(pady=(10,6), padx=14, anchor="w")

        lf = tk.LabelFrame(parent, text=" 1. Look Up Invoice ", font=FONT_MB,
                           bg=P["snow"], fg=P["blue"], padx=14, pady=10)
        lf.pack(fill=tk.X, padx=14, pady=(0,6))
        r1 = tk.Frame(lf, bg=P["snow"]); r1.pack(fill=tk.X)
        tk.Label(r1, text="Invoice No:", font=FONT_M, bg=P["snow"]).pack(side=tk.LEFT)
        self.ret_inv_ent = tk.Entry(r1, font=FONT_M, width=22, relief="flat", bd=0,
                                    bg=P["white"], fg=P["text_dark"],
                                    highlightthickness=1, highlightbackground=P["border"])
        self.ret_inv_ent.pack(side=tk.LEFT, padx=8, ipady=6)
        self._pill(r1,"🔍 Fetch",P["blue"],"white",self._ret_fetch,padx=14,pady=6).pack(side=tk.LEFT)
        self.ret_info_lbl = tk.Label(lf, text="", font=FONT_S,
                                     bg=P["snow"], fg=P["text_soft"])
        self.ret_info_lbl.pack(anchor="w", pady=(6,0))

        if2 = tk.LabelFrame(parent, text=" 2. Select Items ", font=FONT_MB,
                            bg=P["snow"], fg=P["blue"], padx=14, pady=8)
        if2.pack(fill=tk.X, padx=14, pady=(0,6))
        item_cols = ("✓","Product","Sold Qty","Return Qty","Unit Price","Refund")
        self.ret_items_tree = ttk.Treeview(if2, columns=item_cols, show="headings", height=5)
        for c,w in zip(item_cols,[30,200,80,90,90,90]):
            self.ret_items_tree.heading(c,text=c)
            self.ret_items_tree.column(c,width=w,anchor="center")
        self.ret_items_tree.pack(fill=tk.X)
        qf = tk.Frame(if2, bg=P["snow"]); qf.pack(fill=tk.X, pady=(6,0))
        tk.Label(qf, text="Return Qty:", font=FONT_S, bg=P["snow"]).pack(side=tk.LEFT)
        self.ret_qty_var = tk.IntVar(value=1)
        tk.Spinbox(qf, textvariable=self.ret_qty_var, from_=1, to=999,
                   font=FONT_M, width=5, relief="flat").pack(side=tk.LEFT, padx=6)
        self._pill(qf,"Set Qty",P["blue"],"white",self._ret_set_qty,padx=10,pady=4,font=FONT_S).pack(side=tk.LEFT)
        self._pill(qf,"Select All",P["pink_pale"],P["text_soft"],self._ret_all,padx=10,pady=4,font=FONT_S).pack(side=tk.LEFT,padx=6)

        rf3 = tk.LabelFrame(parent, text=" 3. Confirm Refund ", font=FONT_MB,
                            bg=P["snow"], fg=P["blue"], padx=14, pady=10)
        rf3.pack(fill=tk.X, padx=14, pady=(0,6))
        rf3a = tk.Frame(rf3, bg=P["snow"]); rf3a.pack(fill=tk.X)
        tk.Label(rf3a, text="Reason:", font=FONT_M, bg=P["snow"]).pack(side=tk.LEFT)
        self.ret_reason = tk.StringVar(value="Customer Request")
        ttk.Combobox(rf3a, textvariable=self.ret_reason,
                     values=["Customer Request","Defective Product","Wrong Item","Quality Issue","Other"],
                     state="readonly", width=22, font=FONT_M).pack(side=tk.LEFT, padx=8)
        self.ret_refund_lbl = tk.Label(rf3, text="Refund Total: Rs. 0.00",
                                       font=("Georgia",14,"bold"),
                                       bg=P["snow"], fg=P["blue"])
        self.ret_refund_lbl.pack(pady=6)
        self._pill(rf3,"✔  Process Refund",P["blue"],"white",
                   self._ret_process,padx=20,pady=10).pack(pady=4)

        # History
        self._sep(parent)
        tk.Label(parent, text="Return History", font=FONT_MB,
                 bg=P["snow"], fg=P["text_soft"]).pack(anchor="w", padx=14)
        hist_cols = ("Return Inv","Original Inv","Refund","Reason","Cashier","Date")
        self.ret_hist_tree = ttk.Treeview(parent, columns=hist_cols, show="headings", height=5)
        for c in hist_cols:
            self.ret_hist_tree.heading(c,text=c)
            self.ret_hist_tree.column(c,width=120,anchor="center")
        rhs = ttk.Scrollbar(parent, orient="vertical", command=self.ret_hist_tree.yview)
        self.ret_hist_tree.configure(yscrollcommand=rhs.set)
        rhs.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,14))
        self.ret_hist_tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)
        self._ret_sale_id = None; self._ret_sale_data = []
        self._ret_load_hist()

    def _ret_fetch(self):
        inv = self.ret_inv_ent.get().strip().upper()
        if not inv: messagebox.showwarning("Input","Enter invoice number."); return
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
            fg=P["green"])
        cursor.execute("""SELECT si.id,si.product_id,si.product_name,si.quantity,si.unit_price
                          FROM sale_items si WHERE si.sale_id=?""", (sid,))
        for i in self.ret_items_tree.get_children(): self.ret_items_tree.delete(i)
        self._ret_sale_data = []
        for r in cursor.fetchall():
            item_id, pid, pname, qty, uprice = r
            self._ret_sale_data.append({"item_id":item_id,"pid":pid,"name":pname,
                                         "sold_qty":qty,"ret_qty":qty,"unit_price":uprice})
            self.ret_items_tree.insert("","end", iid=str(item_id),
                values=("✓",pname,qty,qty,f"{uprice:.2f}",f"{qty*uprice:.2f}"))
        self._ret_upd_total()

    def _ret_set_qty(self):
        sel = self.ret_items_tree.selection()
        if not sel: messagebox.showwarning("Select","Select an item."); return
        iid = int(sel[0])
        item = next((x for x in self._ret_sale_data if x["item_id"]==iid), None)
        if not item: return
        q = self.ret_qty_var.get()
        if q < 0 or q > item["sold_qty"]:
            messagebox.showerror("Invalid",f"Qty must be 0–{item['sold_qty']}."); return
        item["ret_qty"] = q
        self.ret_items_tree.item(str(iid), values=(
            "✓" if q>0 else "✗", item["name"], item["sold_qty"], q,
            f"{item['unit_price']:.2f}", f"{q*item['unit_price']:.2f}"))
        self._ret_upd_total()

    def _ret_all(self):
        for item in self._ret_sale_data:
            item["ret_qty"] = item["sold_qty"]
            self.ret_items_tree.item(str(item["item_id"]), values=(
                "✓",item["name"],item["sold_qty"],item["sold_qty"],
                f"{item['unit_price']:.2f}",
                f"{item['sold_qty']*item['unit_price']:.2f}"))
        self._ret_upd_total()

    def _ret_upd_total(self):
        total = sum(x["ret_qty"]*x["unit_price"] for x in self._ret_sale_data)
        self.ret_refund_lbl.config(text=f"Refund Total: Rs. {total:.2f}")

    def _ret_process(self):
        if not self._ret_sale_id:
            messagebox.showwarning("No Invoice","Fetch an invoice first."); return
        items = [x for x in self._ret_sale_data if x["ret_qty"]>0]
        if not items:
            messagebox.showwarning("Nothing","Set return qty > 0."); return
        refund = sum(x["ret_qty"]*x["unit_price"] for x in items)
        reason = self.ret_reason.get()
        orig = self.ret_inv_ent.get().strip().upper()
        ret_inv = self._next_ret_inv()
        if not messagebox.askyesno("Confirm",
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
            cursor.execute("UPDATE products SET stock=stock+? WHERE id=?",(item["ret_qty"],item["pid"]))
        conn.commit()
        receipt = [f"REFUND RECEIPT — {ret_inv}",
                   f"Original: {orig}", f"Refund: Rs. {refund:.2f}", f"Reason: {reason}"]
        self._show_receipt("\n".join(receipt), "Refund Receipt")
        self._ret_sale_id = None; self._ret_sale_data = []
        self.ret_inv_ent.delete(0,tk.END)
        self.ret_info_lbl.config(text="")
        for i in self.ret_items_tree.get_children(): self.ret_items_tree.delete(i)
        self.ret_refund_lbl.config(text="Refund Total: Rs. 0.00")
        self._ret_load_hist()

    def _ret_load_hist(self):
        for i in self.ret_hist_tree.get_children(): self.ret_hist_tree.delete(i)
        cursor.execute("SELECT return_invoice,original_invoice,refund_amount,reason,cashier,date FROM returns ORDER BY date DESC")
        for row in cursor.fetchall():
            self.ret_hist_tree.insert("","end",
                values=(row[0],row[1],f"Rs. {row[2]:.2f}",row[3],row[4],row[5]))

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB: CUSTOMERS
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_customers(self, parent):
        hdr = tk.Frame(parent, bg=P["snow"], pady=10)
        hdr.pack(fill=tk.X, padx=14)
        tk.Label(hdr, text="👥  Customer Loyalty", font=FONT_H,
                 bg=P["snow"], fg=P["text_dark"]).pack(side=tk.LEFT)
        self._pill(hdr,"+ Add Customer",P["pink_deep"],"white",
                   self._add_customer,padx=14,pady=7).pack(side=tk.RIGHT)

        cols = ("ID","Name","Phone","Email","Loyalty Pts","Total Spent","Since")
        self.cust_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols:
            self.cust_tree.heading(c,text=c)
            self.cust_tree.column(c,width=130,anchor="center")
        self.cust_tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)
        self._load_customers()

    def _load_customers(self):
        for i in self.cust_tree.get_children(): self.cust_tree.delete(i)
        cursor.execute("SELECT id,name,phone,email,loyalty_pts,total_spent,created_at FROM customers")
        for row in cursor.fetchall():
            self.cust_tree.insert("","end", values=row)

    def _add_customer(self):
        win = tk.Toplevel(self.root); win.title("Add Customer")
        win.geometry("360x340"); win.configure(bg=P["white"]); win.grab_set()
        tk.Frame(win, bg=P["pink_deep"], height=4).pack(fill=tk.X)
        tk.Label(win, text="New Customer", font=("Georgia",16,"bold"),
                 bg=P["pink_pale"], fg=P["text_dark"], pady=14).pack(fill=tk.X)
        for lbl, attr in [("Name","_cname"),("Phone","_cphone"),("Email","_cemail")]:
            self._label_field(win, lbl, attr)
        def save():
            try:
                cursor.execute("INSERT INTO customers (name,phone,email) VALUES (?,?,?)",
                               (self._cname.get(),self._cphone.get(),self._cemail.get()))
                conn.commit(); self._load_customers(); win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error","Phone already exists.")
        self._pill(win,"💾 Save",P["pink_deep"],"white",save,padx=20,pady=10).pack(pady=14)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB: EXPENSES
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_expenses(self, parent):
        hdr = tk.Frame(parent, bg=P["snow"], pady=10)
        hdr.pack(fill=tk.X, padx=14)
        tk.Label(hdr, text="💸  Expense Tracker", font=FONT_H,
                 bg=P["snow"], fg=P["text_dark"]).pack(side=tk.LEFT)
        self._pill(hdr,"+ Add Expense",P["pink_deep"],"white",
                   self._add_expense,padx=14,pady=7).pack(side=tk.RIGHT)

        cols = ("ID","Category","Amount","Description","Date")
        self.exp_tree = ttk.Treeview(parent, columns=cols, show="headings")
        for c in cols:
            self.exp_tree.heading(c,text=c)
            self.exp_tree.column(c,width=170,anchor="center")
        self.exp_tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)
        self._load_expenses()

    def _load_expenses(self):
        for i in self.exp_tree.get_children(): self.exp_tree.delete(i)
        cursor.execute("SELECT id,category,amount,description,date FROM expenses ORDER BY date DESC")
        for row in cursor.fetchall():
            self.exp_tree.insert("","end", values=row)

    def _add_expense(self):
        win = tk.Toplevel(self.root); win.title("Add Expense")
        win.geometry("360x320"); win.configure(bg=P["white"]); win.grab_set()
        tk.Frame(win, bg=P["pink_deep"], height=4).pack(fill=tk.X)
        tk.Label(win, text="Add Expense", font=("Georgia",16,"bold"),
                 bg=P["pink_pale"], fg=P["text_dark"], pady=14).pack(fill=tk.X)
        for lbl, attr in [("Category","_ecat"),("Amount (Rs.)","_eamt"),("Description","_edesc")]:
            self._label_field(win, lbl, attr)
        def save():
            try:
                cursor.execute("INSERT INTO expenses (category,amount,description) VALUES (?,?,?)",
                               (self._ecat.get(),float(self._eamt.get()),self._edesc.get()))
                conn.commit(); self._load_expenses(); win.destroy()
            except ValueError:
                messagebox.showerror("Error","Invalid amount.")
        self._pill(win,"💾 Save",P["pink_deep"],"white",save,padx=20,pady=10).pack(pady=14)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB: SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_settings(self, parent):
        tk.Label(parent, text="⚙️  System Settings", font=FONT_H,
                 bg=P["snow"], fg=P["text_dark"]).pack(pady=(10,6), padx=14, anchor="w")

        scroll_c = tk.Canvas(parent, bg=P["snow"], highlightthickness=0)
        scroll_c.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(scroll_c, bg=P["snow"])
        scroll_c.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: scroll_c.configure(scrollregion=scroll_c.bbox("all")))

        # Users
        uf = tk.LabelFrame(inner, text=" User Management ", font=FONT_MB,
                           bg=P["snow"], fg=P["text_dark"], padx=16, pady=10)
        uf.pack(fill=tk.X, padx=16, pady=6)
        cols = ("Username","Role","Active")
        self.usr_tree = ttk.Treeview(uf, columns=cols, show="headings", height=5)
        for c in cols:
            self.usr_tree.heading(c,text=c)
            self.usr_tree.column(c,width=140,anchor="center")
        self.usr_tree.pack(fill=tk.X)
        bf2 = tk.Frame(uf, bg=P["snow"]); bf2.pack(pady=6)
        self._pill(bf2,"+ Add User",P["pink_deep"],"white",self._add_user,padx=14,pady=6).pack(side=tk.LEFT,padx=4)
        self._pill(bf2,"🗑 Remove",P["red"],"white",self._del_user,padx=14,pady=6).pack(side=tk.LEFT,padx=4)
        self._load_users()

        # Tax
        tf2 = tk.LabelFrame(inner, text=" Tax Rate ", font=FONT_MB,
                            bg=P["snow"], fg=P["text_dark"], padx=16, pady=10)
        tf2.pack(fill=tk.X, padx=16, pady=6)
        trf = tk.Frame(tf2, bg=P["snow"]); trf.pack()
        tk.Label(trf, text="Tax %:", font=FONT_M, bg=P["snow"]).pack(side=tk.LEFT)
        self.tax_ent = tk.Entry(trf, font=FONT_M, width=8, relief="flat", bd=0,
                                bg=P["white"], fg=P["text_dark"])
        self.tax_ent.insert(0, str(int(TAX_RATE*100)))
        self.tax_ent.pack(side=tk.LEFT, padx=8, ipady=5)
        def save_tax():
            global TAX_RATE
            try:
                TAX_RATE = float(self.tax_ent.get())/100
                messagebox.showinfo("Saved",f"Tax rate set to {TAX_RATE*100:.1f}%")
            except:
                messagebox.showerror("Error","Invalid value.")
        self._pill(tf2,"Save Tax Rate",P["pink_deep"],"white",save_tax,padx=14,pady=6).pack(pady=6)

        # Backup
        dbf = tk.LabelFrame(inner, text=" Database Backup ", font=FONT_MB,
                            bg=P["snow"], fg=P["text_dark"], padx=16, pady=10)
        dbf.pack(fill=tk.X, padx=16, pady=6)
        def backup():
            path = filedialog.asksaveasfilename(defaultextension=".db",
                                                filetypes=[("SQLite","*.db")])
            if path:
                shutil.copy2(DB_PATH, path)
                messagebox.showinfo("Backup","Database backed up successfully!")
        self._pill(dbf,"💾 Backup Database",P["blue"],"white",backup,padx=16,pady=8).pack(pady=4)

    def _load_users(self):
        for i in self.usr_tree.get_children(): self.usr_tree.delete(i)
        cursor.execute("SELECT id,username,role,is_active FROM users")
        for row in cursor.fetchall():
            self.usr_tree.insert("","end", iid=str(row[0]),
                values=(row[1],row[2],"Yes" if row[3] else "No"))

    def _add_user(self):
        win = tk.Toplevel(self.root); win.title("Add User")
        win.geometry("340x340"); win.configure(bg=P["white"]); win.grab_set()
        tk.Frame(win, bg=P["pink_deep"], height=4).pack(fill=tk.X)
        tk.Label(win, text="New User", font=("Georgia",16,"bold"),
                 bg=P["pink_pale"], fg=P["text_dark"], pady=14).pack(fill=tk.X)
        self._label_field(win,"Username","_uname")
        self._label_field(win,"Password","_upass","●")
        tk.Label(win, text="Role:", font=FONT_SB,
                 bg=P["white"], fg=P["text_mid"]).pack(fill=tk.X, padx=22, pady=(8,1))
        self._urole = tk.StringVar(value="cashier")
        rf = tk.Frame(win, bg=P["white"]); rf.pack(fill=tk.X, padx=22)
        for r in ["cashier","admin"]:
            tk.Radiobutton(rf, text=r.title(), variable=self._urole, value=r,
                           bg=P["white"], font=FONT_M,
                           selectcolor=P["pink_pale"]).pack(side=tk.LEFT, padx=12)
        def save():
            try:
                cursor.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                               (self._uname.get(),_hash(self._upass.get()),self._urole.get()))
                conn.commit(); self._load_users(); win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error","Username already exists.")
        self._pill(win,"💾 Save",P["pink_deep"],"white",save,padx=20,pady=10).pack(pady=14)

    def _del_user(self):
        sel = self.usr_tree.selection()
        if not sel: return
        uname = self.usr_tree.item(sel[0])["values"][0]
        if uname == self.current_user:
            messagebox.showwarning("Error","Cannot delete yourself."); return
        cursor.execute("DELETE FROM users WHERE id=?", (int(sel[0]),))
        conn.commit(); self._load_users()

    # ── Utility ──────────────────────────────────────────────────────────────
    def _clear_root(self):
        for w in self.root.winfo_children(): w.destroy()


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = BakesByAyeshaPOS(root)
    root.mainloop()
    conn.close()