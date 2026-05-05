import tkinter as tk
import random

class CatchGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Cake Catcher")
        
        # Game Settings
        self.width = 400
        self.height = 500
        self.score = 0
        
        # Canvas Setup
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg="skyblue")
        self.canvas.pack()
        
        # The Basket
        self.basket = self.canvas.create_rectangle(175, 450, 225, 470, fill="brown")
        
        # The Falling Cake
        self.cake = self.canvas.create_oval(0, 0, 20, 20, fill="pink")
        self.reset_cake()
        
        # Score Display
        self.score_text = self.canvas.create_text(50, 20, text=f"Score: {self.score}", fill="black", font=("Arial", 14))
        
        # Controls
        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)
        
        # Start Game Loop
        self.update_game()

    def reset_cake(self):
        x = random.randint(20, self.width - 20)
        self.canvas.coords(self.cake, x, 0, x + 20, 20)

    def move_left(self, event):
        if self.canvas.coords(self.basket)[0] > 0:
            self.canvas.move(self.basket, -20, 0)

    def move_right(self, event):
        if self.canvas.coords(self.basket)[2] < self.width:
            self.canvas.move(self.basket, 20, 0)

    def update_game(self):
        # Move cake down
        self.canvas.move(self.cake, 0, 5)
        pos = self.canvas.coords(self.cake)
        basket_pos = self.canvas.coords(self.basket)

        # Check if cake is caught
        if pos[3] >= basket_pos[1] and pos[2] >= basket_pos[0] and pos[0] <= basket_pos[2]:
            self.score += 1
            self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
            self.reset_cake()

        # Check if cake hit the floor
        elif pos[3] > self.height:
            self.reset_cake()

        # Repeat every 30ms
        self.root.after(30, self.update_game)

if __name__ == "__main__":
    root = tk.Tk()
    game = CatchGame(root)
    root.mainloop()