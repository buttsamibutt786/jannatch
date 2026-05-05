import tkinter as tk
from tkinter import messagebox, ttk

# 1. Product Class (OOP Concept: Storing individual product data)
class Product:
    def __init__(self, name, price, stock, category):
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category

# 2. Store Management System Class
class BakesByAyesha:
    def __init__(self, root):
        self.root = root
        self.root.title("Bakes by Ayesha - Smart Store Management")
        self.root.geometry("900x700")
        self.root.configure(bg="#f8f9fa")

        # Data Structures
        self.inventory = {}  # Dictionary to store products
        self.total_sales = 0.0
        
        # Default Items (Starting Data)
        self.add_default_data()

        # GUI Components
        self.setup_gui()

    def add_default_data(self):
        # Adding some initial bakery items
        initial_items = [
            ("Fudge Cake", 1500, 5, "Cakes"),
            ("Chicken Patty", 80, 50, "Savory"),
            ("Milk Bread", 120, 10, "Bread"),
            ("Cupcake", 150, 20, "Pastry")
        ]
        for name, price, stock, cat in initial_items:
            self.inventory[name] = Product(name, price, stock, cat)

    def setup_gui(self):
        # --- Header ---
        header = tk.Label(self.root, text="BAKES BY AYESHA", font=("Helvetica", 24, "bold"), 
                         bg="#d63384", fg="white", pady=10)
        header.pack(fill=tk.X)

        # --- Main Layout (Frames) ---
        main_frame = tk.Frame(self.root, bg="#f8f9fa", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left Side: Inventory Display
        left_frame = tk.LabelFrame(main_frame, text=" Inventory Management ", font=("Arial", 12, "bold"), bg="white")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Treeview (Table) for Products
        self.tree = ttk.Treeview(left_frame, columns=("Price", "Stock", "Category"), show='headings')
        self.tree.heading("Price", text="Price (Rs.)")
        self.tree.heading("Stock", text="Stock")
        self.tree.heading("Category", text="Category")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.update_treeview()

        # Right Side: Operations
        right_frame = tk.Frame(main_frame, bg="#f8f9fa")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        # Buttons with Professional Styling
        btn_style = {"font": ("Arial", 10, "bold"), "width": 20, "pady": 10}
        
        tk.Button(right_frame, text="Add/Update Product", bg="#198754", fg="white", **btn_style, command=self.add_product_window).pack(pady=5)
        tk.Button(right_frame, text="Sell Product (POS)", bg="#0d6efd", fg="white", **btn_style, command=self.pos_window).pack(pady=5)
        tk.Button(right_frame, text="Delete Product", bg="#dc3545", fg="white", **btn_style, command=self.delete_product).pack(pady=5)
        tk.Button(right_frame, text="View Total Sales", bg="#6c757d", fg="white", **btn_style, command=self.show_sales).pack(pady=5)

        # --- Low Stock Alert Bar ---
        self.alert_label = tk.Label(self.root, text="", font=("Arial", 10, "italic"), bg="#f8f9fa", fg="red")
        self.alert_label.pack(pady=5)
        self.check_low_stock()

    # --- Core Functions ---

    def update_treeview(self, filter_data=None):
        # Clear current list
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        data = filter_data if filter_data else self.inventory
        for name, p in data.items():
            self.tree.insert("", tk.END, iid=name, text=name, values=(p.price, p.stock, p.category))

    def add_product_window(self):
        win = tk.Toplevel(self.root)
        win.title("Manage Inventory")
        win.geometry("300x400")

        tk.Label(win, text="Product Name:").pack(pady=5)
        name_ent = tk.Entry(win)
        name_ent.pack()

        tk.Label(win, text="Price:").pack(pady=5)
        price_ent = tk.Entry(win)
        price_ent.pack()

        tk.Label(win, text="Stock:").pack(pady=5)
        stock_ent = tk.Entry(win)
        stock_ent.pack()

        tk.Label(win, text="Category:").pack(pady=5)
        cat_ent = tk.Entry(win)
        cat_ent.pack()

        def save():
            try:
                name = name_ent.get()
                price = float(price_ent.get())
                stock = int(stock_ent.get())
                cat = cat_ent.get()
                
                if name:
                    self.inventory[name] = Product(name, price, stock, cat)
                    self.update_treeview()
                    self.check_low_stock()
                    win.destroy()
                    messagebox.showinfo("Success", f"{name} added/updated!")
            except ValueError:
                messagebox.showerror("Error", "Invalid Price or Stock!")

        tk.Button(win, text="Save Product", bg="#198754", fg="white", command=save).pack(pady=20)

    def pos_window(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Pehle list se product select karein!")
            return
        
        prod_name = selected[0]
        product = self.inventory[prod_name]

        win = tk.Toplevel(self.root)
        win.title("POS - Sale")
        win.geometry("300x200")

        tk.Label(win, text=f"Selling: {prod_name}", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(win, text="Enter Quantity:").pack()
        qty_ent = tk.Entry(win)
        qty_ent.pack()

        def process_sale():
            try:
                qty = int(qty_ent.get())
                if qty <= 0: raise ValueError
                
                if qty <= product.stock:
                    total = qty * product.price
                    product.stock -= qty
                    self.total_sales += total
                    
                    # Generate Simple Bill
                    bill_msg = f"--- Bakes by Ayesha ---\nItem: {prod_name}\nQty: {qty}\nTotal: Rs. {total}\n\nThank you for coming!"
                    messagebox.showinfo("Bill Generated", bill_msg)
                    
                    self.update_treeview()
                    self.check_low_stock()
                    win.destroy()
                else:
                    messagebox.showerror("Error", "Stock kam hai!")
            except:
                messagebox.showerror("Error", "Quantity sahi likhen!")

        tk.Button(win, text="Print Bill & Sell", bg="#0d6efd", fg="white", command=process_sale).pack(pady=10)

    def delete_product(self):
        selected = self.tree.selection()
        if selected:
            name = selected[0]
            del self.inventory[name]
            self.update_treeview()
            messagebox.showinfo("Deleted", f"{name} removed from inventory.")

    def show_sales(self):
        messagebox.showinfo("Total Sales", f"Aaj ki kul sale: Rs. {self.total_sales}")

    def check_low_stock(self):
        low_items = [p.name for p in self.inventory.values() if p.stock < 5]
        if low_items:
            self.alert_label.config(text=f"Low Stock Alert: {', '.join(low_items)}")
        else:
            self.alert_label.config(text="")

# --- Main Logic ---
if __name__ == "__main__":
    root = tk.Tk()
    app = BakesByAyesha(root)
    root.mainloop()