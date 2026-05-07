import tkinter as tk

class MapDisplayGUI:
    """
    Manages the visual grid. Its only job is to draw what it's told.
    It has no internal logic for timers or key presses.
    """
    GRID_SIZE = 17
    SQUARE_SIZE = 25
    MARGIN = 70

    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Map")
        self.player_x = 8
        self.player_y = 8
        
        canvas_width = self.GRID_SIZE * self.SQUARE_SIZE + self.MARGIN
        canvas_height = self.GRID_SIZE * self.SQUARE_SIZE + self.MARGIN
        
        self.canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='white')
        self.canvas.pack(padx=10, pady=10)
        
        self.grid_rects = []
        self.special_squares = {
            (0, 0): "red", (16, 16): "blue",
            (0, 16): "green", (16, 0): "gold",
            (8, 8): "slate gray"
        }

        self._create_grid_and_labels()
        self._color_special_squares()
        self._draw_player()

    def move_player(self, direction):
        """Public method to move the player block one step."""
        old_x, old_y = self.player_x, self.player_y

        if direction == 'Left' and self.player_x > 0: self.player_x -= 1
        elif direction == 'Right' and self.player_x < self.GRID_SIZE - 1: self.player_x += 1
        elif direction == 'Up' and self.player_y > 0: self.player_y -= 1
        elif direction == 'Down' and self.player_y < self.GRID_SIZE - 1: self.player_y += 1
        
        if old_x != self.player_x or old_y != self.player_y:
            self._update_player_view(old_x, old_y)

    def _update_player_view(self, old_x, old_y):
        """Redraws the player's old and new squares."""
        old_pos = (old_y, old_x)
        old_rect_id = self.grid_rects[old_y][old_x]
        
        # Restore color of the old square
        if old_pos in self.special_squares:
            self.canvas.itemconfig(old_rect_id, fill=self.special_squares[old_pos])
        else:
            self.canvas.itemconfig(old_rect_id, fill="white")
            
        self._draw_player()

    def _draw_player(self):
        """Colors the player's current square black."""
        player_rect_id = self.grid_rects[self.player_y][self.player_x]
        self.canvas.itemconfig(player_rect_id, fill="black")

    def _color_special_squares(self):
        for (y, x), color in self.special_squares.items():
            self.canvas.itemconfig(self.grid_rects[y][x], fill=color)

    def _create_grid_and_labels(self):
        # Draw grid squares first
        for y in range(self.GRID_SIZE):
            row = []
            for x in range(self.GRID_SIZE):
                x1 = x * self.SQUARE_SIZE + self.MARGIN
                y1 = y * self.SQUARE_SIZE + self.MARGIN
                x2, y2 = x1 + self.SQUARE_SIZE, y1 + self.SQUARE_SIZE
                rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="grey")
                row.append(rect_id)
            self.grid_rects.append(row)
        
        # Draw labels on top
        for i in range(self.GRID_SIZE):
            self.canvas.create_text(self.MARGIN / 2, i * self.SQUARE_SIZE + self.MARGIN + (self.SQUARE_SIZE / 2), text=str(i))
            self.canvas.create_text(i * self.SQUARE_SIZE + self.MARGIN + (self.SQUARE_SIZE / 2), self.MARGIN / 2, text=str(i))
        
        self.canvas.create_text((self.GRID_SIZE * self.SQUARE_SIZE + self.MARGIN) / 2, 15, text="X-Axis", font=("Arial", 10, "bold"))
        self.canvas.create_text(15, (self.GRID_SIZE * self.SQUARE_SIZE + self.MARGIN) / 2, text="Y-Axis", font=("Arial", 10, "bold"), angle=90)