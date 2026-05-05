
"""
BAKES BY AYESHA — Modern POS System
Complete working version with all features
Run: python bakery_pos.py
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3, os, shutil, datetime, csv, hashlib

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PILLOW_INSTALLED = True
except ImportError:
    PILLOW_INSTALLED = False
    print("Pillow not installed. Run: pip install Pillow")

# Database setup
DB_PATH = "ayesha_bakery.db"
IMG_DIR = "bakery_images"
os.makedirs(IMG_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
cursor.executescript('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        price REAL NOT NULL,
        stock INTEGER DEFAULT 0,
        category TEXT DEFAULT 'Uncategorized',
        image_path TEXT,
        description TEXT,
        cost_price REAL DEFAULT 0,
        discount_pct REAL DEFAULT 0,
        is_bestseller INTEGER DEFAULT 0,
        is_new INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE,
        subtotal REAL, discount REAL DEFAULT 0,
        tax REAL DEFAULT 0, total REAL,
        payment_method TEXT DEFAULT 'Cash',
        cashier TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS sale_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER, product_id INTEGER,
        product_name TEXT, quantity INTEGER,
        unit_price REAL, total REAL
    );
    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE, type TEXT,
        value REAL, min_purchase REAL DEFAULT 0,
        max_uses INTEGER DEFAULT 999, used_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT UNIQUE,
        loyalty_pts INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE, password TEXT,
        role TEXT DEFAULT 'cashier', is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_invoice TEXT UNIQUE,
        original_invoice TEXT,
        refund_amount REAL, reason TEXT,
        cashier TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS return_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_id INTEGER, product_id INTEGER,
        product_name TEXT, quantity INTEGER,
        unit_price REAL, refund_total REAL
    );
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT, amount REAL,
        description TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS logo_settings (
        id INTEGER PRIMARY KEY,
        logo_path TEXT, logo_size INTEGER DEFAULT 32
    );
''')
conn.commit()

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# Create default admin user
cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
               ("admin", hash_password("admin123"), "admin"))
cursor.execute("INSERT OR IGNORE INTO logo_settings (id, logo_path, logo_size) VALUES (1, '', 32)")
conn.commit()

# Sample products
sample_products = [
    ("Butter Croissant", 280, 50, "Pastries", 0, 0),
    ("Chocolate Cake", 1800, 10, "Cakes", 10, 1),
    ("Red Velvet Cupcake", 180, 60, "Cupcakes", 0, 0),
    ("Sourdough Bread", 450, 30, "Bread", 0, 0),
    ("Cheese Danish", 220, 40, "Pastries", 5, 0),
    ("Blueberry Muffin", 160, 55, "Muffins", 0, 1),
]

for p in sample_products:
    cursor.execute("INSERT OR IGNORE INTO products (name, price, stock, category, discount_pct, is_bestseller) VALUES (?,?,?,?,?,?)", p)
conn.commit()

# Color scheme
COLORS = {
    "bg": "#FFF0F5",
    "white": "#FFFFFF",
    "pink": "#FFB3CE",
    "pink_dark": "#E8527A",
    "text_dark": "#3D1A2E",
    "text_soft": "#B07090",
    "green": "#4CAF82",
    "red": "#E84B6A",
    "blue": "#7B9ED9",
}

# Main Application
class BakeryPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Bakes by Ayesha - POS System")
        self.root.geometry("1300x800")
        self.root.configure(bg=COLORS["bg"])
        
        self.current_user = None
        self.cart = []
        
        self.login_screen()
    
    def login_screen(self):
        # Clear window
        for w in self.root.winfo_children():
            w.destroy()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=COLORS["white"])
        main_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=500)
        
        # Title
        tk.Label(main_frame, text="🎀 BAKES BY AYESHA 🎀", 
                font=("Georgia", 20, "bold"),
                bg=COLORS["white"], fg=COLORS["text_dark"]).pack(pady=30)
        
        tk.Label(main_frame, text="Login to Dashboard",
                font=("Helvetica", 12), bg=COLORS["white"],
                fg=COLORS["text_soft"]).pack(pady=10)
        
        # Username
        tk.Label(main_frame, text="Username", font=("Helvetica", 10, "bold"),
                bg=COLORS["white"], fg=COLORS["text_soft"]).pack(anchor="w", padx=40, pady=(20,5))
        self.username_entry = tk.Entry(main_frame, font=("Helvetica", 12),
                                       bg=COLORS["bg"], fg=COLORS["text_dark"],
                                       relief="flat", bd=0, highlightthickness=1)
        self.username_entry.pack(fill="x", padx=40, ipady=8)
        self.username_entry.insert(0, "admin")
        
        # Password
        tk.Label(main_frame, text="Password", font=("Helvetica", 10, "bold"),
                bg=COLORS["white"], fg=COLORS["text_soft"]).pack(anchor="w", padx=40, pady=(15,5))
        self.password_entry = tk.Entry(main_frame, font=("Helvetica", 12),
                                       bg=COLORS["bg"], fg=COLORS["text_dark"],
                                       relief="flat", bd=0, highlightthickness=1, show="*")
        self.password_entry.pack(fill="x", padx=40, ipady=8)
        self.password_entry.insert(0, "admin123")
        
        # Login button
        login_btn = tk.Button(main_frame, text="SIGN IN", 
                              bg=COLORS["pink_dark"], fg="white",
                              font=("Helvetica", 12, "bold"),
                              relief="flat", cursor="hand2",
                              command=self.do_login)
        login_btn.pack(fill="x", padx=40, pady=30, ipady=10)
        
        self.password_entry.bind("<Return>", lambda e: self.do_login())
    
    def do_login(self):
        username = self.username_entry.get()
        password = hash_password(self.password_entry.get())
        
        cursor.execute("SELECT role FROM users WHERE username=? AND password=? AND is_active=1",
                      (username, password))
        user = cursor.fetchone()
        
        if user:
            self.current_user = username
            self.main_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def main_dashboard(self):
        # Clear window
        for w in self.root.winfo_children():
            w.destroy()
        
        # Header
        header = tk.Frame(self.root, bg=COLORS["white"], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🎀", font=("Helvetica", 30),
                bg=COLORS["white"]).pack(side="left", padx=20)
        
        tk.Label(header, text="Bakes by Ayesha",
                font=("Georgia", 18, "bold"),
                bg=COLORS["white"], fg=COLORS["text_dark"]).pack(side="left")
        
        tk.Label(header, text=f"Welcome, {self.current_user}",
                font=("Helvetica", 10),
                bg=COLORS["white"], fg=COLORS["text_soft"]).pack(side="right", padx=20)
        
        # Navigation buttons
        nav_frame = tk.Frame(self.root, bg=COLORS["pink"])
        nav_frame.pack(fill="x", pady=10)
        
        nav_items = [
            ("🛒 POS", self.pos_tab),
            ("📦 Inventory", self.inventory_tab),
            ("🏷️ Coupons", self.coupons_tab),
            ("📊 Reports", self.reports_tab),
            ("👥 Customers", self.customers_tab),
            ("⚙️ Settings", self.settings_tab)
        ]
        
        self.nav_buttons = {}
        for text, command in nav_items:
            btn = tk.Button(nav_frame, text=text, font=("Helvetica", 10, "bold"),
                           bg=COLORS["white"], fg=COLORS["text_dark"],
                           relief="flat", padx=20, pady=8, cursor="hand2",
                           command=command)
            btn.pack(side="left", padx=5, pady=5)
            self.nav_buttons[text] = btn
        
        # Content area
        self.content_frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Start with POS tab
        self.pos_tab()
    
    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
    
    # POS TAB
    def pos_tab(self):
        self.clear_content()
        self.cart = []
        
        # Left side - Products
        left_frame = tk.Frame(self.content_frame, bg=COLORS["bg"])
        left_frame.pack(side="left", fill="both", expand=True, padx=(0,5))
        
        # Search
        search_frame = tk.Frame(left_frame, bg=COLORS["white"])
        search_frame.pack(fill="x", pady=(0,10))
        
        tk.Label(search_frame, text="🔍", font=("Helvetica", 14),
                bg=COLORS["white"]).pack(side="left", padx=10)
        
        self.search_entry = tk.Entry(search_frame, font=("Helvetica", 12),
                                     bg=COLORS["white"], relief="flat", bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_products())
        
        # Products grid
        self.products_frame = tk.Frame(left_frame, bg=COLORS["bg"])
        self.products_frame.pack(fill="both", expand=True)
        
        self.load_products()
        
        # Right side - Cart
        right_frame = tk.Frame(self.content_frame, bg=COLORS["white"], width=350)
        right_frame.pack(side="right", fill="y", padx=(5,0))
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="🛒 Current Order",
                font=("Georgia", 14, "bold"),
                bg=COLORS["white"], fg=COLORS["text_dark"]).pack(pady=10)
        
        # Cart Treeview
        columns = ("Product", "Qty", "Price", "Total")
        self.cart_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=80)
        self.cart_tree.pack(fill="x", padx=10, pady=5)
        
        # Totals
        self.total_label = tk.Label(right_frame, text="Total: Rs. 0.00",
                                   font=("Georgia", 16, "bold"),
                                   bg=COLORS["white"], fg=COLORS["pink_dark"])
        self.total_label.pack(pady=10)
        
        # Checkout button
        checkout_btn = tk.Button(right_frame, text="Complete Sale",
                                 bg=COLORS["green"], fg="white",
                                 font=("Helvetica", 12, "bold"),
                                 relief="flat", cursor="hand2",
                                 command=self.checkout)
        checkout_btn.pack(fill="x", padx=20, pady=10, ipady=8)
        
        # Clear cart button
        clear_btn = tk.Button(right_frame, text="Clear Cart",
                              bg=COLORS["red"], fg="white",
                              font=("Helvetica", 10),
                              relief="flat", cursor="hand2",
                              command=self.clear_cart)
        clear_btn.pack(fill="x", padx=20, pady=5, ipady=5)
    
    def load_products(self):
        for w in self.products_frame.winfo_children():
            w.destroy()
        
        search = self.search_entry.get().strip()
        if search:
            cursor.execute("SELECT id, name, price, stock, discount_pct FROM products WHERE name LIKE ? AND is_active=1",
                          (f"%{search}%",))
        else:
            cursor.execute("SELECT id, name, price, stock, discount_pct FROM products WHERE is_active=1")
        
        products = cursor.fetchall()
        
        row = 0
        col = 0
        for product in products:
            pid, name, price, stock, discount = product
            
            # Calculate final price
            final_price = price * (1 - discount/100) if discount else price
            
            # Product card
            card = tk.Frame(self.products_frame, bg=COLORS["white"],
                           relief="solid", bd=1)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            tk.Label(card, text=name, font=("Helvetica", 10, "bold"),
                    bg=COLORS["white"], fg=COLORS["text_dark"]).pack(pady=(10,2))
            
            if discount > 0:
                tk.Label(card, text=f"Rs. {price:.0f}", font=("Helvetica", 8),
                        bg=COLORS["white"], fg=COLORS["text_soft"],
                        relief="solid", bd=0).pack()
            
            tk.Label(card, text=f"Rs. {final_price:.0f}", font=("Helvetica", 12, "bold"),
                    bg=COLORS["white"], fg=COLORS["pink_dark"]).pack()
            
            tk.Label(card, text=f"Stock: {stock}", font=("Helvetica", 8),
                    bg=COLORS["white"], fg=COLORS["green"] if stock > 5 else COLORS["red"]).pack()
            
            if stock > 0:
                add_btn = tk.Button(card, text="Add to Cart",
                                   bg=COLORS["pink_dark"], fg="white",
                                   font=("Helvetica", 8),
                                   relief="flat", cursor="hand2",
                                   command=lambda p=(pid, name, final_price, stock): self.add_to_cart(p))
                add_btn.pack(fill="x", pady=(5,10), padx=10)
            else:
                tk.Label(card, text="Out of Stock", font=("Helvetica", 8),
                        bg=COLORS["red"], fg="white").pack(fill="x", pady=5)
            
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(4):
            self.products_frame.columnconfigure(i, weight=1)
    
    def add_to_cart(self, product):
        pid, name, price, stock = product
        
        for item in self.cart:
            if item["pid"] == pid:
                if item["qty"] + 1 > stock:
                    messagebox.showwarning("Out of Stock", f"Cannot add more than {stock} items")
                    return
                item["qty"] += 1
                self.update_cart_display()
                return
        
        self.cart.append({"pid": pid, "name": name, "price": price, "qty": 1})
        self.update_cart_display()
    
    def update_cart_display(self):
        # Clear tree
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        total = 0
        for item in self.cart:
            item_total = item["price"] * item["qty"]
            total += item_total
            self.cart_tree.insert("", "end", values=(item["name"], item["qty"], f"Rs.{item['price']:.0f}", f"Rs.{item_total:.0f}"))
        
        self.total_label.config(text=f"Total: Rs. {total:.2f}")
    
    def clear_cart(self):
        self.cart = []
        self.update_cart_display()
    
    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to cart")
            return
        
        total = sum(item["price"] * item["qty"] for item in self.cart)
        
        # Generate invoice number
        invoice_no = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save sale
        cursor.execute("INSERT INTO sales (invoice_no, subtotal, total, cashier) VALUES (?,?,?,?)",
                      (invoice_no, total, total, self.current_user))
        sale_id = cursor.lastrowid
        
        # Save sale items and update stock
        for item in self.cart:
            cursor.execute("INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total) VALUES (?,?,?,?,?,?)",
                          (sale_id, item["pid"], item["name"], item["qty"], item["price"], item["price"] * item["qty"]))
            
            cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                          (item["qty"], item["pid"]))
        
        conn.commit()
        
        # Show receipt
        receipt = f"""
{'='*40}
BAKES BY AYESHA
{'='*40}
Invoice: {invoice_no}
Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
Cashier: {self.current_user}
{'='*40}

