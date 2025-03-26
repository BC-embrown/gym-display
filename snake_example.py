#!/usr/bin/env python
# Snake Game for RGB LED Matrix
import time
import random
import sys
import termios
import tty
import threading
from samplebase import SampleBase
from PIL import Image, ImageDraw

# Direction constants
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

class SnakeGame(SampleBase):
    def __init__(self, *args, **kwargs):
        super(SnakeGame, self).__init__(*args, **kwargs)
        self.parser.add_argument("--speed", help="Snake speed (lower is faster)", default=0.2, type=float)
        self.parser.add_argument("--snake-color", help="Snake color (R,G,B)", default="0,255,0")
        self.parser.add_argument("--food-color", help="Food color (R,G,B)", default="255,0,0")
        
    def getch(self):
        """Get a single character from stdin without waiting for enter"""
        try:
            # Save the current terminal settings
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                # Change terminal settings to read a single character
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                # Restore terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
        except Exception as e:
            print(f"Error reading keyboard input: {e}")
            return None
    
    def keyboard_listener(self):
        """Listens for keyboard input to control the snake"""
        print("Control the snake with WASD or arrow keys. Press Q to quit.")
        try:
            while not self.game_over and not self.quit_game:
                key = self.getch()
                
                if key is None:
                    continue
                    
                if key.lower() == 'q':
                    self.quit_game = True
                    break
                    
                # Check for arrow keys (they produce escape sequences)
                if key == '\x1b':
                    # It's an escape sequence
                    key = sys.stdin.read(2)  # Read 2 more chars
                    if key == '[A':  # Up arrow
                        self.change_direction(UP)
                    elif key == '[B':  # Down arrow
                        self.change_direction(DOWN)
                    elif key == '[C':  # Right arrow
                        self.change_direction(RIGHT)
                    elif key == '[D':  # Left arrow
                        self.change_direction(LEFT)
                else:
                    # WASD controls
                    if key.lower() == 'w':
                        self.change_direction(UP)
                    elif key.lower() == 's':
                        self.change_direction(DOWN)
                    elif key.lower() == 'a':
                        self.change_direction(LEFT)
                    elif key.lower() == 'd':
                        self.change_direction(RIGHT)
        except Exception as e:
            print(f"Keyboard listener error: {e}")
            self.quit_game = True
    
    def change_direction(self, new_direction):
        """Change the snake's direction, preventing 180-degree turns"""
        # Can't go in the opposite direction (180-degree turn)
        if (new_direction[0] + self.direction[0] == 0 and 
            new_direction[1] + self.direction[1] == 0):
            return
            
        self.new_direction = new_direction
    
    def place_food(self):
        """Place food at a random empty location"""
        empty_cells = []
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) not in self.snake:
                    empty_cells.append((x, y))
        
        if empty_cells:
            self.food = random.choice(empty_cells)
        else:
            # No empty cells, you win!
            self.game_over = True
    
    def update_game_state(self):
        """Update the game state for one step"""
        # Get the snake's head position
        head_x, head_y = self.snake[0]
        
        # Apply current direction to move the head
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        new_x, new_y = new_head
        
        # Check for game over conditions
        if (new_x < 0 or new_x >= self.width or  # Hit wall
            new_y < 0 or new_y >= self.height or  # Hit wall
            new_head in self.snake):              # Hit self
            self.game_over = True
            return
        
        # Add new head
        self.snake.insert(0, new_head)
        
        # Check if snake ate food
        if new_head == self.food:
            # Grow snake (don't remove the tail)
            self.score += 1
            self.place_food()
        else:
            # Move snake (remove the tail)
            self.snake.pop()
    
    def render_game(self, canvas):
        """Render the current game state to the canvas"""
        # Clear canvas
        canvas.Clear()
        
        # Create a new PIL image
        image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw snake
        for segment in self.snake:
            x, y = segment
            draw.point((x, y), fill=self.snake_color)
        
        # Draw food
        x, y = self.food
        draw.point((x, y), fill=self.food_color)
        
        # Copy to canvas
        canvas.SetImage(image.resize((self.matrix.width, self.matrix.height)))
    
    def init_game(self):
        """Initialize a new game"""
        # Game world size
        self.width = self.matrix.width
        self.height = self.matrix.height
        
        # Game state
        self.snake = [(self.width // 2, self.height // 2)]  # Start in the middle
        self.direction = RIGHT  # Starting direction
        self.new_direction = RIGHT
        self.food = (0, 0)
        self.place_food()
        self.score = 0
        
        # Game control
        self.game_over = False
        self.quit_game = False
        
        # Parse colors
        try:
            r, g, b = map(int, self.args.snake_color.split(','))
            self.snake_color = (r, g, b)
        except:
            self.snake_color = (0, 255, 0)  # Green
            
        try:
            r, g, b = map(int, self.args.food_color.split(','))
            self.food_color = (r, g, b)
        except:
            self.food_color = (255, 0, 0)  # Red
    
    def run(self):
        """Main game loop"""
        # Initialize game
        self.init_game()
        
        # Start keyboard listener thread
        keyboard_thread = threading.Thread(target=self.keyboard_listener)
        keyboard_thread.daemon = True
        keyboard_thread.start()
        
        # Create canvas
        canvas = self.matrix.CreateFrameCanvas()
        
        try:
            # Game loop
            while not self.game_over and not self.quit_game:
                # Update direction from new direction
                self.direction = self.new_direction
                
                # Update game state
                self.update_game_state()
                
                # Render the game
                self.render_game(canvas)
                
                # Update display
                canvas = self.matrix.SwapOnVSync(canvas)
                
                # Control game speed
                time.sleep(self.args.speed)
            
            # Game over display
            if self.game_over and not self.quit_game:
                print(f"Game Over! Score: {self.score}")
                
                # Flash the snake a few times
                for _ in range(5):
                    # Toggle between showing and hiding the snake
                    canvas.Clear()
                    self.matrix.SwapOnVSync(canvas)
                    time.sleep(0.3)
                    
                    self.render_game(canvas)
                    self.matrix.SwapOnVSync(canvas)
                    time.sleep(0.3)
                
        except KeyboardInterrupt:
            print("Game interrupted")
        finally:
            print(f"Final Score: {self.score}")

# Main function
if __name__ == "__main__":
    snake_game = SnakeGame()
    if not snake_game.process():
        snake_game.print_help()
    else:
        snake_game.run()