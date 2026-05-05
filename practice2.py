import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
from PIL import Image, ImageTk # Make sure to run 'pip install pillow'
import os

# --- Database Connection & Setup ---
conn = sqlite3.connect('ayesha_bakery.db')
cursor = conn.cursor()

# Create Tables
cursor.execute('''CREATE TABLE IF NOT EXISTS products 
               (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER, 
                category TEXT, image_path TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS sales 
               (id INTEGER PRIMARY KEY, total REAL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

class BakesByAyeshaPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("Bakes by Ayesha - Pro POS System")
        self.root.geometry("1100x750")
        self.root.configure(bg="#fdf2f4")
        
        self.tax_rate = 0.05 # 5% Tax
        self.current_user = None
        self.temp_image_path = "default_cake.png" # Default image
        
        self.login_screen()

    # --- Authentication ---
    def login_screen(self):
        self.login_win = tk.Frame(self.root, bg="white", pdy=50)
        self.login_win.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(self.login_win, text="Admin Login", font=("Arial", 20, "bold"), bg="white").pack(pady=10)
        self.user_ent = tk.Entry(self.login_win, font=("Arial", 12))
        self.user_ent.insert(0, "Ayesha")
        self.user_ent.pack(pady=5)
        
        self.pass_ent = tk.Entry(self.login_win, show="*", font=("Arial", 12))
        self.pass_ent.insert(0, "admin123")
        self.pass_ent.pack(pady=5)
        
        tk.Button(self.login_win, text="Login", bg="#d63384", fg="white", command=self.verify_login).pack(pady=20)

    def verify_login(self):
        if self.user_ent.get() == "Ayesha" and self.pass_ent.get() == "admin123":
            self.login_win.destroy()
            self.main_dashboard()
        else:
            messagebox.showerror("Error", "Ghalat Credentials!")

    # --- Main Dashboard ---
    def main_dashboard(self):
        # Header
        header = tk.Frame(self.root, bg="#d63384", height=80)
        header.pack(fill=tk.X)
        tk.Label(header, text="BAKES BY AYESHA - POS", font=("Helvetica", 22, "bold"), fg="white", bg="#d63384").pack(pady=20)

        # Main Layout
        main_frame = tk.Frame(self.root, bg="#fdf2f4")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # --- Inventory Section (Left) ---
        inv_frame = tk.LabelFrame(main_frame, text=" Inventory Management ", bg="white")
        inv_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.tree = ttk.Treeview(inv_frame, columns=("Price", "Stock", "Category"))
        self.tree.heading("#0", text="Product Name")
        self.tree.heading("Price", text="Price (Rs.)")
        self.tree.heading("Stock", text="Stock")
        self.tree.heading("Category", text="Category")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        # --- Controls (Right) ---
        ctrl_frame = tk.Frame(main_frame, bg="#fdf2f4", width=300)
        ctrl_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        # Image Preview Label
        self.img_label = tk.Label(ctrl_frame, text="No Image", bg="#eee", width=20, height=10)
        self.img_label.pack(pady=10)

        # Buttons
        tk.Button(ctrl_frame, text="Add/Update Item", bg="#0d6efd", fg="white", width=20, command=self.product_window).pack(pady=5)
        tk.Button(ctrl_frame, text="Browse Image", bg="#6c757d", fg="white", width=20, command=self.upload_image).pack(pady=5)
        tk.Button(ctrl_frame, text="Process Sale (POS)", bg="#198754", fg="white", width=20, command=self.pos_window).pack(pady=5)
        tk.Button(ctrl_frame, text="Bulk Stock Edit", bg="#fd7e14", fg="white", width=20, command=self.bulk_edit).pack(pady=5)

        self.refresh_table()

    # --- Logic Functions ---
    def upload_image(self):
        f_types = [('Png Files', '*.png'), ('Jpg Files', '*.jpg')]
        path = filedialog.askopenfilename(filetypes=f_types)
        if path:
            self.temp_image_path = path
            # Show preview
            img = Image.open(path).resize((150, 150))
            photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=photo, text="")
            self.img_label.image = photo

    def refresh_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        cursor.execute("SELECT name, price, stock, category FROM products")
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, text=row[0], values=(row[1], row[2], row[3]))

    def on_item_select(self, event):
        selected = self.tree.selection()
        if selected:
            name = self.tree.item(selected[0])['text']
            cursor.execute("SELECT image_path FROM products WHERE name=?", (name,))
            res = cursor.fetchone()
            if res and res[0] and os.path.exists(res[0]):
                img = Image.open(res[0]).resize((150, 150))
                photo = ImageTk.PhotoImage(img)
                self.img_label.config(image=photo)
                self.img_label.image = photo

    def product_window(self):
        win = tk.Toplevel(self.root)
        win.title("Manage Product")
        win.geometry("300x400")
        
        tk.Label(win, text="Name:").pack()
        name_e = tk.Entry(win); name_e.pack()
        tk.Label(win, text="Price:").pack()
        price_e = tk.Entry(win); price_e.pack()
        tk.Label(win, text="Stock:").pack()
        stock_e = tk.Entry(win); stock_e.pack()
        tk.Label(win, text="Category:").pack()
        cat_e = tk.Entry(win); cat_e.pack()

        def save():
            cursor.execute("INSERT OR REPLACE INTO products (name, price, stock, category, image_path) VALUES (?,?,?,?,?)",
                           (name_e.get(), float(price_e.get()), int(stock_e.get()), cat_e.get(), self.temp_image_path))
            conn.commit()
            self.refresh_table()
            win.destroy()
        
        tk.Button(win, text="Save to Database", command=save, bg="#198754", fg="white").pack(pady=20)

    def pos_window(self):
        selected = self.tree.selection()
        if not selected: return
        name = self.tree.item(selected[0])['text']
        
        win = tk.Toplevel(self.root)
        win.title("Finalize Bill")
        
        tk.Label(win, text="Coupon Code (Optional):").pack()
        coupon_e = tk.Entry(win); coupon_e.pack()

        def apply():
            cursor.execute("SELECT price, stock FROM products WHERE name=?", (name,))
            price, stock = cursor.fetchone()
            
            subtotal = price
            discount = 0.10 if coupon_e.get() == "AYESHA10" else 0 # 10% Coupon
            tax = subtotal * self.tax_rate
            final_total = (subtotal - (subtotal * discount)) + tax
            
            # Update DB
            cursor.execute("UPDATE products SET stock = stock - 1 WHERE name=?", (name,))
            cursor.execute("INSERT INTO sales (total) VALUES (?)", (final_total,))
            conn.commit()
            
            bill = f"--- Bakes by Ayesha ---\nItem: {name}\nTax (5%): {tax}\nDiscount: {discount*100}%\nTotal: Rs.{final_total:.2f}"
            messagebox.showinfo("Receipt", bill)
            self.refresh_table()
            win.destroy()

        tk.Button(win, text="Generate Bill", command=apply).pack(pady=10)

    def bulk_edit(self):
        # Simple bulk update: increase all prices by 10%
        cursor.execute("UPDATE products SET price = price * 1.1")
        conn.commit()
        self.refresh_table()
        messagebox.showinfo("Bulk Update", "All prices increased by 10% (Inflation update)!")

if __name__ == "__main__":
    root = tk.Tk()
    app = BakesByAyeshaPOS(root)
    root.mainloop()