Items:
"""
        for item in self.cart:
            receipt += f"{item['name']:<20} x{item['qty']:<3} = Rs.{item['price']*item['qty']:.0f}\n"
        
        receipt += f"""
{'='*40}
Total: Rs. {total:.2f}
{'='*40}
Thank you! Visit Again 🌸
"""
        
        messagebox.showinfo("Sale Complete", f"Sale completed!\nInvoice: {invoice_no}\nTotal: Rs. {total:.2f}")
        
        # Show receipt in new window
        receipt_win = tk.Toplevel(self.root)
        receipt_win.title("Receipt")
        receipt_win.geometry("400x500")
        receipt_win.configure(bg=COLORS["white"])
        
        text_widget = tk.Text(receipt_win, font=("Courier", 10), bg=COLORS["white"])
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", receipt)
        text_widget.config(state="disabled")
        
        # Clear cart and refresh
        self.clear_cart()
        self.load_products()
    
    # INVENTORY TAB
    def inventory_tab(self):
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0,10))
        
        tk.Label(header, text="📦 Inventory Management",
                font=("Georgia", 16, "bold"),
                bg=COLORS["bg"], fg=COLORS["text_dark"]).pack(side="left")
        
        # Add product button
        add_btn = tk.Button(header, text="+ Add Product",
                           bg=COLORS["green"], fg="white",
                           font=("Helvetica", 10, "bold"),
                           relief="flat", cursor="hand2",
                           command=self.add_product)
        add_btn.pack(side="right")
        
        # Search
        search_frame = tk.Frame(self.content_frame, bg=COLORS["white"])
        search_frame.pack(fill="x", pady=(0,10))
        
        tk.Label(search_frame, text="🔍 Search:", bg=COLORS["white"]).pack(side="left", padx=10)
        self.inv_search = tk.Entry(search_frame, font=("Helvetica", 11),
                                   bg=COLORS["white"], relief="flat", bd=0)
        self.inv_search.pack(side="left", fill="x", expand=True, ipady=6)
        self.inv_search.bind("<KeyRelease>", lambda e: self.load_inventory())
        
        # Products table
        columns = ("ID", "Name", "Price", "Stock", "Category", "Discount", "Status")
        self.inv_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.inv_tree.heading(col, text=col)
            self.inv_tree.column(col, width=120)
        
        self.inv_tree.pack(fill="both", expand=True)
        
        # Action buttons
        action_frame = tk.Frame(self.content_frame, bg=COLORS["bg"])
        action_frame.pack(fill="x", pady=10)
        
        tk.Button(action_frame, text="Edit", bg=COLORS["blue"], fg="white",
                 relief="flat", cursor="hand2", padx=20,
                 command=self.edit_product).pack(side="left", padx=5)
        
        tk.Button(action_frame, text="Delete", bg=COLORS["red"], fg="white",
                 relief="flat", cursor="hand2", padx=20,
                 command=self.delete_product).pack(side="left", padx=5)
        
        self.load_inventory()
    
    def load_inventory(self):
        for item in self.inv_tree.get_children():
            self.inv_tree.delete(item)
        
        search = self.inv_search.get().strip() if hasattr(self, 'inv_search') else ""
        
        if search:
            cursor.execute("SELECT id, name, price, stock, category, discount_pct, is_active FROM products WHERE name LIKE ?", (f"%{search}%",))
        else:
            cursor.execute("SELECT id, name, price, stock, category, discount_pct, is_active FROM products")
        
        for product in cursor.fetchall():
            status = "Active" if product[6] else "Inactive"
            self.inv_tree.insert("", "end", values=(product[0], product[1], f"Rs.{product[2]:.0f}", 
                                                    product[3], product[4], f"{product[5]}%", status))
    
    def add_product(self):
        self.product_form(title="Add New Product")
    
    def edit_product(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a product to edit")
            return
        
        values = self.inv_tree.item(selected[0])['values']
        self.product_form(title="Edit Product", product_id=values[0])
    
    def product_form(self, title="Product", product_id=None):
        form_win = tk.Toplevel(self.root)
        form_win.title(title)
        form_win.geometry("400x500")
        form_win.configure(bg=COLORS["white"])
        
        tk.Label(form_win, text=title, font=("Georgia", 16, "bold"),
                bg=COLORS["white"], fg=COLORS["text_dark"]).pack(pady=20)
        
        # Form fields
        fields = {}
        labels = ["Name:", "Price (Rs.):", "Stock:", "Category:", "Discount (%):"]
        
        for i, (label, field) in enumerate(zip(labels, ["name", "price", "stock", "category", "discount"])):
            tk.Label(form_win, text=label, font=("Helvetica", 10),
                    bg=COLORS["white"], fg=COLORS["text_soft"]).pack(anchor="w", padx=30, pady=(10,2))
            
            entry = tk.Entry(form_win, font=("Helvetica", 11),
                            bg=COLORS["bg"], relief="flat", bd=0,
                            highlightthickness=1)
            entry.pack(fill="x", padx=30, ipady=6)
            fields[field] = entry
        
        # Load data if editing
        if product_id:
            cursor.execute("SELECT name, price, stock, category, discount_pct FROM products WHERE id=?", (product_id,))
            product = cursor.fetchone()
            if product:
                fields["name"].insert(0, product[0])
                fields["price"].insert(0, str(product[1]))
                fields["stock"].insert(0, str(product[2]))
                fields["category"].insert(0, product[3])
                fields["discount"].insert(0, str(product[4]))
        
        def save_product():
            try:
                name = fields["name"].get().strip()
                price = float(fields["price"].get())
                stock = int(fields["stock"].get())
                category = fields["category"].get().strip() or "General"
                discount = float(fields["discount"].get() or 0)
                
                if product_id:
                    cursor.execute("""UPDATE products SET name=?, price=?, stock=?, category=?, discount_pct=? WHERE id=?""",
                                  (name, price, stock, category, discount, product_id))
                else:
                    cursor.execute("""INSERT INTO products (name, price, stock, category, discount_pct) VALUES (?,?,?,?,?)""",
                                  (name, price, stock, category, discount))
                
                conn.commit()
                messagebox.showinfo("Success", "Product saved successfully")
                self.load_inventory()
                form_win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Product name already exists")
        
        tk.Button(form_win, text="Save Product",
                 bg=COLORS["green"], fg="white",
                 font=("Helvetica", 11, "bold"),
                 relief="flat", cursor="hand2",
                 command=save_product).pack(fill="x", padx=30, pady=30, ipady=8)
    
    def delete_product(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a product to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure?"):
            product_id = self.inv_tree.item(selected[0])['values'][0]
            cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
            conn.commit()
            self.load_inventory()
    
    # COUPONS TAB
    def coupons_tab(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="🏷️ Coupon Management",
                font=("Georgia", 16, "bold"),
                bg=COLORS["bg"], fg=COLORS["text_dark"]).pack(pady=(0,10))
        
        # Add coupon button
        add_btn = tk.Button(self.content_frame, text="+ Add Coupon",
                           bg=COLORS["green"], fg="white",
                           font=("Helvetica", 10, "bold"),
                           relief="flat", cursor="hand2",
                           command=self.add_coupon)
        add_btn.pack(anchor="e", pady=(0,10))
        
        # Coupons table
        columns = ("ID", "Code", "Type", "Value", "Min Purchase", "Uses", "Active")
        self.coupon_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.coupon_tree.heading(col, text=col)
            self.coupon_tree.column(col, width=120)
        
        self.coupon_tree.pack(fill="both", expand=True)
        
        self.load_coupons()
    
    def load_coupons(self):
        for item in self.coupon_tree.get_children():
            self.coupon_tree.delete(item)
        
        cursor.execute("SELECT id, code, type, value, min_purchase, used_count, is_active FROM coupons")
        for coupon in cursor.fetchall():
            active = "Yes" if coupon[6] else "No"
            self.coupon_tree.insert("", "end", values=(coupon[0], coupon[1], coupon[2], 
                                                       f"{coupon[3]}{'%' if coupon[2]=='percent' else 'Rs'}",
                                                       f"Rs.{coupon[4]}", coupon[5], active))
    
    def add_coupon(self):
        form_win = tk.Toplevel(self.root)
        form_win.title("Add Coupon")
        form_win.geometry("350x400")
        form_win.configure(bg=COLORS["white"])
        
        tk.Label(form_win, text="Add New Coupon", font=("Georgia", 14, "bold"),
                bg=COLORS["white"], fg=COLORS["text_dark"]).pack(pady=20)
        
        fields = {}
        labels = ["Code:", "Type (percent/flat):", "Value:", "Min Purchase (Rs.):", "Max Uses:"]
        
        for i, label in enumerate(labels):
            tk.Label(form_win, text=label, font=("Helvetica", 10),
                    bg=COLORS["white"], fg=COLORS["text_soft"]).pack(anchor="w", padx=30, pady=(10,2))
            
            entry = tk.Entry(form_win, font=("Helvetica", 11),
                            bg=COLORS["bg"], relief="flat", bd=0,
                            highlightthickness=1)
            entry.pack(fill="x", padx=30, ipady=6)
            fields[label] = entry
        
        def save():
            try:
                code = fields["Code:"].get().strip().upper()
                ctype = fields["Type (percent/flat):"].get().strip().lower()
                value = float(fields["Value:"].get())
                min_purchase = float(fields["Min Purchase (Rs.):"].get() or 0)
                max_uses = int(fields["Max Uses:"].get() or 999)
                
                cursor.execute("""INSERT INTO coupons (code, type, value, min_purchase, max_uses) VALUES (?,?,?,?,?)""",
                              (code, ctype, value, min_purchase, max_uses))
                conn.commit()
                messagebox.showinfo("Success", "Coupon added successfully")
                self.load_coupons()
                form_win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Coupon code already exists")
        
        tk.Button(form_win, text="Save Coupon",
                 bg=COLORS["green"], fg="white",
                 font=("Helvetica", 11, "bold"),
                 relief="flat", cursor="hand2",
                 command=save).pack(fill="x", padx=30, pady=30, ipady=8)
    
    # REPORTS TAB
    def reports_tab(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="📊 Sales Reports",
                font=("Georgia", 16, "bold"),
                bg=COLORS["bg"], fg=COLORS["text_dark"]).pack(pady=(0,10))
        
        # Summary cards
        cursor.execute("SELECT COUNT(*), SUM(total) FROM sales")
        total_sales, total_revenue = cursor.fetchone()
        
        summary_frame = tk.Frame(self.content_frame, bg=COLORS["bg"])
        summary_frame.pack(fill="x", pady=10)
        
        for title, value in [("Total Orders", total_sales or 0), 
                            ("Total Revenue", f"Rs. {total_revenue or 0:.2f}")]:
            card = tk.Frame(summary_frame, bg=COLORS["white"], relief="solid", bd=1)
            card.pack(side="left", expand=True, fill="x", padx=5)
            
            tk.Label(card, text=title, font=("Helvetica", 10),
                    bg=COLORS["white"], fg=COLORS["text_soft"]).pack(pady=(10,0))
            tk.Label(card, text=str(value), font=("Georgia", 18, "bold"),
                    bg=COLORS["white"], fg=COLORS["pink_dark"]).pack(pady=5)
        
        # Sales table
        columns = ("Invoice", "Date", "Total", "Payment", "Cashier")
        self.sales_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=150)
        
        self.sales_tree.pack(fill="both", expand=True, pady=10)
        
        cursor.execute("SELECT invoice_no, date, total, payment_method, cashier FROM sales ORDER BY date DESC LIMIT 50")
        for sale in cursor.fetchall():
            self.sales_tree.insert("", "end", values=sale)
    
    # CUSTOMERS TAB
    def customers_tab(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="👥 Customer Management",
                font=("Georgia", 16, "bold"),
                bg=COLORS["bg"], fg=COLORS["text_dark"]).pack(pady=(0,10))
        
        columns = ("ID", "Name", "Phone", "Loyalty Points", "Total Spent")
        self.cust_tree = ttk.Treeview(self.content_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.cust_tree.heading(col, text=col)
            self.cust_tree.column(col, width=120)
        
        self.cust_tree.pack(fill="both", expand=True)
        
        cursor.execute("SELECT id, name, phone, loyalty_pts, total_spent FROM customers ORDER BY total_spent DESC")
        for customer in cursor.fetchall():
            self.cust_tree.insert("", "end", values=(customer[0], customer[1], customer[2], customer[3], f"Rs.{customer[4]:.2f}"))
    
    # SETTINGS TAB
    def settings_tab(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="⚙️ System Settings",
                font=("Georgia", 16, "bold"),
                bg=COLORS["bg"], fg=COLORS["text_dark"]).pack(pady=(0,20))
        
        # Change password
        pass_frame = tk.LabelFrame(self.content_frame, text="Change Password",
                                   bg=COLORS["white"], font=("Helvetica", 10, "bold"))
        pass_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(pass_frame, text="New Password:", bg=COLORS["white"]).pack(pady=(10,0))
        self.new_pass = tk.Entry(pass_frame, show="*", bg=COLORS["bg"])
        self.new_pass.pack(pady=5, padx=20, ipady=5)
        
        tk.Label(pass_frame, text="Confirm Password:", bg=COLORS["white"]).pack()
        self.confirm_pass = tk.Entry(pass_frame, show="*", bg=COLORS["bg"])
        self.confirm_pass.pack(pady=5, padx=20, ipady=5)
        
        tk.Button(pass_frame, text="Update Password",
                 bg=COLORS["blue"], fg="white",
                 relief="flat", cursor="hand2",
                 command=self.change_password).pack(pady=10)
        
        # Database backup
        backup_frame = tk.LabelFrame(self.content_frame, text="Database",
                                     bg=COLORS["white"], font=("Helvetica", 10, "bold"))
        backup_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(backup_frame, text="Backup Database",
                 bg=COLORS["green"], fg="white",
                 relief="flat", cursor="hand2",
                 command=self.backup_db).pack(pady=10, padx=20, fill="x")
    
    def change_password(self):
        new = self.new_pass.get()
        confirm = self.confirm_pass.get()
        
        if not new:
            messagebox.showerror("Error", "Please enter a password")
            return
        
        if new != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        cursor.execute("UPDATE users SET password=? WHERE username=?", (hash_password(new), self.current_user))
        conn.commit()
        messagebox.showinfo("Success", "Password updated successfully")
        self.new_pass.delete(0, tk.END)
        self.confirm_pass.delete(0, tk.END)
    
    def backup_db(self):
        backup_path = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, backup_path)
        messagebox.showinfo("Backup Complete", f"Database backed up to {backup_path}")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = BakeryPOS(root)
    root.mainloop()
    conn.close()